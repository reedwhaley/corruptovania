from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.builder.connector_builder_option import ConnectorBuilderOption
from randovania.game_connection.builder.prime3_wii_connector_builder import Prime3WiiConnectorBuilder
from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.connector.corruption_remote_connector import CorruptionRemoteConnector
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.prime3_wii_executor import DEFAULT_PRIME3_WII_PORT, Prime3WiiExecutor
from randovania.game_connection.executor.prime3_wii_protocol import (
    DEFAULT_RUNTIME_BUILD_ID,
    HELLO_METADATA_VERSION,
    HELLO_RUNTIME_CAPABILITIES,
    HelloResponsePayload,
    Prime3WiiCapability,
    Prime3WiiCommand,
    Prime3WiiResponse,
    Prime3WiiResponseStatus,
    encode_hello_response_payload,
    encode_response,
)
from randovania.games.prime3.exporter.dol_patcher import patch_prime3_corruption_dol
from randovania.interface_common.players_configuration import INVALID_UUID
from test.game_connection.executor.prime3_wii_fake_corruption_memory import Prime3WiiFakeCorruptionMemory
from test.game_connection.executor.prime3_wii_fake_server import Prime3WiiFakeServer
from test.games.prime3.exporter.test_dol_patcher import _build_synthetic_dol


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
    memory = Prime3WiiFakeCorruptionMemory.create(
        corruption_dol_versions.ALL_VERSIONS[0],
        uuid.UUID("12345678-1234-5678-1234-567812345678"),
    )
    return memory


@pytest.fixture(name="builder")
def builder_fixture(server: Prime3WiiFakeServer):
    return Prime3WiiConnectorBuilder("127.0.0.1", port=server.port)


async def test_create_and_round_trip(server: Prime3WiiFakeServer):
    builder = Prime3WiiConnectorBuilder("192.168.1.44", port=server.port)
    assert builder.connector_builder_choice is ConnectorBuilderChoice.PRIME3_WII
    assert builder.pretty_text == f"Prime 3 Wii: 192.168.1.44:{server.port}"
    assert builder.configuration_params() == {"ip": "192.168.1.44", "port": server.port}

    option = ConnectorBuilderOption(ConnectorBuilderChoice.PRIME3_WII, builder.configuration_params())
    rebuilt = option.create_builder()
    assert isinstance(rebuilt, Prime3WiiConnectorBuilder)
    assert rebuilt.configuration_params() == builder.configuration_params()

    default_builder = Prime3WiiConnectorBuilder("192.168.1.44")
    assert default_builder.pretty_text == "Prime 3 Wii: 192.168.1.44"
    assert default_builder.configuration_params() == {"ip": "192.168.1.44"}
    executor = default_builder.create_executor()
    assert isinstance(executor, Prime3WiiExecutor)
    assert executor.port == DEFAULT_PRIME3_WII_PORT


def test_choice_visibility():
    assert ConnectorBuilderChoice.PRIME3_WII.pretty_text == "Prime 3 Wii"
    assert ConnectorBuilderChoice.PRIME3_WII in ConnectorBuilderChoice.all_usable_choices()
    assert ConnectorBuilderChoice.PRIME3_WII.supports_multiple_instances()


async def test_only_corruption_candidates(builder: Prime3WiiConnectorBuilder):
    executor = AsyncMock()
    candidates = builder.create_connector_candidates(executor)

    assert candidates
    assert all(isinstance(candidate, CorruptionRemoteConnector) for candidate in candidates)
    assert len(candidates) == len(corruption_dol_versions.ALL_VERSIONS)


async def test_default_prime_builder_candidates_unchanged():
    class StubPrimeBuilder(PrimeConnectorBuilder):
        def create_executor(self):
            return AsyncMock()

        @property
        def connector_builder_choice(self):
            return ConnectorBuilderChoice.DOLPHIN

        def configuration_params(self) -> dict:
            return {}

    builder = StubPrimeBuilder()
    candidates = builder.create_connector_candidates(AsyncMock())
    names = {type(candidate).__name__ for candidate in candidates}
    assert "Prime1RemoteConnector" in names
    assert "EchoesRemoteConnector" in names
    assert "CorruptionRemoteConnector" in names


async def test_successful_connection(builder: Prime3WiiConnectorBuilder, server: Prime3WiiFakeServer, memory):
    messages: list[str] = []
    builder.StatusUpdate.connect(messages.append)
    memory.load_into(server)
    with patch(
        "randovania.game_connection.connector.prime_remote_connector.PrimeRemoteConnector.start_updates"
    ) as mock_start_updates:
        connector = await builder.build_connector()

        assert isinstance(connector, CorruptionRemoteConnector)
        assert connector.version is memory.version
        assert connector.layout_uuid == memory.layout_uuid
        assert connector.game_enum == RandovaniaGame.METROID_PRIME_CORRUPTION
        assert connector.description() == (
            f"{RandovaniaGame.METROID_PRIME_CORRUPTION.long_name}: {memory.version.description}"
        )
        assert builder.get_status_message() == f"identified game as {connector.description()}"
        assert messages[:2] == ["Connecting...", "Identifying game..."]
        assert messages[-1] == builder.get_status_message()
        assert mock_start_updates.called


