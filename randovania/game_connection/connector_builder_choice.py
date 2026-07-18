from __future__ import annotations

import os
import sys
from enum import Enum
from typing import Self

import randovania


class ConnectorBuilderChoice(Enum):
    AM2R = "am2r"
    CS = "cave-story"
    DEBUG = "debug"
    DOLPHIN = "dolphin"
    DREAD = "dread"
    NINTENDONT = "nintendont"
    MSR = "msr"
    PRIME3_WII = "prime3-wii"

    @property
    def pretty_text(self) -> str:
        return _pretty_backend_name[self]

    def is_usable(self) -> bool:
        if self is ConnectorBuilderChoice.DEBUG:
            if randovania.is_frozen() or not randovania.is_dev_version():
                return False

        if self is ConnectorBuilderChoice.DOLPHIN:
            # using sys.platform here instead of platform.system() due to a mypy limitation
            # see: https://github.com/python/mypy/issues/8166
            if sys.platform == "darwin":
                return False
            if sys.platform == "linux" and randovania.is_frozen():
                return os.getuid() == 0 and not randovania.is_flatpak()

        return True

    def supports_multiple_instances(self) -> bool:
        return self not in {ConnectorBuilderChoice.DOLPHIN, ConnectorBuilderChoice.PRIME3_WII}

    @classmethod
    def all_usable_choices(cls) -> list[Self]:
        return [r for r in cls if r.is_usable()]


_pretty_backend_name = {
    ConnectorBuilderChoice.AM2R: "AM2R",
    ConnectorBuilderChoice.CS: "Cave Story",
    ConnectorBuilderChoice.DEBUG: "Debug",
    ConnectorBuilderChoice.DOLPHIN: "Dolphin",
    ConnectorBuilderChoice.DREAD: "Dread",
    ConnectorBuilderChoice.NINTENDONT: "Nintendont",
    ConnectorBuilderChoice.MSR: "Samus Returns",
    ConnectorBuilderChoice.PRIME3_WII: "Wii / Wii U (Prime 3)",
}
