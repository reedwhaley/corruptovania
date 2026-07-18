from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions

from randovania.game_connection.connector.corruption_remote_connector import CorruptionRemoteConnector
from randovania.game_connection.executor.memory_operation import MemoryOperation
from randovania.game_connection.executor.prime3_wii_executor import Prime3WiiExecutor
from randovania.game_connection.executor.prime3_wii_protocol import (
    Prime3WiiCapability,
    Prime3WiiInventoryAvailability,
    Prime3WiiInventoryRecord,
    Prime3WiiInventorySnapshot,
)
from randovania.game_description.resources.inventory import InventoryItem


@pytest.fixture(name="connector")
def corruption_remote_connector():
    connector = CorruptionRemoteConnector(dol_versions.ALL_VERSIONS[0], AsyncMock())
    return connector


def test_multiworld_magic_item_is_unavailable_for_read_only_corruption(connector: CorruptionRemoteConnector):
    assert connector.multiworld_magic_item is None


@pytest.mark.parametrize("correct_vtable", [False, True])
@pytest.mark.parametrize("has_cplayer", [False, True])
@pytest.mark.parametrize("has_pending_op", [False, True])
@pytest.mark.parametrize("has_world", [False, True])
async def test_fetch_game_status(
    connector: CorruptionRemoteConnector, has_world, has_pending_op, has_cplayer, correct_vtable
):
    # Setup
    assert isinstance(connector.executor, AsyncMock)

    expected_world = connector.game.region_list.regions[1]

    cplayer_address = 0x8099FFAA

    connector.executor.perform_memory_operations.side_effect = lambda ops: {
        ops[0]: expected_world.extra["asset_id"].to_bytes(8, "big") if has_world else b"DEADBEEF",
        ops[1]: b"\x01" if has_pending_op else b"\x00",
        ops[2]: cplayer_address.to_bytes(4, "big") if has_cplayer else None,
    }

    if correct_vtable:
        vtable_memory_return = connector.version.cplayer_vtable.to_bytes(4, "big")
    else:
        vtable_memory_return = b"CAFE"
    connector.executor.perform_single_memory_operation.return_value = vtable_memory_return

    # Run
    actual_has_op, actual_world = await connector.current_game_status()

    # Assert
    if has_world and has_cplayer and correct_vtable:
        assert actual_world is expected_world
    else:
        assert actual_world is None
    assert actual_has_op == has_pending_op
    if has_cplayer:
        connector.executor.perform_single_memory_operation.assert_awaited_once_with(
            MemoryOperation(
                cplayer_address,
                read_byte_count=4,
            )
        )
    else:
        connector.executor.perform_single_memory_operation.assert_not_awaited()


async def test_cp3w_inventory_uses_shared_semantics_and_preserves_suit_transform() -> None:
    executor = Prime3WiiExecutor("127.0.0.1")
    executor._accepted_capabilities = Prime3WiiCapability.INVENTORY_STATE
    executor._identity_validated = True
    records = list(Prime3WiiInventorySnapshot().records)
    records[4] = Prime3WiiInventoryRecord(10, 255)
    records[17] = Prime3WiiInventoryRecord(5, 5)
    executor.get_inventory_snapshot = AsyncMock(
        return_value=Prime3WiiInventorySnapshot(
            availability_flags=(
                Prime3WiiInventoryAvailability.EXECUTABLE_RECOGNIZED
                | Prime3WiiInventoryAvailability.GAME_STATE_POINTER_VALID
                | Prime3WiiInventoryAvailability.INVENTORY_ROOT_VALID
                | Prime3WiiInventoryAvailability.RANGE_VALID
                | Prime3WiiInventoryAvailability.CONSISTENCY_CHECK_PASSED
                | Prime3WiiInventoryAvailability.SNAPSHOT_AVAILABLE
            ),
            records=tuple(records),
        )
    )
    connector = CorruptionRemoteConnector(dol_versions.ALL_VERSIONS[0], executor)

    inventory = await connector.get_inventory()

    assert inventory[connector.game.resource_database.get_item("Missile")] == InventoryItem(10, 255)
    assert inventory[connector.game.resource_database.get_item("SuitType")] == InventoryItem(True, True)
    assert all(item.extra["item_id"] < 1000 for item in inventory.raw)
