import logging
from typing import Any

from simulator.config.config_manager import ConfigManager
from simulator.config.schemas import DeviceSchema


class BaseMessageGenerator:
    """Base class for message generators."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

    def generate_message(self, _: DeviceSchema) -> dict[str, Any]:
        """Generate a message. To be implemented by subclasses."""
        raise NotImplementedError
