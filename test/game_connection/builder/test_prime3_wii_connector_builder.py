from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from randovania.game_connection.builder.connector_builder_option import ConnectorBuilderOption
from randovania.game_connection.builder.prime3_wii_connector_builder import Prime3WiiConnectorBuilder
from randovania.game_connection.connector.corruption_remote_connector import CorruptionRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.prime3_wii_executor import Prime3WiiExecutor


def test_configuration_persists_only_ip() -> None:
    builder = Prime3WiiConnectorBuilder("192.168.1.42", port=12345)
    assert builder.configuration_params() == {"ip": "192.168.1.42"}

    option = ConnectorBuilderOption(ConnectorBuilderChoice.PRIME3_WII, {"ip": "192.168.1.42", "port": 12345})
    restored = option.create_builder()
    assert isinstance(restored, Prime3WiiConnectorBuilder)
    assert restored.ip == "192.168.1.42"
    assert restored._port == 43674


async def test_builder_uses_bounded_reconnect_backoff(mocker) -> None:
    clock = MagicMock(return_value=100.0)
    builder = Prime3WiiConnectorBuilder("192.168.1.42", monotonic=clock)
    executor_type = mocker.patch(
        "randovania.game_connection.builder.prime3_wii_connector_builder.Prime3WiiExecutor",
        autospec=True,
    )
    executor = executor_type.return_value
    executor.connect = AsyncMock(return_value="timeout")

    assert await builder.build_connector() is None
    assert builder.get_status_message() == "Wii did not respond: timeout Retrying in 1 seconds."
    executor_type.assert_called_once_with("192.168.1.42", 43674)

    assert await builder.build_connector() is None
    executor_type.assert_called_once()
    clock.return_value = 101.0
    assert await builder.build_connector() is None
    assert builder.get_status_message() == "Wii did not respond: timeout Retrying in 2 seconds."


def test_choice_is_explicit_and_single_instance() -> None:
    choice = ConnectorBuilderChoice.PRIME3_WII
    assert choice.pretty_text == "Wii / Wii U (Prime 3)"
    assert not choice.supports_multiple_instances()


def test_factory_architecture_keeps_candidates_corruption_only() -> None:
    builder = Prime3WiiConnectorBuilder("192.168.1.42")
    executor = builder.create_executor()
    candidates = builder.create_connector_candidates(AsyncMock())

    assert isinstance(executor, Prime3WiiExecutor)
    assert executor.port == 43674
    assert candidates
    assert all(isinstance(candidate, CorruptionRemoteConnector) for candidate in candidates)
