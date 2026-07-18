from __future__ import annotations

import asyncio
import dataclasses
import datetime
import enum
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
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiGameId,
    Prime3WiiInventoryAvailability,
    Prime3WiiInventorySnapshot,
    Prime3WiiPlatformId,
    Prime3WiiProtocolError,
    Prime3WiiRegionId,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    Prime3WiiRevisionId,
    ServerSideProtocolError,
    compute_accepted_capabilities,
    decode_game_identity_payload,
    decode_hello_response_payload,
    decode_inventory_payload,
    decode_response,
    encode_hello_request_payload,
    encode_request,
)

DEFAULT_PRIME3_WII_PORT = 43674
DEFAULT_TIMEOUT_SECONDS = 1.0
DEFAULT_RETRY_COUNT = 1
DEFAULT_RETRY_BACKOFF_SECONDS = 0.25
INVENTORY_TIMEOUTS_BEFORE_RECONNECT = 3
CLIENT_CAPABILITIES = (
    Prime3WiiCapability.HELLO_NEGOTIATION
    | Prime3WiiCapability.PING
    | Prime3WiiCapability.STRUCTURED_ERRORS
    | Prime3WiiCapability.DETERMINISTIC_SESSION_ID
    | Prime3WiiCapability.GAME_IDENTITY
    | Prime3WiiCapability.INVENTORY_STATE
)
CLIENT_NONCE = 0x43503357
CLIENT_NAME = "randovania"


class _RequestTimeoutError(MemoryOperationException):
    pass


class Prime3WiiTransientError(MemoryOperationException):
    """A recoverable request failure that does not invalidate the negotiated session."""


class Prime3WiiRuntimeRestartError(MemoryOperationException):
    """The runtime lost its negotiated session and must be reconnected."""


