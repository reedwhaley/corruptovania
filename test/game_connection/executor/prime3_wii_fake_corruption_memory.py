from __future__ import annotations

import dataclasses
import struct
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from open_prime_rando.dol_patching.corruption import dol_versions as corruption_dol_versions

from randovania.game_connection.connector.corruption_remote_connector import (
    CorruptionRemoteConnector,
    _corruption_powerup_offset,
)
from randovania.game_description.resources.inventory import InventoryItem

if TYPE_CHECKING:
    import uuid


@dataclasses.dataclass
class Prime3WiiFakeCorruptionMemory:
    connector: CorruptionRemoteConnector
    layout_uuid: uuid.UUID
    game_state_struct: int = 0x80010000
    cstate_manager_owner: int = 0x80011000
    player_pointer: int = 0x80012000
    powerup_table: int = 0x80030000

    def __post_init__(self) -> None:
        self.region = next(region for region in self.connector.game.region_list.regions if "asset_id" in region.extra)
        self.item_states = {
            item.short_name: InventoryItem(0, 0)
            for item in self.connector.game.resource_database.item
            if item.extra["item_id"] < 1000
        }
        self.item_states["PowerBeam"] = InventoryItem(1, 1)
        self.item_states["Missile"] = InventoryItem(25, 25)
        self.item_states["Energy"] = InventoryItem(299, 299)
        self.item_states["SuitType"] = InventoryItem(5, 5)
        self.pending_operation = False

    @classmethod
    def create(cls, version, layout_uuid: uuid.UUID) -> Prime3WiiFakeCorruptionMemory:  # noqa: ANN001
        return cls(CorruptionRemoteConnector(version, AsyncMock()), layout_uuid)

    @property
    def version(self):
        return self.connector.version

    def set_pending_operation(self, pending: bool) -> None:
        self.pending_operation = pending

    def set_region(self, region_index: int) -> None:
        self.region = self.connector.game.region_list.regions[region_index]

    def set_item(self, short_name: str, amount: int, capacity: int) -> None:
        self.item_states[short_name] = InventoryItem(amount, capacity)

    def inventory_for_assertions(self) -> dict:
        return {
            self.connector.game.resource_database.get_item(short_name): value
            for short_name, value in self.item_states.items()
        }

    def _build_string_bytes(self) -> bytes:
        build_string = bytearray(self.version.build_string)
        build_string[6 : 6 + 16] = self.layout_uuid.bytes
        return bytes(build_string)

    def load_into(self, server) -> None:  # noqa: ANN001
        version = self.version
        for other_version in corruption_dol_versions.ALL_VERSIONS:
            if other_version is version:
                continue
            server.load_bytes(other_version.build_string_address, b"NOPE")
        server.load_bytes(version.build_string_address, self._build_string_bytes())
        server.store_pointer(version.game_state_pointer, self.game_state_struct)
        server.load_bytes(self.game_state_struct + 8, self.region.extra["asset_id"].to_bytes(8, "big"))
        server.store_pointer(self.game_state_struct + 36, self.powerup_table)
        server.load_bytes(version.cstate_manager_global + 2, b"\x01" if self.pending_operation else b"\x00")
        server.store_pointer(version.cstate_manager_global + 40, self.cstate_manager_owner)
        server.store_pointer(self.cstate_manager_owner + 0x2184, self.player_pointer)
        server.load_bytes(self.player_pointer, struct.pack(">I", version.cplayer_vtable))

        for item in self.connector.game.resource_database.item:
            if item.extra["item_id"] >= 1000:
                continue
            state = self.item_states[item.short_name]
            item_address = self.powerup_table + _corruption_powerup_offset(item.extra["item_id"])
            server.load_bytes(item_address, struct.pack(">II", state.amount, state.capacity))
