"""Configuration user interface for device setup."""

import logging
from datetime import datetime
from typing import Any, Optional

from rich.console import Console

from simulator.api import FirmwareVersionApi
from simulator.api.device_creation_metadata_api import DeviceCreationMetadataApi
from simulator.config.config_manager import ConfigManager, DeviceConfig
from simulator.provisioning.device_provisioner import DeviceProvisioner

from .device_selector import DeviceSelector


class ConfigurationUI:
    """Handles device configuration setup through user interface."""

    def __init__(
        self,
        config_manager: ConfigManager,
        device_metadata_api: DeviceCreationMetadataApi,
        device_provisioner: DeviceProvisioner,
        device_selector: DeviceSelector,
        firmware_version_api: FirmwareVersionApi,
        console: Console,
    ):
        self.config_manager = config_manager
        self.platform_api = device_metadata_api
        self.device_provisioner = device_provisioner
        self.device_selector = device_selector
        self.firmware_version_manager = firmware_version_api
        self.console = console
        self.logger = logging.getLogger(__name__)

    async def setup_new_device(self) -> None:
        """Setup a new device using the provisioner API."""
        self.console.print("\n[bold]Step 2: New Device Configuration[/bold]")
        device_id = self.device_selector.get_device_id()
        group_id = await self._get_group_id()
        selected_device_type = await self._get_device_type()
        await self._provision_device(device_id, group_id, selected_device_type)
        self._save_schema(selected_device_type)
        firmware_version = await self._fetch_fw_version(selected_device_type)
        self._save_device_config(device_id, selected_device_type, firmware_version)

    def _save_device_config(
        self,
        device_id: str,
        selected_device_type: dict[str, Any],
        firmware_version: Optional[str],
    ) -> None:
        device_config = DeviceConfig(
            deviceId=device_id,
            gatewayId=device_id,  # Use device_id as gateway_id
            deviceType=selected_device_type["name"],
            lastUpdated=datetime.now().isoformat(),
            firmwareVersion=firmware_version,
        )

        self.config_manager.save_device_config(device_config)
        self.console.print(
            f"[green]✅ New device '{device_id}' configured successfully![/green]"
        )

    def _save_schema(self, schema: dict) -> None:
        """Save device type schema."""
        schema_name = schema["name"]

        if schema_name is None:
            self.console.print("[red]❌ Schema name is required[/red]")
            return

        if self.config_manager.has_schema(schema_name):
            self.console.print(
                f"[green]✅ Schema for '{schema_name}' already exists[/green]"
            )
            return

        self.console.print(
            f"[blue]📥 Saving schema for device type '{schema_name}'...[/blue]"
        )

        self.config_manager.save_schema(schema_name, schema)

        self.console.print(f"[green]✅ Schema for '{schema_name}' is saved[/green]")

    async def _fetch_fw_version(
        self, selected_device_type: dict[str, Any]
    ) -> Optional[str]:
        device_type_name: str = selected_device_type["name"]
        self.console.print(
            f"[blue]🔄 Fetching latest firmware version for '{device_type_name}'...[/blue]"
        )
        firmware_version = await self.firmware_version_manager.get_latest_version(
            device_type_name
        )

        if firmware_version:
            self.console.print(
                f"[green]✅ Latest firmware version: {firmware_version}[/green]"
            )

        return firmware_version

    async def _provision_device(
        self, device_id: str, group_id: str, selected_device_type: dict[str, Any]
    ) -> None:
        self.console.print(
            f"[blue]🔧 Provisioning device '{device_id}' with certificates...[/blue]"
        )
        provision_result = await self.device_provisioner.provision_device(
            device_id=device_id,
            device_type=selected_device_type["name"],
            group_id=group_id,
            override_if_exists=True,
        )

        self.console.print("[green]✅ Device provisioned successfully![/green]")
        self.console.print(
            f"[blue]📁 Certificates saved to: {provision_result.private_key_path}[/blue]"
        )

    async def _get_device_type(self) -> dict[str, Any]:
        device_types = await self.platform_api.get_device_types()
        selected_device_type = self.device_selector.select_device_type(device_types)
        return selected_device_type

    async def _get_group_id(self) -> str:
        groups = await self.platform_api.get_managed_groups()
        self.logger.debug(f"Retrieved groups: {groups}")
        selected_group = self.device_selector.select_managed_group(groups)
        group_id: str = selected_group["id"]
        return group_id