class Prime3WiiConnectionState(enum.Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    NEGOTIATING = "negotiating"
    VALIDATING_IDENTITY = "validating_identity"
    CONNECTED = "connected"
    TEMPORARILY_UNAVAILABLE = "temporarily_unavailable"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    DISCONNECTING = "disconnecting"

    @property
    def pretty_text(self) -> str:
        return {
            Prime3WiiConnectionState.DISCONNECTED: "Disconnected",
            Prime3WiiConnectionState.CONNECTING: "Connecting to Wii",
            Prime3WiiConnectionState.NEGOTIATING: "Negotiating CP3W",
            Prime3WiiConnectionState.VALIDATING_IDENTITY: "Validating Prime 3",
            Prime3WiiConnectionState.CONNECTED: "Connected",
            Prime3WiiConnectionState.TEMPORARILY_UNAVAILABLE: "Game state temporarily unavailable",
            Prime3WiiConnectionState.RECONNECTING: "Reconnecting",
            Prime3WiiConnectionState.ERROR: "Connection error",
            Prime3WiiConnectionState.DISCONNECTING: "Disconnecting",
        }[self]


@dataclasses.dataclass(frozen=True, slots=True)
class Prime3WiiConnectionDiagnostics:
    configured_ip: str
    remote_port: int
    local_endpoint: tuple[str, int] | None
    connection_state: Prime3WiiConnectionState
    negotiated_capabilities: Prime3WiiCapability
    identity: GameIdentityPayload | None
    runtime_build_id: int | None
    runtime_mode: int | None
    session_id: int | None
    last_inventory_sequence: int | None
    last_availability_flags: Prime3WiiInventoryAvailability
    last_rtt_ms: float | None
    timeout_count: int
    consecutive_inventory_timeouts: int
    duplicate_count: int
    sequence_gap_count: int
    sequence_reset_count: int
    sequence_wrap_count: int
    malformed_response_count: int
    unexpected_response_count: int
    dropped_response_count: int
    last_successful_update: datetime.datetime | None
    last_error: str | None


@dataclasses.dataclass(slots=True)
class _ProtocolState:
    queue: asyncio.Queue[bytes]
    expected_endpoint: tuple[str, int]
    diagnostics: Prime3WiiExecutor
    error: Exception | None = None
    closed: bool = False


class _Prime3WiiDatagramProtocol(asyncio.DatagramProtocol):
    def __init__(self, state: _ProtocolState):
        self._state = state

    def datagram_received(self, data: bytes, addr: tuple[str, int]) -> None:
        if addr != self._state.expected_endpoint:
            self._state.diagnostics._unexpected_response_count += 1
            return
        try:
            self._state.queue.put_nowait(data)
        except asyncio.QueueFull:
            self._state.diagnostics._dropped_response_count += 1

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
        self._session_id: int | None = None
        self._local_endpoint: tuple[str, int] | None = None
        self._identity_validated = False
        self._game_identity: GameIdentityPayload | None = None
        self._connection_state = Prime3WiiConnectionState.DISCONNECTED
        self._last_inventory_sequence: int | None = None
        self._last_availability_flags = Prime3WiiInventoryAvailability(0)
        self._last_rtt_ms: float | None = None
        self._timeout_count = 0
        self._consecutive_inventory_timeouts = 0
        self._duplicate_count = 0
        self._sequence_gap_count = 0
        self._sequence_reset_count = 0
        self._sequence_wrap_count = 0
        self._malformed_response_count = 0
        self._unexpected_response_count = 0
        self._dropped_response_count = 0
        self._last_successful_update: datetime.datetime | None = None
        self._last_error: str | None = None
        self._last_completed_request_id: int | None = None

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def port(self) -> int:
        return self._port

    @property
    def connection_state(self) -> Prime3WiiConnectionState:
        return self._connection_state

    @property
    def diagnostics(self) -> Prime3WiiConnectionDiagnostics:
        return Prime3WiiConnectionDiagnostics(
            configured_ip=self._ip,
            remote_port=self._port,
            local_endpoint=self._local_endpoint,
            connection_state=self._connection_state,
            negotiated_capabilities=self._accepted_capabilities,
            identity=self._game_identity,
            runtime_build_id=self._runtime_build_id,
            runtime_mode=self._runtime_mode,
            session_id=self._session_id,
            last_inventory_sequence=self._last_inventory_sequence,
            last_availability_flags=self._last_availability_flags,
            last_rtt_ms=self._last_rtt_ms,
            timeout_count=self._timeout_count,
            consecutive_inventory_timeouts=self._consecutive_inventory_timeouts,
            duplicate_count=self._duplicate_count,
            sequence_gap_count=self._sequence_gap_count,
            sequence_reset_count=self._sequence_reset_count,
            sequence_wrap_count=self._sequence_wrap_count,
            malformed_response_count=self._malformed_response_count,
            unexpected_response_count=self._unexpected_response_count,
            dropped_response_count=self._dropped_response_count,
            last_successful_update=self._last_successful_update,
            last_error=self._last_error,
        )

    def _is_transport_connected(self) -> bool:
        return self._transport is not None and self._protocol_state is not None and not self._protocol_state.closed

    async def connect(self) -> str | None:
        if self.is_connected():
            return None

        self._connection_state = Prime3WiiConnectionState.CONNECTING
        self._last_error = None
        self.logger.info("Opening CP3W UDP connection to %s:%d", self._ip, self._port)

        loop = asyncio.get_running_loop()
        state = _ProtocolState(
            queue=asyncio.Queue(maxsize=32),
            expected_endpoint=(self._ip, self._port),
            diagnostics=self,
        )
        try:
            transport, _ = await loop.create_datagram_endpoint(
                lambda: _Prime3WiiDatagramProtocol(state),
                local_addr=("0.0.0.0", 0),
                remote_addr=(self._ip, self._port),
            )
        except (OSError, ValueError) as e:
            self._connection_state = Prime3WiiConnectionState.ERROR
            self._last_error = f"Unable to open UDP socket: ({type(e).__name__}) {e}"
            return self._last_error

        self._transport = transport
        self._protocol_state = state
        sockname = transport.get_extra_info("sockname")
        if isinstance(sockname, tuple) and len(sockname) >= 2:
            self._local_endpoint = (str(sockname[0]), int(sockname[1]))
        self._connected = False
        self._connection_state = Prime3WiiConnectionState.NEGOTIATING

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
            required_capabilities = Prime3WiiCapability.GAME_IDENTITY | Prime3WiiCapability.INVENTORY_STATE
            if hello.accepted_client_capabilities & required_capabilities != required_capabilities:
                missing = required_capabilities & ~hello.accepted_client_capabilities
                names = ", ".join(
                    capability.name or f"0x{int(capability):X}"
                    for capability in Prime3WiiCapability
                    if capability & missing
                )
                raise MemoryOperationException(
                    "The Wii runtime does not support the inventory protocol required by this version of CDV "
                    f"(missing {names})."
                )
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
            self._session_id = hello.session_id
            self._identity_validated = False
            self._game_identity = None
            self._last_inventory_sequence = None
            self._last_availability_flags = Prime3WiiInventoryAvailability(0)
            self._consecutive_inventory_timeouts = 0
            self._connection_state = Prime3WiiConnectionState.VALIDATING_IDENTITY
            self._last_successful_update = datetime.datetime.now(datetime.UTC)
            self.logger.info(
                "CP3W HELLO succeeded: local=%s capabilities=0x%x session=0x%08x build=0x%08x",
                self._local_endpoint,
                int(self._accepted_capabilities),
                self._session_id,
                self._runtime_build_id,
            )
            return None
        except MemoryOperationException as e:
            self.logger.warning("CP3W HELLO negotiation failed: %s", e)
            self._last_error = str(e)
            self._connection_state = Prime3WiiConnectionState.ERROR
            self._close_transport(Prime3WiiConnectionState.ERROR, send_disconnect=False)
            return str(e)

    def disconnect(self) -> None:
        self._connection_state = Prime3WiiConnectionState.DISCONNECTING
        self._close_transport(Prime3WiiConnectionState.DISCONNECTED, send_disconnect=True)
        self.logger.info("CP3W disconnect complete for %s:%d", self._ip, self._port)

    def _close_transport(
        self,
        final_state: Prime3WiiConnectionState,
        *,
        send_disconnect: bool,
    ) -> None:
        transport = self._transport
        if transport is None:
            self._connected = False
            self._connection_state = final_state
            return

        try:
            if send_disconnect:
                request_id = self._next_request_id()
                transport.sendto(encode_request(Prime3WiiRequest(Prime3WiiCommand.DISCONNECT, request_id)))
        except Exception as e:  # pragma: no cover - best effort before close
            self.logger.debug("Ignoring disconnect packet failure: %s", e)
        finally:
            self._connected = False
            self._accepted_capabilities = Prime3WiiCapability(0)
            self._runtime_build_id = None
            self._runtime_mode = None
            self._session_id = None
            self._identity_validated = False
            self._game_identity = None
            self._local_endpoint = None
            self._transport = None
            self._protocol_state = None
            self._connection_state = final_state
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
                decoded = decode_response(packet)
            except Prime3WiiProtocolError as e:
                self._malformed_response_count += 1
                self.logger.warning("Malformed response for request %d: %s", request_id, e)
                raise MemoryOperationException(f"Malformed response for request {request_id}: {e}") from e

            if decoded.request_id != request_id:
                if decoded.request_id == self._last_completed_request_id:
                    self._duplicate_count += 1
                    self.logger.warning("Ignoring duplicate CP3W response for request %d", decoded.request_id)
                else:
                    self._unexpected_response_count += 1
                    self.logger.warning(
                        "Ignoring unexpected CP3W response %d while waiting for request %d",
                        decoded.request_id,
                        request_id,
                    )
                continue

            if isinstance(decoded, Prime3WiiResponse):
                self._last_completed_request_id = request_id
                return decoded

            error = ServerSideProtocolError(decoded.error_code, decoded.message, decoded.command)
            if decoded.error_code is Prime3WiiErrorCode.NOT_NEGOTIATED:
                self._sequence_reset_count += 1
                raise Prime3WiiRuntimeRestartError(str(error))
            raise MemoryOperationException(str(error))

    async def _request(
        self,
        command: Prime3WiiCommand,
        payload: bytes,
        *,
        expected_command: Prime3WiiCommand,
        disconnect_on_error: bool = True,
        retry_count: int | None = None,
    ) -> Prime3WiiResponse:
        if not self._is_transport_connected():
            raise MemoryOperationException("Not connected")
        assert self._transport is not None
        assert self._protocol_state is not None

        async with self._request_lock:
            request_retry_count = self._retry_count if retry_count is None else retry_count
            for attempt in range(request_retry_count + 1):
                request_id = self._next_request_id()
                request = Prime3WiiRequest(command=command, request_id=request_id, payload=payload)
                self.logger.debug("Sending %s request %d (attempt %d)", command.name, request_id, attempt + 1)
                started = time.monotonic()
                try:
                    self._transport.sendto(encode_request(request))
                    response = await self._read_response_for_request(request_id)
                    self._last_rtt_ms = (time.monotonic() - started) * 1000.0
                    self._last_successful_update = datetime.datetime.now(datetime.UTC)
                    if response.command is not expected_command:
                        self._unexpected_response_count += 1
                        raise MemoryOperationException(
                            f"Expected {expected_command.name} response, received {response.command.name}."
                        )
                    if response.status is not Prime3WiiResponseStatus.OK:
                        raise MemoryOperationException(f"Unexpected response status {response.status.name}.")
                    return response
                except _RequestTimeoutError as e:
                    self._timeout_count += 1
                    if attempt >= request_retry_count:
                        if disconnect_on_error:
                            self._last_error = str(e)
                            self._close_transport(Prime3WiiConnectionState.ERROR, send_disconnect=False)
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
                        self._close_transport(Prime3WiiConnectionState.ERROR, send_disconnect=False)
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
        self._connection_state = Prime3WiiConnectionState.VALIDATING_IDENTITY
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
        self._connection_state = Prime3WiiConnectionState.CONNECTED
        self._last_error = None
        self.logger.info(
            "Prime 3 identity accepted: region=%s revision=%s profile=0x%08x fingerprint=0x%08x",
            identity.region_id.name,
            identity.revision_id.name,
            identity.profile_id,
            identity.profile_fingerprint,
        )
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
        try:
            response = await self._request(
                Prime3WiiCommand.GET_INVENTORY,
                b"",
                expected_command=Prime3WiiCommand.GET_INVENTORY,
                disconnect_on_error=False,
                retry_count=0,
            )
        except _RequestTimeoutError as exc:
            self._consecutive_inventory_timeouts += 1
            self._last_error = str(exc)
            if self._consecutive_inventory_timeouts >= INVENTORY_TIMEOUTS_BEFORE_RECONNECT:
                self.logger.warning(
                    "CP3W inventory timed out %d consecutive times; reconnecting",
                    self._consecutive_inventory_timeouts,
                )
                self._close_transport(Prime3WiiConnectionState.RECONNECTING, send_disconnect=False)
                raise MemoryOperationException(str(exc)) from exc
            self.logger.warning(
                "CP3W inventory timeout %d/%d",
                self._consecutive_inventory_timeouts,
                INVENTORY_TIMEOUTS_BEFORE_RECONNECT,
            )
            raise Prime3WiiTransientError(str(exc)) from exc
        except Prime3WiiRuntimeRestartError:
            self._last_error = "The Wii runtime restarted; renegotiating CP3W."
            self._close_transport(Prime3WiiConnectionState.RECONNECTING, send_disconnect=False)
            raise
        except MemoryOperationException:
            self._close_transport(Prime3WiiConnectionState.ERROR, send_disconnect=False)
            raise
        try:
            snapshot = decode_inventory_payload(response.payload)
        except Prime3WiiProtocolError as exc:
            raise MemoryOperationException(f"Malformed GET_INVENTORY response: {exc}") from exc
        if snapshot.schema_version != INVENTORY_SCHEMA_VERSION:
            raise MemoryOperationException(
                "GET_INVENTORY schema mismatch: "
                f"received {snapshot.schema_version}, expected {INVENTORY_SCHEMA_VERSION}."
            )
        self._consecutive_inventory_timeouts = 0
        previous_sequence = self._last_inventory_sequence
        sequence = snapshot.snapshot_sequence
        if previous_sequence is not None:
            expected_sequence = (previous_sequence + 1) & 0xFFFFFFFF
            if sequence == previous_sequence:
                self._duplicate_count += 1
                self.logger.warning("Duplicate CP3W inventory sequence %d", sequence)
            elif sequence == expected_sequence:
                if previous_sequence == 0xFFFFFFFF:
                    self._sequence_wrap_count += 1
            elif sequence > previous_sequence:
                self._sequence_gap_count += 1
                self.logger.warning("CP3W inventory sequence gap: previous=%d current=%d", previous_sequence, sequence)
            else:
                self._sequence_reset_count += 1
                self._last_error = (
                    f"CP3W inventory sequence moved backward from {previous_sequence} to {sequence}; "
                    "runtime restart suspected."
                )
                self.logger.warning(self._last_error)
                self._close_transport(Prime3WiiConnectionState.RECONNECTING, send_disconnect=False)
                raise Prime3WiiRuntimeRestartError(self._last_error)

        self._last_inventory_sequence = sequence
        self._last_availability_flags = snapshot.availability_flags
        self._last_error = None
        if snapshot.is_available:
            if self._connection_state is Prime3WiiConnectionState.TEMPORARILY_UNAVAILABLE:
                self.logger.info("Prime 3 inventory became available again")
            self._connection_state = Prime3WiiConnectionState.CONNECTED
        else:
            if self._connection_state is not Prime3WiiConnectionState.TEMPORARILY_UNAVAILABLE:
                self.logger.warning("Prime 3 game state is temporarily unavailable")
            self._connection_state = Prime3WiiConnectionState.TEMPORARILY_UNAVAILABLE
        return snapshot

    async def perform_memory_operations(self, ops: list[MemoryOperation]) -> dict[MemoryOperation, bytes]:
        raise MemoryOperationException(
            "Arbitrary READ_MEMORY and game-memory writes are unavailable for the Wii / Wii U CP3W connection."
        )
