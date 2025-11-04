"""Ensures firmware version is always reported in device twin."""

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from simulator.config.config_manager import ConfigManager


class FirmwareReporter:
    def __init__(
        self,
        logger: logging.Logger,
        config_manager: ConfigManager,
        update_reported_property: Callable[[Any], Coroutine[Any, Any, None]],
    ):
        self.logger = logger
        self.config_manager = config_manager
        self.update_reported_property = update_reported_property

    async def ensure_firmware_version_reported(
        self, device_id: str, current_device: dict[str, Any]
    ) -> None:
        """Ensure firmware version is always reported in twin."""
        if (
            not self.config_manager.device_config
            or not self.config_manager.device_config.firmware_version
        ):
            self.logger.warning("[TWIN] No firmware version available to report")
            return

        try:
            current_software = current_device.get("software", {})
            current_version = current_software.get("version")
            firmware_version = self.config_manager.device_config.firmware_version

            # Only patch if version is different or missing
            if current_version != firmware_version:
                # Patch only the software section, not the entire reported properties
                await self.update_reported_property(
                    {
                        "devices": {
                            device_id: {"software": {"version": firmware_version}}
                        }
                    }
                )
                self.logger.info(
                    f"[TWIN] Patched firmware version in reported properties: {firmware_version}"
                )
            else:
                self.logger.debug(
                    f"[TWIN] Firmware version already up to date: {firmware_version}"
                )
        except Exception as e:
            self.logger.error(f"Failed to patch firmware version in twin: {e}")
