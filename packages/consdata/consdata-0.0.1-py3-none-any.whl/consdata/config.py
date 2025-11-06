"""Configuration"""

import os
import warnings
from pathlib import Path


XDG_DATA_ROOT = os.getenv("XDG_DATA_HOME", "~/.local/share")
CONSDATA_ROOT = os.getenv("CONSDATA_ROOT", f"{XDG_DATA_ROOT}/consdata")


def consdata_root() -> Path:
    root = Path(CONSDATA_ROOT).expanduser()

    if not root.exists():
        warnings.warn(f"consdata root path {root} does not exist!", UserWarning, stacklevel=2)

    return root
