from __future__ import annotations

import asyncio
import contextlib
import dataclasses
from collections import defaultdict

from randovania.game_connection.executor.prime3_wii_protocol import (
    HelloPayload,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    decode_read_memory_payload,
    decode_request,
    encode_error_response,
    encode_hello_payload,
    encode_response,
)


@dataclasses.dataclass(slots=True)
class PendingBehavior:
    drop_count: int = 0
    release_event: asyncio.Event | None = None
    malformed_packet: bytes | None = None
    stale_packet: bytes | None = None


class _Prime3WiiFakeServerProtocol(asyncio.DatagramProtocol):
    def __init__(self, server: Prime3WiiFakeServer):
        self._server = server

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self._server.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, addr) -> None:  # noqa: ANN001
        task = asyncio.create_task(self._server.handle_packet(data, addr))
        self._server._tasks.add(task)
        task.add_done_callback(self._server._tasks.discard)


class Prime3WiiFakeServer:
    def __init__(
        self,
        *,
        max_read_size: int = 32,
        capabilities: Prime3WiiCapability = Prime3WiiCapability.READ_MEMORY,
        valid_ranges: tuple[tuple[int, int], ...] = ((0x80000000, 0x81800000),),
    ):
        self.max_read_size = max_read_size
        self.capabilities = capabilities
        self.valid_ranges = valid_ranges
        self.transport: asyncio.DatagramTransport | None = None
        self.port: int | None = None
        self.requests_seen: dict[Prime3WiiCommand, int] = defaultdict(int)
        self._memory: dict[int, int] = {}
        self._tasks: set[asyncio.Task[None]] = set()
        self._behaviors: dict[Prime3WiiCommand, PendingBehavior] = defaultdict(PendingBehavior)
        self.disconnect_requests = 0
        self.disconnect_event = asyncio.Event()

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _Prime3WiiFakeServerProtocol(self),
            local_addr=("127.0.0.1", 0),
        )
        self.transport = transport  # type: ignore[assignment]
        self.port = transport.get_extra_info("sockname")[1]

    async def close(self) -> None:
        if self.transport is not None:
            self.transport.close()
        for task in tuple(self._tasks):
            task.cancel()
        for task in tuple(self._tasks):
            with contextlib.suppress(asyncio.CancelledError):
                await task

    def load_bytes(self, address: int, data: bytes) -> None:
        for i, value in enumerate(data):
            self._memory[address + i] = value

    def store_pointer(self, address: int, pointer: int) -> None:
        self.load_bytes(address, pointer.to_bytes(4, "big"))

    def drop_next(self, command: Prime3WiiCommand, *, count: int = 1) -> None:
        self._behaviors[command].drop_count += count

    def delay_next(self, command: Prime3WiiCommand) -> asyncio.Event:
        event = asyncio.Event()
        self._behaviors[command].release_event = event
        return event

    def inject_malformed_next(self, command: Prime3WiiCommand, packet: bytes) -> None:
        self._behaviors[command].malformed_packet = packet

    def inject_stale_next(self, command: Prime3WiiCommand, packet: bytes) -> None:
        self._behaviors[command].stale_packet = packet

    def _is_valid_range(self, address: int, size: int) -> bool:
        end = address + size
        return any(address >= start and end <= stop for start, stop in self.valid_ranges)

    async def handle_packet(self, data: bytes, addr) -> None:  # noqa: ANN001
        request = decode_request(data)
        self.requests_seen[request.command] += 1
        behavior = self._behaviors[request.command]

        if behavior.drop_count > 0:
            behavior.drop_count -= 1
            return

        if behavior.release_event is not None:
            release_event = behavior.release_event
            behavior.release_event = None
            await release_event.wait()

        if behavior.stale_packet is not None:
            assert self.transport is not None
            self.transport.sendto(behavior.stale_packet, addr)
            behavior.stale_packet = None

        if behavior.malformed_packet is not None:
            assert self.transport is not None
            self.transport.sendto(behavior.malformed_packet, addr)
            behavior.malformed_packet = None
            return

        response = self._build_response(request)
        assert self.transport is not None
        self.transport.sendto(response, addr)

    def _build_response(self, request: Prime3WiiRequest) -> bytes:
        if request.command is Prime3WiiCommand.HELLO:
            hello = HelloPayload(
                protocol_version=1,
                max_read_size=self.max_read_size,
                capabilities=self.capabilities,
            )
            return encode_response(
                Prime3WiiResponse(
                    command=Prime3WiiCommand.HELLO,
                    request_id=request.request_id,
                    status=Prime3WiiResponseStatus.OK,
                    payload=encode_hello_payload(hello),
                )
            )

        if request.command is Prime3WiiCommand.PING:
            return encode_response(
                Prime3WiiResponse(
                    command=Prime3WiiCommand.PING,
                    request_id=request.request_id,
                    status=Prime3WiiResponseStatus.OK,
                    payload=b"",
                )
            )

        if request.command is Prime3WiiCommand.DISCONNECT:
            self.disconnect_requests += 1
            self.disconnect_event.set()
            return encode_response(
                Prime3WiiResponse(
                    command=Prime3WiiCommand.DISCONNECT,
                    request_id=request.request_id,
                    status=Prime3WiiResponseStatus.OK,
                    payload=b"",
                )
            )

        if request.command is Prime3WiiCommand.READ_MEMORY:
            payload = decode_read_memory_payload(request.payload)
            if payload.size > self.max_read_size:
                return encode_error_response(
                    request.command,
                    request.request_id,
                    Prime3WiiErrorCode.INVALID_PAYLOAD_LENGTH,
                    f"Read size {payload.size} exceeds max {self.max_read_size}",
                )
            if not self._is_valid_range(payload.address, payload.size):
                return encode_error_response(
                    request.command,
                    request.request_id,
                    Prime3WiiErrorCode.INVALID_ADDRESS,
                    f"Invalid address range 0x{payload.address:08x}+{payload.size}",
                )
            try:
                body = bytes(self._memory[payload.address + i] for i in range(payload.size))
            except KeyError:
                return encode_error_response(
                    request.command,
                    request.request_id,
                    Prime3WiiErrorCode.INVALID_ADDRESS,
                    f"Missing memory at 0x{payload.address:08x}",
                )

            return encode_response(
                Prime3WiiResponse(
                    command=Prime3WiiCommand.READ_MEMORY,
                    request_id=request.request_id,
                    status=Prime3WiiResponseStatus.OK,
                    payload=body,
                )
            )

        return encode_error_response(
            request.command,
            request.request_id,
            Prime3WiiErrorCode.UNKNOWN_COMMAND,
            f"Command {request.command.name} is unsupported",
        )
