from __future__ import annotations

import asyncio
import dataclasses

import pytest

from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationException
from randovania.game_connection.executor.prime3_wii_executor import Prime3WiiExecutor
from randovania.game_connection.executor.prime3_wii_protocol import (
    DEFAULT_RUNTIME_BUILD_ID,
    HELLO_METADATA_VERSION,
    HELLO_RUNTIME_CAPABILITIES,
    INVALID_STATE_MESSAGE,
    NOT_NEGOTIATED_MESSAGE,
    UNSUPPORTED_VERSION_MESSAGE,
    HelloRequestPayload,
    HelloResponsePayload,
    Prime3WiiAvailability,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiErrorCode,
    Prime3WiiErrorResponse,
    Prime3WiiInventoryAvailability,
    Prime3WiiInventoryRecord,
    Prime3WiiRequest,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    decode_response,
    encode_hello_request_payload,
    encode_hello_response_payload,
    encode_response,
)
from test.game_connection.executor.prime3_wii_fake_server import Prime3WiiFakeServer


@pytest.fixture(name="sleep_spy")
def sleep_spy_fixture():
    calls: list[float] = []

    async def _sleep(delay: float) -> None:
        calls.append(delay)

    return calls, _sleep


@pytest.fixture(name="server")
async def fake_server():
    server = Prime3WiiFakeServer(
        max_read_size=32,
        capabilities=(
            Prime3WiiCapability.READ_MEMORY | Prime3WiiCapability.GAME_IDENTITY | Prime3WiiCapability.INVENTORY_STATE
        ),
        identity_availability=(
            Prime3WiiAvailability.EXECUTABLE_RECOGNIZED | Prime3WiiAvailability.GAME_STATE_POINTER_VALID
        ),
        inventory_availability=(
            Prime3WiiInventoryAvailability.EXECUTABLE_RECOGNIZED
            | Prime3WiiInventoryAvailability.GAME_STATE_POINTER_VALID
            | Prime3WiiInventoryAvailability.INVENTORY_ROOT_VALID
            | Prime3WiiInventoryAvailability.RANGE_VALID
            | Prime3WiiInventoryAvailability.CONSISTENCY_CHECK_PASSED
            | Prime3WiiInventoryAvailability.SNAPSHOT_AVAILABLE
        ),
        inventory_records=tuple(Prime3WiiInventoryRecord(i, i + 100) for i in range(59)),
    )
    server.load_bytes(0x80000020, b"ABCD")
    server.load_bytes(0x80000040, b"EFGH")
    server.store_pointer(0x80000080, 0x800000A0)
    server.load_bytes(0x800000A4, b"PTR!")
    await server.start()
    try:
        yield server
    finally:
        await server.close()


@pytest.fixture(name="executor")
def executor_fixture(server: Prime3WiiFakeServer, sleep_spy):
    _, sleep = sleep_spy
    assert server.port is not None
    return Prime3WiiExecutor(
        "127.0.0.1",
        port=server.port,
        timeout=0.05,
        retry_count=1,
        retry_backoff=0.01,
        sleep=sleep,
    )


async def test_connect_hello_success(executor: Prime3WiiExecutor):
    assert await executor.connect() is None
    assert executor.is_connected()
    assert executor.supports_writes is False
    assert executor.accepted_capabilities & Prime3WiiCapability.GAME_IDENTITY


async def test_get_game_identity_returns_typed_availability(executor: Prime3WiiExecutor) -> None:
    assert await executor.connect() is None
    identity = await executor.get_game_identity()
    assert identity.availability_flags & Prime3WiiAvailability.EXECUTABLE_RECOGNIZED
    assert identity.availability_flags & Prime3WiiAvailability.GAME_STATE_POINTER_VALID
    assert not identity.availability_flags & Prime3WiiAvailability.PLAYER_STATE_POINTER_VALID


async def test_get_inventory_returns_typed_snapshot_after_identity(executor: Prime3WiiExecutor) -> None:
    assert await executor.connect() is None
    await executor.get_game_identity()
    snapshot = await executor.get_inventory_snapshot()
    assert snapshot.is_available
    assert snapshot.snapshot_sequence == 0
    assert len(snapshot.records) == 59
    assert snapshot.records[17] == Prime3WiiInventoryRecord(17, 117)


async def test_get_inventory_requires_validated_identity(executor: Prime3WiiExecutor) -> None:
    assert await executor.connect() is None
    with pytest.raises(MemoryOperationException, match="must be validated"):
        await executor.get_inventory_snapshot()


