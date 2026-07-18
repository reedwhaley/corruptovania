from __future__ import annotations

import asyncio
import contextlib
import dataclasses
from collections import Counter

from randovania.game_connection.executor.prime3_wii_protocol import (
    DEFAULT_RUNTIME_BUILD_ID,
    DEFAULT_RUNTIME_NAME,
    HELLO_METADATA_VERSION,
    HELLO_RUNTIME_CAPABILITIES,
    GameIdentityPayload,
    HelloResponsePayload,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiInventoryAvailability,
    Prime3WiiInventorySnapshot,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    compute_accepted_capabilities,
    decode_hello_request_payload,
    decode_request,
    derive_session_id,
    encode_error_response,
    encode_game_identity_payload,
    encode_hello_response_payload,
    encode_inventory_payload,
    encode_response,
)


class _Protocol(asyncio.DatagramProtocol):
    def __init__(self, runtime: FakePrime3WiiRuntime):
        self.runtime = runtime

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        self.runtime.transport = transport  # type: ignore[assignment]

    def datagram_received(self, data: bytes, address: tuple[str, int]) -> None:
        task = asyncio.create_task(self.runtime.handle(data, address))
        self.runtime.tasks.add(task)
        task.add_done_callback(self.runtime.tasks.discard)


class FakePrime3WiiRuntime:
    def __init__(self, capabilities: Prime3WiiCapability | None = None):
        self.capabilities = (
            Prime3WiiCapability.GAME_IDENTITY | Prime3WiiCapability.INVENTORY_STATE
            if capabilities is None
            else capabilities
        )
        self.transport: asyncio.DatagramTransport | None = None
        self.port = 0
        self.tasks: set[asyncio.Task[None]] = set()
        self.requests: Counter[Prime3WiiCommand] = Counter()
        self.drop_inventory = 0
        self.duplicate_inventory = False
        self.malformed_inventory = False
        self.inventory_gate: asyncio.Event | None = None
        self.negotiated = False
        self.identity = GameIdentityPayload(runtime_mode=21)
        self.inventory = Prime3WiiInventorySnapshot(
            availability_flags=(
                Prime3WiiInventoryAvailability.EXECUTABLE_RECOGNIZED
                | Prime3WiiInventoryAvailability.GAME_STATE_POINTER_VALID
                | Prime3WiiInventoryAvailability.INVENTORY_ROOT_VALID
                | Prime3WiiInventoryAvailability.SNAPSHOT_AVAILABLE
                | Prime3WiiInventoryAvailability.CONSISTENCY_CHECK_PASSED
                | Prime3WiiInventoryAvailability.RANGE_VALID
            )
        )

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _Protocol(self),
            local_addr=("127.0.0.1", 0),
        )
        self.transport = transport
        self.port = int(transport.get_extra_info("sockname")[1])

    async def close(self) -> None:
        if self.transport is not None:
            self.transport.close()
        for task in tuple(self.tasks):
            task.cancel()
        for task in tuple(self.tasks):
            with contextlib.suppress(asyncio.CancelledError):
                await task

    def restart(self, sequence: int = 0) -> None:
        self.negotiated = False
        self.inventory = dataclasses.replace(self.inventory, snapshot_sequence=sequence)

    async def handle(self, data: bytes, address: tuple[str, int]) -> None:
        request = decode_request(data)
        self.requests[request.command] += 1
        if request.command is Prime3WiiCommand.GET_INVENTORY and self.drop_inventory:
            self.drop_inventory -= 1
            return
        if request.command is Prime3WiiCommand.GET_INVENTORY and self.inventory_gate is not None:
            gate = self.inventory_gate
            self.inventory_gate = None
            await gate.wait()
        if request.command is Prime3WiiCommand.GET_INVENTORY and self.malformed_inventory:
            self.malformed_inventory = False
            assert self.transport is not None
            self.transport.sendto(b"malformed", address)
            return
        response = self._response(request)
        assert self.transport is not None
        self.transport.sendto(response, address)
        if request.command is Prime3WiiCommand.GET_INVENTORY and self.duplicate_inventory:
            self.duplicate_inventory = False
            self.transport.sendto(response, address)

    def _response(self, request: Prime3WiiRequest) -> bytes:
        if request.command is Prime3WiiCommand.HELLO:
            hello = decode_hello_request_payload(request.payload)
            runtime_capabilities = HELLO_RUNTIME_CAPABILITIES | self.capabilities
            accepted = compute_accepted_capabilities(hello.capabilities, runtime_capabilities)
            payload = HelloResponsePayload(
                selected_protocol_version=1,
                runtime_capabilities=runtime_capabilities,
                accepted_client_capabilities=accepted,
                session_id=derive_session_id(
                    selected_protocol_version=1,
                    client_nonce=hello.client_nonce,
                    runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
                    runtime_capabilities=runtime_capabilities,
                    accepted_client_capabilities=accepted,
                ),
                runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
                runtime_mode=21,
                runtime_metadata_version=HELLO_METADATA_VERSION,
                runtime_name=DEFAULT_RUNTIME_NAME,
            )
            self.negotiated = True
            return self._ok(request, encode_hello_response_payload(payload))

        if not self.negotiated:
            return encode_error_response(
                request.command,
                request.request_id,
                Prime3WiiErrorCode.NOT_NEGOTIATED,
                "HELLO negotiation is required",
            )
        if request.command is Prime3WiiCommand.GET_GAME_IDENTITY:
            return self._ok(request, encode_game_identity_payload(self.identity))
        if request.command is Prime3WiiCommand.GET_INVENTORY:
            snapshot = self.inventory
            self.inventory = dataclasses.replace(
                snapshot,
                snapshot_sequence=(snapshot.snapshot_sequence + 1) & 0xFFFFFFFF,
            )
            return self._ok(request, encode_inventory_payload(snapshot))
        if request.command is Prime3WiiCommand.PING:
            return self._ok(request, request.payload)
        if request.command is Prime3WiiCommand.DISCONNECT:
            return self._ok(request, b"")
        return encode_error_response(
            request.command,
            request.request_id,
            Prime3WiiErrorCode.UNKNOWN_COMMAND,
            "unsupported test command",
        )

    @staticmethod
    def _ok(request: Prime3WiiRequest, payload: bytes) -> bytes:
        return encode_response(
            Prime3WiiResponse(
                command=request.command,
                request_id=request.request_id,
                status=Prime3WiiResponseStatus.OK,
                payload=payload,
            )
        )
