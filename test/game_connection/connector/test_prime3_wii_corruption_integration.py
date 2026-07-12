from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions

from randovania.game_connection.builder.prime3_wii_connector_builder import Prime3WiiConnectorBuilder
from randovania.game_connection.connector.corruption_remote_connector import CorruptionRemoteConnector
from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_connection.executor.prime3_wii_protocol import Prime3WiiCommand
from randovania.game_connection.game_connection import GameConnection
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.network_common.game_connection_status import GameConnectionStatus
from test.game_connection.executor.prime3_wii_fake_corruption_memory import Prime3WiiFakeCorruptionMemory
from test.game_connection.executor.prime3_wii_fake_server import Prime3WiiFakeServer


@pytest.fixture(name="server")
async def fake_server():
    server = Prime3WiiFakeServer(max_read_size=64)
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


async def _build_connector(server: Prime3WiiFakeServer, memory: Prime3WiiFakeCorruptionMemory):
    builder = Prime3WiiConnectorBuilder("127.0.0.1", port=server.port)
    memory.load_into(server)
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
    memory.load_into(server)
    await connector.update()

    missile = connector.game.resource_database.get_item("Missile")
    suit_type = connector.game.resource_database.get_item("SuitType")
    assert locations == [PlayerLocationEvent(memory.region, None)]
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
    server.drop_next(Prime3WiiCommand.READ_MEMORY, count=3)

    await connector.update()

    assert connector.is_disconnected()
    connector._timer.stop.assert_called_once_with()


async def test_game_connection_inventory_path(server: Prime3WiiFakeServer, memory, skip_qtbot):
    options = MagicMock()
    options.__enter__ = MagicMock(return_value=options)
    options.connector_builders = []
    connection = GameConnection(options, MagicMock())
    builder = Prime3WiiConnectorBuilder("127.0.0.1", port=server.port)
    memory.load_into(server)
    with patch("randovania.game_connection.connector.prime_remote_connector.PrimeRemoteConnector.start_updates"):
        connection.add_connection_builder(builder)
        await connection._auto_update()
    connector = connection.get_connector_for_builder(builder)
    assert isinstance(connector, CorruptionRemoteConnector)
    connector._timer = MagicMock()

    states = []
    connection.GameStateUpdated.connect(states.append)
    await connector.update()

    state = connection.connected_states[connector]
    missile = connector.game.resource_database.get_item("Missile")
    assert state.status == GameConnectionStatus.InGame
    assert state.current_inventory[missile] == InventoryItem(25, 25)
    assert any(emitted.current_inventory[missile] == InventoryItem(25, 25) for emitted in states)