async def test_get_inventory_temporary_unavailable_is_valid(
    executor: Prime3WiiExecutor, server: Prime3WiiFakeServer
) -> None:
    server.inventory_payload = dataclasses.replace(
        server.inventory_payload,
        availability_flags=Prime3WiiInventoryAvailability.TEMPORARILY_UNAVAILABLE,
        records=type(server.inventory_payload)().records,
    )
    assert await executor.connect() is None
    await executor.get_game_identity()
    snapshot = await executor.get_inventory_snapshot()
    assert not snapshot.is_available
    assert snapshot.availability_flags & Prime3WiiInventoryAvailability.TEMPORARILY_UNAVAILABLE


async def test_connect_rejects_omitted_inventory_capabilities(
    server: Prime3WiiFakeServer,
    sleep_spy,
) -> None:
    server.capabilities = Prime3WiiCapability.READ_MEMORY
    _, sleep = sleep_spy
    assert server.port is not None
    executor = Prime3WiiExecutor(
        "127.0.0.1",
        port=server.port,
        timeout=0.05,
        retry_count=0,
        sleep=sleep,
    )
    message = await executor.connect()

    assert message is not None
    assert "missing GAME_IDENTITY, INVENTORY_STATE" in message
    assert not executor.is_connected()


async def test_connect_unsupported_protocol_version(executor: Prime3WiiExecutor, server: Prime3WiiFakeServer):
    server.inject_malformed_next(
        Prime3WiiCommand.HELLO,
        encode_response(
            Prime3WiiResponse(
                Prime3WiiCommand.HELLO,
                1,
                Prime3WiiResponseStatus.OK,
                encode_hello_response_payload(
                    HelloResponsePayload(
                        selected_protocol_version=2,
                        runtime_capabilities=HELLO_RUNTIME_CAPABILITIES | Prime3WiiCapability.READ_MEMORY,
                        accepted_client_capabilities=Prime3WiiCapability.READ_MEMORY,
                        session_id=1,
                        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
                        runtime_mode=19,
                        runtime_metadata_version=HELLO_METADATA_VERSION,
                    )
                ),
            )
        ),
    )

    message = await executor.connect()

    assert message == "Server reported unsupported protocol version 2."
    assert not executor.is_connected()


async def test_connect_missing_required_capability(executor: Prime3WiiExecutor, server: Prime3WiiFakeServer):
    server.capabilities = Prime3WiiCapability(0)

    message = await executor.connect()

    assert message == (
        "The Wii runtime does not support the inventory protocol required by this version of CDV "
        "(missing GAME_IDENTITY, INVENTORY_STATE)."
    )
    assert not executor.is_connected()


async def test_connect_accepts_structured_inventory_without_arbitrary_read_memory(
    server: Prime3WiiFakeServer, sleep_spy
) -> None:
    server.capabilities = Prime3WiiCapability.GAME_IDENTITY | Prime3WiiCapability.INVENTORY_STATE
    _, sleep = sleep_spy
    assert server.port is not None
    executor = Prime3WiiExecutor("127.0.0.1", port=server.port, timeout=0.05, retry_count=0, sleep=sleep)
    assert await executor.connect() is None
    assert not executor.accepted_capabilities & Prime3WiiCapability.READ_MEMORY
    await executor.ensure_game_identity()
    assert (await executor.get_inventory_snapshot()).is_available


async def test_connect_unexpected_accepted_capability_mask(executor: Prime3WiiExecutor, server: Prime3WiiFakeServer):
    inventory_capabilities = (
        HELLO_RUNTIME_CAPABILITIES | Prime3WiiCapability.GAME_IDENTITY | Prime3WiiCapability.INVENTORY_STATE
    )
    server.inject_malformed_next(
        Prime3WiiCommand.HELLO,
        encode_response(
            Prime3WiiResponse(
                Prime3WiiCommand.HELLO,
                1,
                Prime3WiiResponseStatus.OK,
                encode_hello_response_payload(
                    HelloResponsePayload(
                        selected_protocol_version=1,
                        runtime_capabilities=inventory_capabilities,
                        accepted_client_capabilities=inventory_capabilities | Prime3WiiCapability.RECONNECT,
                        session_id=1,
                        runtime_build_id=DEFAULT_RUNTIME_BUILD_ID,
                        runtime_mode=19,
                    )
                ),
            )
        ),
    )

    message = await executor.connect()

    assert message is not None
    assert "unexpected accepted capability mask" in message
    assert not executor.is_connected()


async def test_ping(executor: Prime3WiiExecutor):
    await executor.connect()

    await executor.ping()


