from __future__ import annotations

import importlib
import socket
import struct
import sys
import threading
from pathlib import Path

from randovania.game_connection.builder.connector_builder_option import ConnectorBuilderOption
from randovania.game_connection.builder.prime3_tcp_tracker_connector_builder import (
    Prime3TcpTrackerConnectionManager,
    Prime3TcpTrackerConnectorBuilder,
)
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.prime3_tcp_tracker import (
    CLIENT_HELLO,
    CP3W_SERVER_PORT,
    TRACKER_ACK,
    TRACKER_SNAPSHOT,
    Prime3TrackerFrame,
)


def _frame(message_type: int, sequence: int, words: list[int]) -> Prime3TrackerFrame:
    payload = struct.pack(f">{len(words)}I", *words)
    return Prime3TrackerFrame(message_type, sequence, 0, len(payload), 0, payload)


def test_legacy_wii_udp_configuration_migrates_to_inbound_tracker() -> None:
    option = ConnectorBuilderOption(
        ConnectorBuilderChoice.PRIME3_WII,
        {"ip": "192.168.50.19", "port": 43674},
    )

    restored = option.create_builder()

    assert isinstance(restored, Prime3TcpTrackerConnectorBuilder)
    assert restored.configuration_params() == {
        "name": "Prime 3 Wii",
        "client_nonce": None,
        "seed_id": None,
        "enabled": True,
    }


def test_default_listener_uses_the_fixed_tcp_tracker_port() -> None:
    manager = Prime3TcpTrackerConnectionManager()

    assert manager.service._configuration["bind_port"] == CP3W_SERVER_PORT
    assert manager.service._configuration["bind_host"] == "0.0.0.0"


def test_game_connection_modules_do_not_reference_removed_udp_connector_stack() -> None:
    game_connection_root = Path(__file__).resolve().parents[3].joinpath("randovania", "game_connection")
    source = "\n".join(path.read_text(encoding="utf-8") for path in game_connection_root.rglob("*.py"))

    for removed_reference in (
        "Prime3WiiConnectorBuilder",
        "Prime3WiiExecutor",
        "Opening CP3W UDP connection",
        "CP3W UDP port",
        "HELLO negotiation failed",
        "Connecting to Wii",
    ):
        assert removed_reference not in source


def test_desktop_prime3_connection_imports_without_the_server_package(monkeypatch) -> None:
    builder_module = "randovania.game_connection.builder.prime3_tcp_tracker_connector_builder"
    option_module = "randovania.game_connection.builder.connector_builder_option"
    monkeypatch.delitem(sys.modules, builder_module, raising=False)
    monkeypatch.delitem(sys.modules, option_module, raising=False)
    monkeypatch.setitem(sys.modules, "randovania.server", None)

    importlib.import_module(option_module)
    importlib.import_module(builder_module)


async def test_inbound_hello_binds_single_configured_connection_and_snapshot_updates_status():
    manager = Prime3TcpTrackerConnectionManager(
        {"enabled": True, "bind_host": "127.0.0.1", "bind_port": 0, "idle_timeout_seconds": 1}
    )
    builder = Prime3TcpTrackerConnectorBuilder(manager=manager)
    server_socket, wii_socket = socket.socketpair()
    thread = threading.Thread(target=manager.service.handle_socket, args=(server_socket, ("192.168.50.19", 43674)))
    try:
        assert await builder.build_connector() is None
        assert builder.get_status_message() == "Waiting for Wii connection"
        thread.start()

        wii_socket.sendall(_frame(CLIENT_HELLO, 1, [0x524D3345, 0x1234, 0xF, 0x43503357, 0, 0, 4, 4, 0]).encode())
        assert Prime3TrackerFrame.decode(wii_socket.recv(64)).message_type == 0x02
        assert builder.get_status_message() == "Connected to Prime 3 Wii"

        wii_socket.sendall(_frame(TRACKER_SNAPSHOT, 2, [7, 0, 1, 99, 1, 8, 10, 20]).encode())
        assert Prime3TrackerFrame.decode(wii_socket.recv(64)).message_type == TRACKER_ACK
        assert builder.tracker_status["state"] == "snapshot_received"
        assert builder.tracker_status["last_snapshot_id"] == 7
    finally:
        wii_socket.close()
        thread.join(timeout=1)
        server_socket.close()
        builder.close()
    assert manager.service.status()["listening"] is False


async def test_ambiguous_inbound_hello_is_rejected_without_constructing_a_wii_udp_executor():
    manager = Prime3TcpTrackerConnectionManager(
        {"enabled": True, "bind_host": "127.0.0.1", "bind_port": 0, "idle_timeout_seconds": 1}
    )
    first = Prime3TcpTrackerConnectorBuilder(manager=manager)
    second = Prime3TcpTrackerConnectorBuilder(manager=manager)
    server_socket, wii_socket = socket.socketpair()
    thread = threading.Thread(target=manager.service.handle_socket, args=(server_socket, ("192.168.50.19", 43674)))
    try:
        await first.build_connector()
        await second.build_connector()
        thread.start()
        wii_socket.sendall(_frame(CLIENT_HELLO, 1, [0x524D3345, 0x1234, 0xF, 0x43503357, 0, 0, 4, 4, 0]).encode())
        thread.join(timeout=1)
        assert not thread.is_alive()
        assert first.tracker_status["state"] == "error"
        assert second.tracker_status["state"] == "error"
    finally:
        wii_socket.close()
        thread.join(timeout=1)
        server_socket.close()
        first.close()
        second.close()


async def test_shared_listener_is_reused_and_released_by_the_final_connection():
    manager = Prime3TcpTrackerConnectionManager(
        {"enabled": True, "bind_host": "127.0.0.1", "bind_port": 0, "idle_timeout_seconds": 1}
    )
    first = Prime3TcpTrackerConnectorBuilder(manager=manager)
    second = Prime3TcpTrackerConnectorBuilder(manager=manager)

    assert await first.build_connector() is None
    first_service = manager.service
    assert first_service.status()["listening"] is True

    assert await second.build_connector() is None
    assert manager.service is first_service
    assert manager.service.status()["listening"] is True

    first.close()
    assert manager.service.status()["listening"] is True

    second.close()
    assert manager.service.status()["listening"] is False
