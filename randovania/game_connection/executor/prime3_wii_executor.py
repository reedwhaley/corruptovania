from __future__ import annotations

import asyncio
import dataclasses
import math
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from randovania.game_connection.executor.memory_operation import (
    MemoryOperation,
    MemoryOperationException,
    MemoryOperationExecutor,
)
from randovania.game_connection.executor.prime3_wii_protocol import (
    MismatchedRequestIdError,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiProtocolError,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    ReadMemoryPayload,
    ServerSideProtocolError,
    decode_hello_payload,
    decode_response,
    encode_read_memory_payload,
    encode_request,
)

DEFAULT_PRIME3_WII_PORT = 43674
DEFAULT_TIMEOUT_SECONDS = 1.0
DEFAULT_RETRY_COUNT = 2
DEFAULT_RETRY_BACKOFF_SECONDS = 0.25
MEMORY_START = 0x80000000
MEMORY_END = 0x81800000


class _RequestTimeoutError(MemoryOperationException):
    pass


def _is_valid_memory_range(address: int, size: int) -> bool:
    if address < MEMORY_START or size < 0:
        return False
    end_address = address + size
    return end_address <= MEMORY_END and end_address >= address


def _validate_uint32(value: int, label: str) -> None:
    if value < 0 or value > 0xFFFFFFFF:
        raise MemoryOperationException(f"{label} 0x{value:x} is outside the 32-bit address space.")


def _validate_read(address: int, size: int) -> None:
    _validate_uint32(address, "Address")
    if size <= 0:
        raise MemoryOperationException("Read size must be greater than zero.")
    if not _is_valid_memory_range(address, size):
        raise MemoryOperationException(
            f"Range 0x{address:08x} -> 0x{address + size:08x} is outside the supported Wii memory range."
        )


@dataclasses.dataclass(slots=True)
class _ProtocolState:
    queue: asyncio.Queue[bytes]
    error: Exception | None = None
    closed: bool = False


class _Prime3WiiDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, state: _ProtocolState):
        self._state = state

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        self._state.queue.put_nowait(data)

    def error_received(self, exc: Exception) -> None:
        self._state.error = exc

    def connection_lost(self, exc: Exception | None) -> None:
        self._state.closed = True
        if exc is not None:
            self._state.error = exc