async def test_only_corruption_addresses_probed(
    builder: Prime3WiiConnectorBuilder, server: Prime3WiiFakeServer, memory
):
    memory.load_into(server)
    with patch("randovania.game_connection.connector.prime_remote_connector.PrimeRemoteConnector.start_updates"):
        await builder.build_connector()

        expected_probe_count = len(corruption_dol_versions.ALL_VERSIONS)
        probe_addresses = [payload.address for payload in server.read_requests[:expected_probe_count]]
        expected_addresses = [version.build_string_address for version in corruption_dol_versions.ALL_VERSIONS]
        assert probe_addresses == expected_addresses
        assert all(payload.size == 4 for payload in server.read_requests[:expected_probe_count])


async def test_invalid_build_string_returns_none(
    builder: Prime3WiiConnectorBuilder, server: Prime3WiiFakeServer, memory
):
    memory.load_into(server)
    server.load_bytes(memory.version.build_string_address, b"BAD!" + memory.version.build_string[4:])
    with patch("randovania.game_connection.connector.prime_remote_connector.PrimeRemoteConnector.start_updates"):
        connector = await builder.build_connector()

        assert connector is None
        assert builder.get_status_message() == "Could not identify which game it is"


async def test_builder_round_trips_uuid_from_patched_synthetic_dol(
    builder: Prime3WiiConnectorBuilder,
    server: Prime3WiiFakeServer,
) -> None:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    layout_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    synthetic_dol = _build_synthetic_dol(version, section_address=version.build_string_address - 0x20)
    patched_dol, _result = patch_prime3_corruption_dol(synthetic_dol, layout_uuid, version=version)

    build_string_offset = version.build_string_address - (version.build_string_address - 0x20) + 0x100
    patched_build_string = patched_dol[build_string_offset : build_string_offset + len(version.build_string)]

    memory = Prime3WiiFakeCorruptionMemory.create(version, uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"))
    memory.load_into(server)
    server.load_bytes(version.build_string_address, patched_build_string)

    with patch("randovania.game_connection.connector.prime_remote_connector.PrimeRemoteConnector.start_updates"):
        connector = await builder.build_connector()

    assert isinstance(connector, CorruptionRemoteConnector)
    assert connector.layout_uuid == layout_uuid


async def test_builder_retail_build_string_returns_invalid_uuid(
    builder: Prime3WiiConnectorBuilder,
    server: Prime3WiiFakeServer,
) -> None:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    memory = Prime3WiiFakeCorruptionMemory.create(version, uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"))
    memory.load_into(server)
    server.load_bytes(version.build_string_address, version.build_string)

    with patch("randovania.game_connection.connector.prime_remote_connector.PrimeRemoteConnector.start_updates"):
        connector = await builder.build_connector()

    assert isinstance(connector, CorruptionRemoteConnector)
    assert connector.layout_uuid == INVALID_UUID


async def test_builder_rejects_malformed_patched_identity(
    builder: Prime3WiiConnectorBuilder,
    server: Prime3WiiFakeServer,
) -> None:
    version = corruption_dol_versions.ALL_VERSIONS[0]
    layout_uuid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    synthetic_dol = _build_synthetic_dol(version, section_address=version.build_string_address - 0x20)
    patched_dol, _result = patch_prime3_corruption_dol(synthetic_dol, layout_uuid, version=version)

    build_string_offset = version.build_string_address - (version.build_string_address - 0x20) + 0x100
    malformed_build_string = bytearray(
        patched_dol[build_string_offset : build_string_offset + len(version.build_string)]
    )
    malformed_build_string[-1] ^= 0x01

    memory = Prime3WiiFakeCorruptionMemory.create(version, layout_uuid)
    memory.load_into(server)
    server.load_bytes(version.build_string_address, bytes(malformed_build_string))

    with patch("randovania.game_connection.connector.prime_remote_connector.PrimeRemoteConnector.start_updates"):
        connector = await builder.build_connector()

    assert connector is None


async def test_unsupported_protocol_returns_useful_status(
    builder: Prime3WiiConnectorBuilder, server: Prime3WiiFakeServer
):
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

    connector = await builder.build_connector()

    assert connector is None
    assert builder.get_status_message() == "Server reported unsupported protocol version 2."


async def test_server_disconnect_during_identification(builder: Prime3WiiConnectorBuilder, server: Prime3WiiFakeServer):
    server.drop_next(Prime3WiiCommand.READ_MEMORY, count=2)

    connector = await builder.build_connector()

    assert connector is None
    assert "Unable to probe for game version" in str(builder.get_status_message())
