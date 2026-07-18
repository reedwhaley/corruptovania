from __future__ import annotations

import importlib
import ipaddress
import logging
import time
from typing import TYPE_CHECKING

from randovania.game_connection.builder.prime_connector_builder import PrimeConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.executor.memory_operation import MemoryOperationException
from randovania.game_connection.executor.prime3_wii_executor import DEFAULT_PRIME3_WII_PORT, Prime3WiiExecutor
from randovania.game_connection.executor.prime3_wii_protocol import Prime3WiiRevisionId
from randovania.interface_common.players_configuration import INVALID_UUID

if TYPE_CHECKING:
    from collections.abc import Callable

    from randovania.game_connection.connector.prime_remote_connector import PrimeRemoteConnector
    from randovania.game_connection.connector.remote_connector import RemoteConnector
    from randovania.game_connection.executor.memory_operation import MemoryOperationExecutor


MAX_RECONNECT_BACKOFF_SECONDS = 10.0


def validate_wii_ip_address(value: str, *, allow_loopback: bool = False) -> str:
    address_text = value.strip()
    if not address_text:
        raise ValueError("Enter the Wii IP address.")
    if "://" in address_text:
        raise ValueError("Enter an IPv4 address without a URI scheme.")
    if ":" in address_text:
        raise ValueError("Enter only the Wii IP address; CP3W always uses UDP port 43674.")
    try:
        address = ipaddress.ip_address(address_text)
    except ValueError as exc:
        raise ValueError("Enter a valid IPv4 address, for example 192.168.1.42.") from exc
    if not isinstance(address, ipaddress.IPv4Address):
        raise ValueError("Wii / Wii U connections currently require an IPv4 address.")
    if address.is_unspecified:
        raise ValueError("The unspecified address cannot identify a Wii.")
    if address.is_multicast:
        raise ValueError("A multicast address cannot identify a Wii.")
    if address == ipaddress.IPv4Address("255.255.255.255") or int(address) & 0xFF == 0xFF:
        raise ValueError("A broadcast address cannot identify a Wii.")
    if address.is_loopback and not allow_loopback:
        raise ValueError("Loopback is reserved for local CP3W diagnostics.")
    return str(address)


class Prime3WiiConnectorBuilder(PrimeConnectorBuilder):
    def __init__(
        self,
        ip: str,
        *,
        port: int = DEFAULT_PRIME3_WII_PORT,
        allow_loopback: bool = False,
        monotonic: Callable[[], float] = time.monotonic,
    ):
        super().__init__()
        self.ip = validate_wii_ip_address(ip, allow_loopback=allow_loopback)
        self._port = port
        self._allow_loopback = allow_loopback
        self._monotonic = monotonic
        self._last_status_message: str | None = None
        self._failed_attempts = 0
        self._next_attempt_at = 0.0
        self._ever_connected = False
        self._reconnect_count = 0
        self._last_executor: Prime3WiiExecutor | None = None
        self.logger = logging.getLogger(type(self).__name__)

    @property
    def pretty_text(self) -> str:
        return f"{super().pretty_text}: {self.ip}"

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.PRIME3_WII

    @property
    def reconnect_count(self) -> int:
        return self._reconnect_count

    @property
    def last_executor(self) -> Prime3WiiExecutor | None:
        return self._last_executor

    def get_status_message(self) -> str | None:
        return self._last_status_message

    def configuration_params(self) -> dict:
        # The protocol port and all transient socket/session state are deliberately not persisted.
        return {"ip": self.ip}

    def create_executor(self) -> MemoryOperationExecutor:
        return Prime3WiiExecutor(self.ip, self._port)

    def create_connector_candidates(self, executor: MemoryOperationExecutor) -> list[PrimeRemoteConnector]:
        corruption_dol_versions = importlib.import_module("open_prime_rando.dol_patching.corruption.dol_versions")
        connector_module = importlib.import_module("randovania.game_connection.connector.corruption_remote_connector")
        return [
            connector_module.CorruptionRemoteConnector(version, executor)
            for version in corruption_dol_versions.ALL_VERSIONS
        ]

    def _status_message(self, msg: str, log: bool = True) -> None:
        self._last_status_message = msg
        if log:
            self.logger.info(msg)
        self.StatusUpdate.emit(msg)

    def _record_failure(self, message: str) -> None:
        self._failed_attempts += 1
        delay = min(2 ** (self._failed_attempts - 1), MAX_RECONNECT_BACKOFF_SECONDS)
        self._next_attempt_at = self._monotonic() + delay
        status = f"{message} Retrying in {delay:g} seconds."
        self._status_message(status, log=False)
        self.logger.warning(status)

    async def build_connector(self) -> RemoteConnector | None:
        now = self._monotonic()
        if now < self._next_attempt_at:
            return None

        if self._ever_connected:
            self._status_message("Reconnecting to Wii...")
            self._reconnect_count += 1
        else:
            self._status_message("Connecting to Wii...")

        executor = Prime3WiiExecutor(self.ip, self._port)
        self._last_executor = executor
        connect_error = await executor.connect()
        if connect_error is not None:
            self._record_failure(f"Wii did not respond: {connect_error}")
            return None

        self._status_message("Validating Prime 3...")
        try:
            identity = await executor.get_game_identity()
        except MemoryOperationException as exc:
            executor.disconnect()
            self._record_failure(f"Unable to validate Prime 3: {exc}")
            return None

        supported_versions = {
            Prime3WiiRevisionId.WII_NTSC_3_436: 0,
        }
        version_index = supported_versions.get(identity.revision_id)
        if version_index is None:
            executor.disconnect()
            self._record_failure(f"Unsupported Prime 3 revision: {identity.revision_id.name}.")
            return None

        corruption_dol_versions = importlib.import_module("open_prime_rando.dol_patching.corruption.dol_versions")
        connector_module = importlib.import_module("randovania.game_connection.connector.corruption_remote_connector")
        connector = connector_module.CorruptionRemoteConnector(
            corruption_dol_versions.ALL_VERSIONS[version_index],
            executor,
        )
        connector._layout_uuid = INVALID_UUID
        connector.start_updates()

        self._failed_attempts = 0
        self._next_attempt_at = 0.0
        self._ever_connected = True
        self._status_message(
            f"Connected to Wii / Wii U; {identity.region_id.name}, {identity.revision_id.name}, "
            f"profile 0x{identity.profile_id:08X}."
        )
        return connector
