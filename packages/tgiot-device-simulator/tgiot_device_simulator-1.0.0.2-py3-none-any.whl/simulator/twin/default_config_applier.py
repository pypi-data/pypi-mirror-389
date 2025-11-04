"""Applies default configurations from schema to reported properties."""

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from simulator.config.config_manager import ConfigManager
from simulator.utils.schema.schema_generator import SchemaDataGenerator

from .reported_store import TwinReportedStore


class DefaultConfigApplier:
    def __init__(
        self,
        logger: logging.Logger,
        config_manager: ConfigManager,
        update_reported_property: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    ):
        self.logger = logger
        self.config_manager = config_manager
        self.schema_generator = SchemaDataGenerator()
        self.update_reported_property = update_reported_property

    async def apply_initial_configurations(
        self,
        device_id: str,
        current_reported_device: dict[str, Any],
        current_desired_device: dict[str, Any],
    ) -> None:
        """Apply default configurations from schema"""

        try:
            reported_store = TwinReportedStore(device_id)
            local_reported = reported_store.load()
            local_config_reported = (
                local_reported.get("devices", {}).get(device_id, {}).get("configs", {})
                if local_reported
                else None
            )

            reported_configs = None
            if local_config_reported:
                reported_configs = local_config_reported
            elif current_reported_device:
                reported_configs = current_reported_device.get("configs")

            if reported_configs:
                self.logger.info("[TWIN] Loaded configs from local TwinReportedStore")
            else:
                reported_configs = self._generate_configs_data()
                if reported_configs:
                    self.logger.info("[TWIN] Generated default configs from schema")
                else:
                    self.logger.warning(
                        "[TWIN] No default configurations or firmware version found"
                    )

            if reported_configs:
                desired_configs = current_desired_device.get("configs")
                if desired_configs:
                    reported_configs.update(desired_configs)

                await self.update_reported_property(
                    {"devices": {device_id: {"configs": reported_configs}}}
                )
        except Exception as e:
            self.logger.error(f"Failed to apply default configurations: {e}")

    def _generate_configs_data(self) -> Any:
        try:
            device_type = self.config_manager.device_config.device_type
            schema = self.config_manager.load_schema(device_type)

            configurations = schema.get_configurations()
            return self.schema_generator.create_schema_data(configurations)
        except Exception as e:
            self.logger.error(f"Failed to generate default configs: {e}")
            return {}
