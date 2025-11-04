"""Version information for the simulator package."""

import importlib.metadata
from typing import Optional


def get_version() -> Optional[str]:
    """Get the version of the simulator package."""
    try:
        return importlib.metadata.version("tgiot-device-simulator")
    except importlib.metadata.PackageNotFoundError:
        # Fallback for development mode
        return "dev"


__version__ = get_version()
