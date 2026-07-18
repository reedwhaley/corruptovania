from __future__ import annotations

import asyncio
import dataclasses

import pytest

from randovania.game_connection.builder.prime3_wii_connector_builder import validate_wii_ip_address
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationException
from randovania.game_connection.executor.prime3_wii_executor import (
    DEFAULT_PRIME3_WII_PORT,
    Prime3WiiConnectionState,
    Prime3WiiExecutor,
    Prime3WiiRuntimeRestartError,
    Prime3WiiTransientError,
)
from randovania.game_connection.executor.prime3_wii_protocol import (
    INVENTORY_FRAME_SIZE,
    INVENTORY_ITEM_IDS,
    INVENTORY_PAYLOAD_SIZE,
    INVENTORY_RECORD_COUNT,
    INVENTORY_RECORD_SIZE,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiInventoryAvailability,
    Prime3WiiInventoryRecord,
)
from test.game_connection.executor.prime3_wii_fake_runtime import FakePrime3WiiRuntime


async def _connected(runtime: FakePrime3WiiRuntime, *, timeout: float = 0.05) -> Prime3WiiExecutor:
    executor = Prime3WiiExecutor("127.0.0.1", runtime.port, timeout=timeout, retry_backoff=0)
    assert await executor.connect() is None
    await executor.get_game_identity()
    return executor


async def test_loopback_session_inventory_unavailable_and_recovery() -> None:
    runtime = FakePrime3WiiRuntime()
    await runtime.start()
    executor = await _connected(runtime)
    try:
        assert executor.diagnostics.remote_port == runtime.port
        assert executor.diagnostics.local_endpoint is not None
        assert executor.diagnostics.local_endpoint[1] != runtime.port
        assert executor.accepted_capabilities & Prime3WiiCapability.GAME_IDENTITY
        assert executor.accepted_capabilities & Prime3WiiCapability.INVENTORY_STATE

        first = await executor.get_inventory_snapshot()
        assert first.is_available
        runtime.inventory = dataclasses.replace(
            runtime.inventory,
            availability_flags=Prime3WiiInventoryAvailability.TEMPORARILY_UNAVAILABLE,
        )
        unavailable = await executor.get_inventory_snapshot()
        assert not unavailable.is_available
        assert executor.connection_state is Prime3WiiConnectionState.TEMPORARILY_UNAVAILABLE

        runtime.inventory = dataclasses.replace(
            runtime.inventory,
            availability_flags=first.availability_flags,
        )
        recovered = await executor.get_inventory_snapshot()
        assert recovered.is_available
        assert executor.connection_state is Prime3WiiConnectionState.CONNECTED
        assert runtime.requests[Prime3WiiCommand.GET_INVENTORY] == 3
    finally:
        executor.disconnect()
        await runtime.close()


async def test_inventory_timeout_escalates_to_reconnect() -> None:
    runtime = FakePrime3WiiRuntime()
    await runtime.start()
    executor = await _connected(runtime)
    executor._timeout = 0.01
    runtime.drop_inventory = 3
    try:
        with pytest.raises(Prime3WiiTransientError):
            await executor.get_inventory_snapshot()
        with pytest.raises(Prime3WiiTransientError):
            await executor.get_inventory_snapshot()
        with pytest.raises(MemoryOperationException):
            await executor.get_inventory_snapshot()
        assert executor.connection_state is Prime3WiiConnectionState.RECONNECTING
        assert executor.diagnostics.timeout_count == 3
        assert not executor.is_connected()
    finally:
        executor.disconnect()
        await runtime.close()


async def test_runtime_restart_requires_new_session() -> None:
    runtime = FakePrime3WiiRuntime()
    await runtime.start()
    executor = await _connected(runtime)
    try:
        await executor.get_inventory_snapshot()
        runtime.restart()
        with pytest.raises(Prime3WiiRuntimeRestartError):
            await executor.get_inventory_snapshot()
        assert executor.connection_state is Prime3WiiConnectionState.RECONNECTING

        replacement = await _connected(runtime)
        try:
            assert (await replacement.get_inventory_snapshot()).snapshot_sequence == 0
        finally:
            replacement.disconnect()
    finally:
        executor.disconnect()
        await runtime.close()