@pytest.mark.parametrize(
    "operation",
    [
        MemoryOperation(0x80000020, read_byte_count=4),
        MemoryOperation(0x80000020, write_bytes=b"ABCD"),
    ],
)
async def test_generic_memory_operations_are_unavailable(
    executor: Prime3WiiExecutor, operation: MemoryOperation
) -> None:
    await executor.connect()

    with pytest.raises(MemoryOperationException, match="Arbitrary READ_MEMORY and game-memory writes are unavailable"):
        await executor.perform_single_memory_operation(operation)

    assert executor.is_connected()


async def test_clean_disconnect(executor: Prime3WiiExecutor, server: Prime3WiiFakeServer):
    await executor.connect()

    executor.disconnect()
    await asyncio.wait_for(server.disconnect_event.wait(), timeout=0.1)

    assert not executor.is_connected()
    assert server.disconnect_requests == 1


async def test_reconnect_after_disconnect(executor: Prime3WiiExecutor):
    await executor.connect()
    executor.disconnect()

    assert await executor.connect() is None
    assert executor.is_connected()


def test_fake_server_rejects_ping_before_hello() -> None:
    server = Prime3WiiFakeServer()

    response = decode_response(
        server._build_response(Prime3WiiRequest(Prime3WiiCommand.PING, 1, b"before")),
        expected_request_id=1,
    )

    assert isinstance(response, Prime3WiiErrorResponse)
    assert response.command is Prime3WiiCommand.PING
    assert response.error_code is Prime3WiiErrorCode.NOT_NEGOTIATED
    assert response.message == NOT_NEGOTIATED_MESSAGE
    assert server.negotiated_request is None
    assert server.negotiated_response is None


def test_fake_server_repeats_identical_hello_session() -> None:
    server = Prime3WiiFakeServer()
    hello = HelloRequestPayload(
        min_protocol_version=1,
        max_protocol_version=1,
        capabilities=Prime3WiiCapability.PING | Prime3WiiCapability.READ_MEMORY,
        client_nonce=0x43503357,
        client_name="randovania",
    )
    first = decode_response(
        server._build_response(Prime3WiiRequest(Prime3WiiCommand.HELLO, 1, encode_hello_request_payload(hello))),
        expected_request_id=1,
    )
    second = decode_response(
        server._build_response(Prime3WiiRequest(Prime3WiiCommand.HELLO, 2, encode_hello_request_payload(hello))),
        expected_request_id=2,
    )

    assert isinstance(first, Prime3WiiResponse)
    assert isinstance(second, Prime3WiiResponse)
    assert first.command is Prime3WiiCommand.HELLO
    assert second.command is Prime3WiiCommand.HELLO
    assert first.payload == second.payload


def test_fake_server_rejects_changed_hello_after_negotiation() -> None:
    server = Prime3WiiFakeServer()
    initial = HelloRequestPayload(
        min_protocol_version=1,
        max_protocol_version=1,
        capabilities=Prime3WiiCapability.PING,
        client_nonce=1,
        client_name="randovania",
    )
    changed = HelloRequestPayload(
        min_protocol_version=1,
        max_protocol_version=1,
        capabilities=Prime3WiiCapability.PING,
        client_nonce=2,
        client_name="randovania",
    )

    _ = server._build_response(Prime3WiiRequest(Prime3WiiCommand.HELLO, 1, encode_hello_request_payload(initial)))
    response = decode_response(
        server._build_response(Prime3WiiRequest(Prime3WiiCommand.HELLO, 2, encode_hello_request_payload(changed))),
        expected_request_id=2,
    )

    assert isinstance(response, Prime3WiiErrorResponse)
    assert response.command is Prime3WiiCommand.HELLO
    assert response.error_code is Prime3WiiErrorCode.INVALID_STATE
    assert response.message == INVALID_STATE_MESSAGE


def test_fake_server_rejects_unsupported_hello_version_without_negotiating() -> None:
    server = Prime3WiiFakeServer()
    response = decode_response(
        server._build_response(
            Prime3WiiRequest(
                Prime3WiiCommand.HELLO,
                1,
                encode_hello_request_payload(
                    HelloRequestPayload(
                        min_protocol_version=2,
                        max_protocol_version=3,
                        capabilities=Prime3WiiCapability.PING,
                        client_nonce=1,
                    )
                ),
            )
        ),
        expected_request_id=1,
    )

    assert isinstance(response, Prime3WiiErrorResponse)
    assert response.command is Prime3WiiCommand.HELLO
    assert response.error_code is Prime3WiiErrorCode.UNSUPPORTED_VERSION
    assert response.message == UNSUPPORTED_VERSION_MESSAGE
    assert server.negotiated_request is None
    assert server.negotiated_response is None
