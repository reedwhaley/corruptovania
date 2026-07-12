from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.prime3_wii_executor import DEFAULT_PRIME3_WII_PORT, Prime3WiiExecutor

if TYPE_CHECKING:
    from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
    from randovania.game_connection.executor.memory_operation import MemoryOperationExecutor


class Prime3WiiConnectorBuilder(PrimeConnectorBuilder):
    ip: str
    port: int

    def __init__(self, ip: str, port: int = DEFAULT_PRIME3_WII_PORT):
        super().__init__()
        self.ip = ip
        self.port = port

    @property
    def pretty_text(self) -> str:
        suffix = self.ip
        if self.port != DEFAULT_PRIME3_WII_PORT:
            suffix = f"{suffix}:{self.port}"
        return f"{super().pretty_text}: {suffix}"

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.PRIME3_WII

    def create_executor(self) -> MemoryOperationExecutor:
        return Prime3WiiExecutor(self.ip, self.port)

    def create_connector_candidates(self, executor: MemoryOperationExecutor) -> list[PrimeRemoteConnector]:
        corruption_dol_versions = importlib.import_module("open_prime_rando.dol_patching.corruption.dol_versions")
        connector_module = importlib.import_module("randovania.game_connection.connector.corruption_remote_connector")
        CorruptionRemoteConnector = connector_module.CorruptionRemoteConnector

        return [CorruptionRemoteConnector(version, executor) for version in corruption_dol_versions.ALL_VERSIONS]

    def configuration_params(self) -> dict:
        params: dict[str, str | int] = {
            "ip": self.ip,
        }
        if self.port != DEFAULT_PRIME3_WII_PORT:
            params["port"] = self.port
        return params