async def test_missing_inventory_capability_is_rejected() -> None:
    runtime = FakePrime3WiiRuntime(Prime3WiiCapability.GAME_IDENTITY)
    await runtime.start()
    executor = Prime3WiiExecutor("127.0.0.1", runtime.port, timeout=0.05, retry_backoff=0)
    try:
        error = await executor.connect()
        assert error is not None
        assert "does not support the inventory protocol" in error
        assert "INVENTORY_STATE" in error
        assert not executor.is_connected()
    finally:
        executor.disconnect()
        await runtime.close()


async def test_backward_sequence_detects_restart() -> None:
    runtime = FakePrime3WiiRuntime()
    runtime.inventory = dataclasses.replace(runtime.inventory, snapshot_sequence=20)
    await runtime.start()
    executor = await _connected(runtime)
    try:
        await executor.get_inventory_snapshot()
        runtime.inventory = dataclasses.replace(runtime.inventory, snapshot_sequence=3)
        with pytest.raises(Prime3WiiRuntimeRestartError):
            await executor.get_inventory_snapshot()
        assert executor.diagnostics.sequence_reset_count == 1
    finally:
        executor.disconnect()
        await runtime.close()


async def test_sequence_wrap_and_duplicate_response() -> None:
    runtime = FakePrime3WiiRuntime()
    runtime.inventory = dataclasses.replace(runtime.inventory, snapshot_sequence=0xFFFFFFFF)
    await runtime.start()
    executor = await _connected(runtime)
    try:
        runtime.duplicate_inventory = True
        assert (await executor.get_inventory_snapshot()).snapshot_sequence == 0xFFFFFFFF
        assert (await executor.get_inventory_snapshot()).snapshot_sequence == 0
        assert executor.diagnostics.sequence_wrap_count == 1
        assert executor.diagnostics.duplicate_count == 1
    finally:
        executor.disconnect()
        await runtime.close()


async def test_malformed_and_delayed_response_fail_safely() -> None:
    runtime = FakePrime3WiiRuntime()
    await runtime.start()
    executor = await _connected(runtime)
    try:
        runtime.malformed_inventory = True
        with pytest.raises(MemoryOperationException, match="Malformed response"):
            await executor.get_inventory_snapshot()
        assert executor.diagnostics.malformed_response_count == 1
        assert not executor.is_connected()

        executor = await _connected(runtime)
        gate = runtime.inventory_gate = asyncio.Event()
        executor._timeout = 0.01
        with pytest.raises(Prime3WiiTransientError):
            await executor.get_inventory_snapshot()
        gate.set()
    finally:
        executor.disconnect()
        await runtime.close()


def test_fixed_port_and_address_validation() -> None:
    assert DEFAULT_PRIME3_WII_PORT == 43674
    assert validate_wii_ip_address(" 192.168.1.42 ") == "192.168.1.42"
    for invalid in ("", "http://192.168.1.2", "192.168.1.2:43674", "0.0.0.0", "224.0.0.1", "127.0.0.1"):
        with pytest.raises(ValueError, match="address|IPv4|Loopback"):
            validate_wii_ip_address(invalid)


def test_canonical_inventory_artifact_shape() -> None:
    assert INVENTORY_RECORD_COUNT == len(INVENTORY_ITEM_IDS) == 59
    assert INVENTORY_RECORD_SIZE == 8
    assert INVENTORY_PAYLOAD_SIZE == 484
    assert INVENTORY_FRAME_SIZE == 504
    assert INVENTORY_ITEM_IDS == tuple(range(43)) + (44, 45, 46) + tuple(range(48, 53)) + tuple(range(62, 70))


async def test_inventory_shape_and_arbitrary_memory_are_read_only() -> None:
    runtime = FakePrime3WiiRuntime()
    records = tuple(Prime3WiiInventoryRecord(index, index + 5) for index in range(len(INVENTORY_ITEM_IDS)))
    runtime.inventory = dataclasses.replace(runtime.inventory, records=records)
    await runtime.start()
    executor = await _connected(runtime)
    try:
        snapshot = await executor.get_inventory_snapshot()
        assert len(snapshot.records) == 59
        assert snapshot.record_for_item_id(INVENTORY_ITEM_IDS[10]) == records[10]
        with pytest.raises(MemoryOperationException, match="Arbitrary READ_MEMORY"):
            await executor.perform_memory_operations([MemoryOperation(0x80000000, read_byte_count=4)])
    finally:
        executor.disconnect()
        await runtime.close()
