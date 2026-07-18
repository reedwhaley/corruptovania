from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions

from randovania.game_connection.builder.prime3_wii_connector_builder import Prime3WiiConnectorBuilder
from randovania.game_connection.connector.corruption_remote_connector import CorruptionRemoteConnector
from randovania.game_connection.executor.prime3_wii_protocol import (
    INVENTORY_ITEM_IDS,
    Prime3WiiAvailability,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiInventoryAvailability,
    Prime3WiiInventoryRecord,
    Prime3WiiInventorySnapshot,
)
from randovania.game_connection.game_connection import ConnectedGameState, GameConnection
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.network_common.game_connection_status import GameConnectionStatus
from test.game_connection.executor.prime3_wii_fake_corruption_memory import Prime3WiiFakeCorruptionMemory
from test.game_connection.executor.prime3_wii_fake_server import Prime3WiiFakeServer

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import PlayerLocationEvent


@pytest.fixture(name="server")
async def fake_server():
    server = Prime3WiiFakeServer(
        capabilities=Prime3WiiCapability.GAME_IDENTITY | Prime3WiiCapability.INVENTORY_STATE,
        identity_availability=(
            Prime3WiiAvailability.EXECUTABLE_RECOGNIZED
            | Prime3WiiAvailability.GAME_STATE_POINTER_VALID
            | Prime3WiiAvailability.INVENTORY_ROOT_AVAILABLE
        ),
        inventory_availability=(
            Prime3WiiInventoryAvailability.EXECUTABLE_RECOGNIZED
            | Prime3WiiInventoryAvailability.GAME_STATE_POINTER_VALID
            | Prime3WiiInventoryAvailability.INVENTORY_ROOT_VALID
            | Prime3WiiInventoryAvailability.RANGE_VALID
            | Prime3WiiInventoryAvailability.CONSISTENCY_CHECK_PASSED
            | Prime3WiiInventoryAvailability.SNAPSHOT_AVAILABLE
        ),
    )
    await server.start()
    try:
        yield server
    finally:
        await server.close()


@pytest.fixture(name="memory")
def fake_memory():
    return Prime3WiiFakeCorruptionMemory.create(
        corruption_dol_versions.ALL_VERSIONS[0],
        uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
    )


def _load_inventory(server: Prime3WiiFakeServer, memory: Prime3WiiFakeCorruptionMemory) -> None:
    resources_by_id = {
        item.extra["item_id"]: item
        for item in memory.connector.game.resource_database.item
        if item.extra["item_id"] < 1000
    }
    records = tuple(
        Prime3WiiInventoryRecord(
            memory.item_states[resources_by_id[item_id].short_name].amount,
            memory.item_states[resources_by_id[item_id].short_name].capacity,
        )
        for item_id in INVENTORY_ITEM_IDS
    )
    server.inventory_payload = Prime3WiiInventorySnapshot(
        availability_flags=server.inventory_payload.availability_flags,
        snapshot_sequence=server.inventory_payload.snapshot_sequence + 1,
        records=records,
    )


async def _build_connector(server: Prime3WiiFakeServer, memory: Prime3WiiFakeCorruptionMemory):
    assert server.port is not None
    builder = Prime3WiiConnectorBuilder("127.0.0.1", port=server.port, allow_loopback=True)
    _load_inventory(server, memory)
    with patch("randovania.game_connection.connector.prime_remote_connector.PrimeRemoteConnector.start_updates"):
        connector = await builder.build_connector()
    assert isinstance(connector, CorruptionRemoteConnector)
    connector._timer = MagicMock()
    return builder, connector


async def test_read_only_update_flow(server: Prime3WiiFakeServer, memory):
    _, connector = await _build_connector(server, memory)
    locations: list[PlayerLocationEvent] = []
    inventories: list[Inventory] = []
    connector.PlayerLocationChanged.connect(locations.append)
    connector.InventoryUpdated.connect(inventories.append)
    connector.known_collected_locations = AsyncMock()
    connector.receive_remote_pickups = AsyncMock()

    await connector.update()
    await connector.update()
    memory.set_item("Missile", 30, 30)
    _load_inventory(server, memory)
    await connector.update()

    missile = connector.game.resource_database.get_item("Missile")
    suit_type = connector.game.resource_database.get_item("SuitType")
    assert locations == []
    assert len(inventories) == 2
    assert inventories[0][missile] == InventoryItem(25, 25)
    assert inventories[1][missile] == InventoryItem(30, 30)
    assert inventories[0][suit_type] == InventoryItem(True, True)
    connector.known_collected_locations.assert_not_awaited()
    connector.receive_remote_pickups.assert_not_awaited()
    assert connector.supports_writes is False
    assert server.requests_seen[Prime3WiiCommand.RESERVED_MAILBOX] == 0


async def test_read_only_message_actions_fail(server: Prime3WiiFakeServer, memory):
    _, connector = await _build_connector(server, memory)

    with pytest.raises(RuntimeError, match="read-only executor"):
        await connector.display_arbitrary_message("Hello")


async def test_connection_loss_disconnects_cleanly(server: Prime3WiiFakeServer, memory):
    _, connector = await _build_connector(server, memory)
    server.drop_next(Prime3WiiCommand.GET_INVENTORY, count=6)

    await connector.update()
    await connector.update()
    await connector.update()

    assert connector.is_disconnected()
    connector._timer.stop.assert_called_once_with()


async def test_game_connection_inventory_path(server: Prime3WiiFakeServer, memory, skip_qtbot):
    options = MagicMock()
    options.__enter__ = MagicMock(return_value=options)
    options.connector_builders = []
    connection = GameConnection(options, MagicMock())
    assert server.port is not None
    builder = Prime3WiiConnectorBuilder("127.0.0.1", port=server.port, allow_loopback=True)
    _load_inventory(server, memory)
    with patch("randovania.game_connection.connector.prime_remote_connector.PrimeRemoteConnector.start_updates"):
        connection.add_connection_builder(builder)
        await connection._auto_update()
    connector = connection.get_connector_for_builder(builder)
    assert isinstance(connector, CorruptionRemoteConnector)
    connector._timer = MagicMock()

    states: list[ConnectedGameState] = []
    connection.GameStateUpdated.connect(states.append)
    await connector.update()

    state = connection.connected_states[connector]
    missile = connector.game.resource_database.get_item("Missile")
    assert state.status == GameConnectionStatus.TitleScreen
    assert state.current_inventory[missile] == InventoryItem(25, 25)
    assert any(emitted.current_inventory[missile] == InventoryItem(25, 25) for emitted in states)
