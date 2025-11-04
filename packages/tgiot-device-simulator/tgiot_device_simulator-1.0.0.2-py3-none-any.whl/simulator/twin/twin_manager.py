"""Device Twin management module."""

import logging
from typing import Any

from simulator.config.config_manager import ConfigManager
from simulator.connectivity.iot_hub_client import IoTHubClient

from .default_config_applier import DefaultConfigApplier
from .firmware_reporter import FirmwareReporter
from .reported_store import TwinReportedStore


class TwinManager:
    """
    Manages device twin operations, delegates property sync, default config, and firmware reporting.
    """

    def __init__(self, iot_client: IoTHubClient, config_manager: ConfigManager) -> None:
        self.iot_client = iot_client
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.current_desired_properties: dict[str, Any] = {}
        self.current_reported_properties: dict[str, Any] = {}
        self.reported_store = TwinReportedStore(
            self.config_manager.device_config.device_id
        )

        self.default_config_applier = DefaultConfigApplier(
            self.logger,
            self.config_manager,
            self.update_reported_property,
        )
        self.firmware_reporter = FirmwareReporter(
            self.logger,
            self.config_manager,
            self.update_reported_property,
        )

        # Set twin patch handler
        self.iot_client.set_twin_patch_handler(self.handle_twin_patch)

    async def start(self) -> None:
        """Start twin management."""
        self.logger.info("Starting twin management...")
        try:
            twin = await self.iot_client.get_twin()
            self.current_desired_properties.update(twin.get("desired", {}))
            self.current_reported_properties.update(twin.get("reported", {}))
            device_id = self.config_manager.device_config.device_id
            current_reported_device = self.current_reported_properties.get(
                "devices", {}
            ).get(device_id, {})
            current_desired_device = self.current_desired_properties.get(
                "devices", {}
            ).get(device_id, {})

            await self.default_config_applier.apply_initial_configurations(
                device_id, current_reported_device, current_desired_device
            )
            await self.firmware_reporter.ensure_firmware_version_reported(
                device_id, current_reported_device
            )
            self.logger.info("Twin management started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start twin management: {e}")
            raise

    async def handle_twin_patch(self, patch: dict[str, Any]) -> None:
        """Handle twin desired properties patch. Only process 'devices.{deviceid}.configs' patches."""
        self.logger.info(f"[TWIN] Desired property updated from IoT Hub: {patch}")
        self.current_desired_properties.update(patch)
        device_id: str = self.config_manager.device_config.device_id
        if not device_id:
            self.logger.warning(
                "[TWIN] Device ID is not set in device configuration. Cannot process twin patch."
            )
            return
        configs_patch = None
        # For now, only handle 'devices.{deviceid}.configs' patches
        devices = patch.get("devices", {})
        if device_id in devices:
            configs_patch = devices[device_id].get("configs")
        if configs_patch is not None:
            await self.update_reported_property(
                {"devices": {device_id: {"configs": configs_patch}}}
            )
            self.logger.info(
                f"[TWIN] Reported properties updated: devices.{device_id}.configs = {configs_patch}"
            )

    async def update_reported_property(self, patch: dict[str, Any]) -> None:
        """Update a single reported property using a patch, preserving the original structure."""
        try:
            self.current_reported_properties.update(patch)
            self.reported_store.save(self.current_reported_properties)
            await self.iot_client.patch_twin_reported_properties(patch)
            self.logger.debug(f"[TWIN] Patched reported property: {patch}")
        except Exception as e:
            self.logger.error(f"Failed to patch reported property {patch}: {e}")