class Prime3WiiExecutor(MemoryOperationExecutor):
    supports_writes = False
    _transport: asyncio.DatagramTransport | None = None
    _protocol_state: _ProtocolState | None = None
    _max_read_size: int | None = None
    _request_id: int = 0
    _connected: bool = False

    def __init__(
        self,
        ip: str,
        port: int = DEFAULT_PRIME3_WII_PORT,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        retry_count: int = DEFAULT_RETRY_COUNT,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF_SECONDS,
        sleep: Callable[[float], Awaitable[None]] | None = None,
    ):
        super().__init__()
        self._ip = ip
        self._port = port
        self._timeout = timeout
        self._retry_count = retry_count
        self._retry_backoff = retry_backoff
        self._sleep = sleep or asyncio.sleep
        self._request_lock = asyncio.Lock()

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port

    def _is_transport_connected(self) -> bool:
        return self._transport is not None and self._protocol_state is not None and not self._protocol_state.closed

    async def connect(self) -> str | None:
        if self.is_connected():
            return None

        self.logger.debug("Connecting to Prime 3 Wii endpoint %s:%d", self._ip, self._port)

        loop = asyncio.get_running_loop()
        state = _ProtocolState(queue=asyncio.Queue())
        try:
            transport, _ = await loop.create_datagram_endpoint(
                lambda: _Prime3WiiDatagramProtocol(state),
                remote_addr=(self._ip, self._port),
            )
        except (OSError, ValueError) as e:
            return f"Unable to connect to {self._ip}:{self._port} - ({type(e).__name__}) {e}"

        self._transport = transport
        self._protocol_state = state
        self._max_read_size = None
        self._connected = False

        try:
            hello_response = await self._request(
                Prime3WiiCommand.HELLO,
                b"",
                expected_command=Prime3WiiCommand.HELLO,
                disconnect_on_error=False,
            )
            hello = decode_hello_payload(hello_response.payload)
            self.logger.debug(
                "HELLO negotiation succeeded: protocol=%d max_read_size=%d capabilities=0x%x",
                hello.protocol_version,
                hello.max_read_size,
                int(hello.capabilities),
            )

            if hello.protocol_version != 1:
                raise MemoryOperationException(
                    f"Server reported unsupported protocol version {hello.protocol_version}."
                )
            if not hello.capabilities & Prime3WiiCapability.READ_MEMORY:
                raise MemoryOperationException("Server does not advertise read-memory support.")
            if hello.max_read_size <= 0:
                raise MemoryOperationException("Server reported an invalid maximum read size.")

            self._max_read_size = hello.max_read_size
            self._connected = True
            return None
        except MemoryOperationException as e:
            self.logger.debug("HELLO negotiation failed: %s", e)
            self.disconnect()
            return str(e)

    def disconnect(self) -> None:
        transport = self._transport
        if transport is None:
            return

        self.logger.debug("Disconnecting Prime 3 Wii endpoint %s:%d", self._ip, self._port)
        try:
            request_id = self._next_request_id()
            transport.sendto(encode_request(Prime3WiiRequest(Prime3WiiCommand.DISCONNECT, request_id)))
        except Exception as e:  # pragma: no cover - best effort before close
            self.logger.debug("Ignoring disconnect packet failure: %s", e)
        finally:
            self._connected = False
            self._max_read_size = None
            self._transport = None
            self._protocol_state = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                transport.close()
            else:
                loop.call_later(0.01, transport.close)

    def is_connected(self) -> bool:
        return self._connected and self._is_transport_connected()

    def _next_request_id(self) -> int:
        self._request_id = (self._request_id % 0xFFFFFFFF) + 1
        return self._request_id

    async def _read_response_for_request(self, request_id: int) -> Prime3WiiResponse:
        if not self.is_connected() and self._protocol_state is None:
            raise MemoryOperationException("Not connected")
        assert self._protocol_state is not None

        deadline = time.monotonic() + self._timeout
        while True:
            if self._protocol_state.error is not None:
                raise MemoryOperationException(f"UDP transport error: {self._protocol_state.error}")

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise _RequestTimeoutError(f"Timed out waiting for request {request_id}.")

            try:
                packet = await asyncio.wait_for(self._protocol_state.queue.get(), timeout=remaining)
            except TimeoutError as e:
                raise _RequestTimeoutError(f"Timed out waiting for request {request_id}.") from e

            try:
                decoded = decode_response(packet, expected_request_id=request_id)
            except MismatchedRequestIdError:
                self.logger.debug("Ignoring stale response while waiting for request %d", request_id)
                continue
            except Prime3WiiProtocolError as e:
                self.logger.warning("Malformed response for request %d: %s", request_id, e)
                raise MemoryOperationException(f"Malformed response for request {request_id}: {e}") from e

            if isinstance(decoded, Prime3WiiResponse):
                return decoded

            error = ServerSideProtocolError(decoded.error_code, decoded.message, decoded.command)
            raise MemoryOperationException(str(error))

    async def _request(
        self,
        command: Prime3WiiCommand,
        payload: bytes,
        *,
        expected_command: Prime3WiiCommand,
        disconnect_on_error: bool = True,
    ) -> Prime3WiiResponse:
        if not self._is_transport_connected():
            raise MemoryOperationException("Not connected")
        assert self._transport is not None
        assert self._protocol_state is not None

        async with self._request_lock:
            for attempt in range(self._retry_count + 1):
                request_id = self._next_request_id()
                request = Prime3WiiRequest(command=command, request_id=request_id, payload=payload)
                self.logger.debug("Sending %s request %d (attempt %d)", command.name, request_id, attempt + 1)
                try:
                    self._transport.sendto(encode_request(request))
                    response = await self._read_response_for_request(request_id)
                    if response.command is not expected_command:
                        raise MemoryOperationException(
                            f"Expected {expected_command.name} response, received {response.command.name}."
                        )
                    if response.status is not Prime3WiiResponseStatus.OK:
                        raise MemoryOperationException(f"Unexpected response status {response.status.name}.")
                    return response
                except _RequestTimeoutError as e:
                    if attempt >= self._retry_count:
                        if disconnect_on_error:
                            self.disconnect()
                        raise e
                    delay = self._retry_backoff * math.pow(2.0, attempt)
                    self.logger.debug(
                        "Retrying %s request after timeout on attempt %d; sleeping %.3f seconds",
                        command.name,
                        attempt + 1,
                        delay,
                    )
                    await self._sleep(delay)
                except MemoryOperationException:
                    if disconnect_on_error:
                        self.disconnect()
                    raise

            raise AssertionError("Retry loop exited unexpectedly")

    async def ping(self) -> None:
        response = await self._request(Prime3WiiCommand.PING, b"", expected_command=Prime3WiiCommand.PING)
        if response.payload:
            raise MemoryOperationException("PING response must not include a payload.")

    async def _read_memory_raw(self, address: int, size: int) -> bytes:
        _validate_read(address, size)
        if self._max_read_size is None:
            raise MemoryOperationException("Server capabilities are unknown; connect() must complete first.")
        if size > self._max_read_size:
            raise MemoryOperationException(
                f"Requested read of {size} bytes exceeds the server maximum of {self._max_read_size}."
            )

        response = await self._request(
            Prime3WiiCommand.READ_MEMORY,
            encode_read_memory_payload(ReadMemoryPayload(address=address, size=size)),
            expected_command=Prime3WiiCommand.READ_MEMORY,
        )
        if len(response.payload) != size:
            raise MemoryOperationException(f"Received {len(response.payload)} bytes, expected {size}.")
        return response.payload

    async def perform_memory_operations(self, ops: list[MemoryOperation]) -> dict[MemoryOperation, bytes]:
        if not self.is_connected():
            raise MemoryOperationException("Not connected")

        results: dict[MemoryOperation, bytes] = {}
        for op in ops:
            op.validate_byte_sizes()
            if op.write_bytes is not None and op.read_byte_count is not None:
                raise MemoryOperationException(f"Combined read/write operations are unsupported: {op}")
            if op.write_bytes is not None:
                raise MemoryOperationException(f"Write operations are unsupported: {op}")
            if op.read_byte_count is None:
                raise MemoryOperationException(f"Operation must specify a read size: {op}")

            _validate_uint32(op.address, "Address")
            if op.offset is None:
                results[op] = await self._read_memory_raw(op.address, op.read_byte_count)
                continue

            pointer_bytes = await self._read_memory_raw(op.address, 4)
            pointer_value = int.from_bytes(pointer_bytes, "big")
            if pointer_value == 0:
                raise MemoryOperationException(f"Pointer at 0x{op.address:08x} was null.")

            resolved_address = pointer_value + op.offset
            if resolved_address < 0 or resolved_address > 0xFFFFFFFF:
                raise MemoryOperationException(
                    f"Pointer resolution overflowed: 0x{pointer_value:08x} + {op.offset} = {resolved_address}."
                )

            results[op] = await self._read_memory_raw(resolved_address, op.read_byte_count)

        return results
