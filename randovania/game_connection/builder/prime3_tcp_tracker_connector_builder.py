from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from randovania.game_connection.builder.connector_builder import ConnectorBuilder
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.server.prime3_tracker import Prime3TrackerAdapter, Prime3TrackerService, Prime3TrackerSession

if TYPE_CHECKING:
    from randovania.game_connection.connector.remote_connector import RemoteConnector


class Prime3TcpTrackerConnectionManager:
    """Routes inbound TCP tracker sessions to user-configured Prime 3 connections."""

    def __init__(self, configuration: dict[str, object] | None = None):
        self._connections: set[Prime3TcpTrackerConnectorBuilder] = set()
        self._bindings: dict[int, Prime3TcpTrackerConnectorBuilder] = {}
        self._adapter = Prime3TrackerAdapter(self._publish, self._bind_session)
        self._service = Prime3TrackerService(
            configuration
            or {
                "enabled": True,
                "bind_host": "0.0.0.0",
                "bind_port": 43674,
                "idle_timeout_seconds": 30,
                "maximum_clients": 8,
            },
            self._adapter,
        )

    @property
    def service(self) -> Prime3TrackerService:
        return self._service

    def register(self, connection: Prime3TcpTrackerConnectorBuilder) -> None:
        self._connections.add(connection)
        try:
            self._service.start()
        except OSError as error:
            connection._set_error(f"Unable to start Prime 3 TCP listener: {error}")
            return
        connection._set_waiting()

    def unregister(self, connection: Prime3TcpTrackerConnectorBuilder) -> None:
        self._connections.discard(connection)
        for nonce, bound_connection in list(self._bindings.items()):
            if bound_connection is connection:
                del self._bindings[nonce]
        if not self._connections:
            self._service.stop()

    def _bind_session(self, session: Prime3TrackerSession) -> bool:
        exact = [
            connection
            for connection in self._connections
            if (
                connection.enabled
                and connection.bound_client_nonce is None
                and connection.client_nonce == session.client_nonce
            )
        ]
        unbound = [
            connection
            for connection in self._connections
            if connection.enabled and connection.bound_client_nonce is None and connection.client_nonce is None
        ]
        candidates = exact or unbound
        if len(candidates) != 1:
            for connection in candidates:
                connection._set_error("Ambiguous inbound Prime 3 Wii session")
            return False
        connection = candidates[0]
        connection._bind(session)
        self._bindings[session.client_nonce] = connection
        return True

    def _publish(self, event: dict[str, object]) -> None:
        client_nonce = event["client_nonce"]
        if not isinstance(client_nonce, int):
            return
        connection = self._bindings.get(client_nonce)
        if connection is not None:
            connection._update(event)


_manager: Prime3TcpTrackerConnectionManager | None = None


def prime3_tcp_tracker_connection_manager() -> Prime3TcpTrackerConnectionManager:
    global _manager
    if _manager is None:
        _manager = Prime3TcpTrackerConnectionManager()
    return _manager


class Prime3TcpTrackerConnectorBuilder(ConnectorBuilder):
    """A user-owned inbound Prime 3 TCP tracker connection, never a Wii UDP client."""

    def __init__(
        self,
        *,
        name: str = "Prime 3 Wii",
        client_nonce: int | None = None,
        seed_id: int | None = None,
        enabled: bool = True,
        manager: Prime3TcpTrackerConnectionManager | None = None,
    ):
        super().__init__()
        self.name = name
        self.client_nonce = client_nonce
        self.seed_id = seed_id
        self.enabled = enabled
        self._manager = manager or prime3_tcp_tracker_connection_manager()
        self._registered = False
        self._bound_client_nonce: int | None = None
        self._status: dict[str, object] = {"state": "waiting", "message": "Waiting for Wii connection"}
        self.logger = logging.getLogger(type(self).__name__)

    @property
    def connector_builder_choice(self) -> ConnectorBuilderChoice:
        return ConnectorBuilderChoice.PRIME3_WII

    @property
    def pretty_text(self) -> str:
        return f"{self.connector_builder_choice.pretty_text}: {self.name}"

    @property
    def bound_client_nonce(self) -> int | None:
        return self._bound_client_nonce

    @property
    def tracker_status(self) -> dict[str, object]:
        return dict(self._status)

    def configuration_params(self) -> dict:
        return {
            "name": self.name,
            "client_nonce": self.client_nonce,
            "seed_id": self.seed_id,
            "enabled": self.enabled,
        }

    def get_status_message(self) -> str | None:
        return str(self._status["message"])

    async def build_connector(self) -> RemoteConnector | None:
        if not self.enabled:
            self._set_status("disabled", "Prime 3 TCP tracker connection is disabled")
            return None
        if not self._registered:
            self._registered = True
            self._manager.register(self)
        return None

    def close(self) -> None:
        if self._registered:
            self._manager.unregister(self)
            self._registered = False

    def _bind(self, session: Prime3TrackerSession) -> None:
        self._bound_client_nonce = session.client_nonce
        self._set_status(
            "connected",
            "Connected to Prime 3 Wii",
            client_nonce=session.client_nonce,
            protocol_version=1,
            game_build_id=session.build_id,
            seed_id=session.seed_id,
        )

    def _update(self, event: dict[str, object]) -> None:
        connected = bool(event["connected"])
        snapshot_id = event["last_snapshot_id"]
        message = "Connected to Prime 3 Wii"
        state = "connected"
        if not connected:
            message = "Prime 3 Wii disconnected"
            state = "disconnected"
        elif isinstance(snapshot_id, int) and snapshot_id:
            message = f"Connected to Prime 3 Wii; snapshot {snapshot_id} received"
            state = "snapshot_received"
        self._set_status(state, message, **event)

    def _set_waiting(self) -> None:
        self._set_status("waiting", "Waiting for Wii connection")

    def _set_error(self, message: str) -> None:
        self._set_status("error", message, last_error=message)

    def _set_status(self, state: str, message: str, **fields: object) -> None:
        self._status = {"state": state, "message": message, **fields}
        self.logger.info(message)
        self.StatusUpdate.emit(message)
