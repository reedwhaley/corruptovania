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
    DEFAULT_RUNTIME_BUILD_ID,
    GAME_IDENTITY_SCHEMA_VERSION,
    INVENTORY_SCHEMA_VERSION,
    PRIME3_NTSC_RETAIL_PROFILE_FINGERPRINT,
    PRIME3_NTSC_RETAIL_PROFILE_ID,
    GameIdentityPayload,
    HelloRequestPayload,
    MismatchedRequestIdError,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiGameId,
    Prime3WiiInventorySnapshot,
    Prime3WiiPlatformId,
    Prime3WiiProtocolError,
    Prime3WiiRegionId,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    Prime3WiiRevisionId,
    ReadMemoryPayload,
    ServerSideProtocolError,
    compute_accepted_capabilities,
    decode_game_identity_payload,
    decode_hello_response_payload,
    decode_inventory_payload,
    decode_response,
    encode_hello_request_payload,
    encode_read_memory_payload,
    encode_request,
)

DEFAULT_PRIME3_WII_PORT = 43674
DEFAULT_TIMEOUT_SECONDS = 1.0
DEFAULT_RETRY_COUNT = 2
DEFAULT_RETRY_BACKOFF_SECONDS = 0.25
MEMORY_START = 0x80000000
MEMORY_END = 0x81800000
CLIENT_CAPABILITIES = (
    Prime3WiiCapability.HELLO_NEGOTIATION
    | Prime3WiiCapability.PING
    | Prime3WiiCapability.STRUCTURED_ERRORS
    | Prime3WiiCapability.DETERMINISTIC_SESSION_ID
    | Prime3WiiCapability.READ_MEMORY
    | Prime3WiiCapability.GAME_IDENTITY
    | Prime3WiiCapability.INVENTORY_STATE
)
CLIENT_NONCE = 0x43503357
CLIENT_NAME = "randovania"


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
        self._accepted_capabilities = Prime3WiiCapability(0)
        self._runtime_build_id: int | None = None
        self._runtime_mode: int | None = None
        self._identity_validated = False
        self._game_identity: GameIdentityPayload | None = None

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
        self._connected = False

        try:
            hello_request_payload = encode_hello_request_payload(
                HelloRequestPayload(
                    min_protocol_version=1,
                    max_protocol_version=1,
                    capabilities=CLIENT_CAPABILITIES,
                    client_nonce=CLIENT_NONCE,
                    client_name=CLIENT_NAME,
                )
            )
            hello_response = await self._request(
                Prime3WiiCommand.HELLO,
                hello_request_payload,
                expected_command=Prime3WiiCommand.HELLO,
                disconnect_on_error=False,
            )
            hello = decode_hello_response_payload(hello_response.payload)
            self.logger.debug(
                "HELLO negotiation succeeded: protocol=%d accepted=0x%x runtime=0x%x session=0x%08x build=0x%08x",
                hello.selected_protocol_version,
                int(hello.accepted_client_capabilities),
                int(hello.runtime_capabilities),
                hello.session_id,
                hello.runtime_build_id,
            )

            if hello.selected_protocol_version != 1:
                raise MemoryOperationException(
                    f"Server reported unsupported protocol version {hello.selected_protocol_version}."
                )
            if hello.runtime_build_id == 0:
                raise MemoryOperationException("Server reported an invalid runtime build ID of zero.")
            if not hello.accepted_client_capabilities & (
                Prime3WiiCapability.READ_MEMORY | Prime3WiiCapability.INVENTORY_STATE
            ):
                raise MemoryOperationException("Server does not advertise read-memory support.")
            expected_accept = compute_accepted_capabilities(CLIENT_CAPABILITIES, hello.runtime_capabilities)
            if hello.accepted_client_capabilities != expected_accept:
                raise MemoryOperationException(
                    "Server returned an unexpected accepted capability mask "
                    f"0x{int(hello.accepted_client_capabilities):x}; expected 0x{int(expected_accept):x}."
                )
            if hello.runtime_build_id == DEFAULT_RUNTIME_BUILD_ID and hello.session_id == 0:
                raise MemoryOperationException("Server reported an uninitialized session identifier.")

            self._connected = True
            self._accepted_capabilities = hello.accepted_client_capabilities
            self._runtime_build_id = hello.runtime_build_id
            self._runtime_mode = hello.runtime_mode
            self._identity_validated = False
            self._game_identity = None
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
            self._accepted_capabilities = Prime3WiiCapability(0)
            self._runtime_build_id = None
            self._runtime_mode = None
            self._identity_validated = False
            self._game_identity = None
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
        await self._request(Prime3WiiCommand.PING, b"", expected_command=Prime3WiiCommand.PING)

    @property
    def accepted_capabilities(self) -> Prime3WiiCapability:
        return self._accepted_capabilities

    @property
    def identity_validated(self) -> bool:
        return self._identity_validated

    async def get_game_identity(self) -> GameIdentityPayload:
        if not self.is_connected():
            raise MemoryOperationException("Not connected")
        if not self._accepted_capabilities & Prime3WiiCapability.GAME_IDENTITY:
            raise MemoryOperationException("Server did not negotiate GAME_IDENTITY capability.")
        response = await self._request(
            Prime3WiiCommand.GET_GAME_IDENTITY,
            b"",
            expected_command=Prime3WiiCommand.GET_GAME_IDENTITY,
        )
        try:
            identity = decode_game_identity_payload(response.payload)
        except Prime3WiiProtocolError as exc:
            raise MemoryOperationException(f"Malformed GET_GAME_IDENTITY response: {exc}") from exc
        expected = {
            "schema_version": (identity.schema_version, GAME_IDENTITY_SCHEMA_VERSION),
            "game_id": (identity.game_id, Prime3WiiGameId.METROID_PRIME_3_CORRUPTION),
            "platform_id": (identity.platform_id, Prime3WiiPlatformId.WII),
            "region_id": (identity.region_id, Prime3WiiRegionId.NTSC_U),
            "revision_id": (identity.revision_id, Prime3WiiRevisionId.WII_NTSC_3_436),
            "profile_id": (identity.profile_id, PRIME3_NTSC_RETAIL_PROFILE_ID),
            "profile_fingerprint": (
                identity.profile_fingerprint,
                PRIME3_NTSC_RETAIL_PROFILE_FINGERPRINT,
            ),
            "runtime_build_id": (identity.runtime_build_id, self._runtime_build_id),
            "runtime_mode": (identity.runtime_mode, self._runtime_mode),
        }
        for field_name, (actual, wanted) in expected.items():
            if actual != wanted:
                raise MemoryOperationException(
                    f"GET_GAME_IDENTITY {field_name} mismatch: received {actual!r}, expected {wanted!r}."
                )
        self._identity_validated = True
        self._game_identity = identity
        return identity

    async def ensure_game_identity(self) -> GameIdentityPayload:
        if self._game_identity is None:
            return await self.get_game_identity()
        return self._game_identity

    async def get_inventory_snapshot(self) -> Prime3WiiInventorySnapshot:
        if not self.is_connected():
            raise MemoryOperationException("Not connected")
        if not self._accepted_capabilities & Prime3WiiCapability.INVENTORY_STATE:
            raise MemoryOperationException("Server did not negotiate INVENTORY_STATE capability.")
        if not self._identity_validated:
            raise MemoryOperationException("GET_GAME_IDENTITY must be validated before GET_INVENTORY.")
        response = await self._request(
            Prime3WiiCommand.GET_INVENTORY,
            b"",
            expected_command=Prime3WiiCommand.GET_INVENTORY,
        )
        try:
            snapshot = decode_inventory_payload(response.payload)
        except Prime3WiiProtocolError as exc:
            raise MemoryOperationException(f"Malformed GET_INVENTORY response: {exc}") from exc
        if snapshot.schema_version != INVENTORY_SCHEMA_VERSION:
            raise MemoryOperationException(
                "GET_INVENTORY schema mismatch: "
                f"received {snapshot.schema_version}, expected {INVENTORY_SCHEMA_VERSION}."
            )
        return snapshot

    async def _read_memory_raw(self, address: int, size: int) -> bytes:
        _validate_read(address, size)
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
