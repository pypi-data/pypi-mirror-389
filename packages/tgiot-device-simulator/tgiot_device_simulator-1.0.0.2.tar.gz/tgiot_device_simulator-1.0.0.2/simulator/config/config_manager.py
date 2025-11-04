"""Configuration management module."""

import json
import logging
from pathlib import Path
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from .schemas import DeviceSchema


class OAuth2Config(BaseModel):
    """OAuth2 configuration."""

    model_config = ConfigDict(populate_by_name=True)

    client_id: str = Field(alias="clientId")
    authorization_endpoint: str = Field(alias="authorization_endpoint")
    token_endpoint: str = Field(alias="token_endpoint")


class IoTPlatformConfig(BaseModel):
    """IoT Platform configuration."""

    model_config = ConfigDict(populate_by_name=True)

    base_url: str = Field(alias="baseUrl")
    oauth2: OAuth2Config


class MessagingConfig(BaseModel):
    """Messaging intervals and enabled status configuration."""

    model_config = ConfigDict(populate_by_name=True)

    intervals: dict[str, int]
    enabled: dict[str, bool]


class LoggingConfig(BaseModel):
    """Logging configuration."""

    model_config = ConfigDict(populate_by_name=True)

    level: str = "INFO"
    file: str = "logs/simulator.log"


class IoTHubConfig(BaseModel):
    """IoT Hub configuration."""

    model_config = ConfigDict(populate_by_name=True)

    host_name: str = Field(alias="hostName")


class ProvisionerConfig(BaseModel):
    """Provisioner configuration."""

    model_config = ConfigDict(populate_by_name=True)

    base_url: str = Field(alias="baseUrl")


class AppConfig(BaseModel):
    """Main application configuration."""

    model_config = ConfigDict(populate_by_name=True)

    iot_platform: IoTPlatformConfig = Field(alias="iotPlatform")
    provisioner: ProvisionerConfig
    iot_hub: IoTHubConfig = Field(alias="iotHub")
    messaging: MessagingConfig
    logging: LoggingConfig


class DeviceConfig(BaseModel):
    """Device-specific configuration."""

    model_config = ConfigDict(populate_by_name=True)

    device_id: str = Field(alias="deviceId")
    gateway_id: Optional[str] = Field(alias="gatewayId", default=None)
    device_type: str = Field(alias="deviceType")
    last_updated: str = Field(alias="lastUpdated")
    firmware_version: Optional[str] = Field(alias="firmwareVersion", default=None)


class ConfigManager:
    """Manages application and device configuration."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path("config")
        self.schemas_dir = Path("schemas")

        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        self.schemas_dir.mkdir(exist_ok=True)
        self._device_config: Optional[DeviceConfig] = None

        # Load application configuration
        self.app_config = self.load_app_config()

    @property
    def device_config(self) -> DeviceConfig:
        """Get device configuration, raising an exception if not loaded."""
        if self._device_config is None:
            raise ValueError(
                "Device configuration is not loaded. Call load_device_config() first."
            )
        return self._device_config

    @device_config.setter
    def device_config(self, value: Optional[DeviceConfig]) -> None:
        """Set device configuration."""
        self._device_config = value

    def load_app_config(self) -> AppConfig:
        """Load application configuration from config.json."""
        config_file = self.config_dir / "config.json"

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        try:
            with open(config_file) as f:
                config_data = json.load(f)

            app_config = AppConfig(**config_data)
            self.logger.info("Application configuration loaded successfully")
            return app_config

        except Exception as e:
            self.logger.error(f"Failed to load application configuration: {e}")
            raise

    def has_device_config(self) -> bool:
        """Check if device configuration exists."""
        device_config_file = self.config_dir / "device-config.json"
        return device_config_file.exists()

    def load_device_config(self) -> None:
        """Load device configuration from device-config.json."""
        device_config_file = self.config_dir / "device-config.json"

        if not device_config_file.exists():
            raise FileNotFoundError(
                f"Device configuration file not found: {device_config_file}"
            )

        try:
            with open(device_config_file) as f:
                config_data = json.load(f)

            self._device_config = DeviceConfig(**config_data)
            self.logger.info(
                f"Device configuration loaded for device: {self._device_config.device_id}"
            )

        except Exception as e:
            self.logger.error(f"Failed to load device configuration: {e}")
            raise

    def save_device_config(self, device_config: DeviceConfig) -> None:
        """Save device configuration to device-config.json."""
        device_config_file = self.config_dir / "device-config.json"

        try:
            config_data = device_config.model_dump(by_alias=True)

            with open(device_config_file, "w") as f:
                json.dump(config_data, f, indent=2)

            self._device_config = device_config
            self.logger.info(
                f"Device configuration saved for device: {device_config.device_id}"
            )

        except Exception as e:
            self.logger.error(f"Failed to save device configuration: {e}")
            raise

    def get_schema_path(self, device_type: str) -> Path:
        """Get the path to a device type schema file."""
        return self.schemas_dir / f"{device_type}-schema.json"

    def has_schema(self, device_type: str) -> bool:
        """Check if schema exists for device type."""
        return self.get_schema_path(device_type).exists()

    def load_schema(self, device_type: str) -> DeviceSchema:
        """Load device type schema as a structured object."""
        schema_file = self.get_schema_path(device_type)

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        try:
            with open(schema_file) as f:
                schema_data = json.load(f)

            # Convert the JSON data to a DeviceSchema object
            return DeviceSchema(**schema_data)

        except Exception as e:
            self.logger.error(f"Failed to load schema for {device_type}: {e}")
            raise

    def load_schema_raw(self, device_type: str) -> dict[str, Any]:
        """Load device type schema as raw dictionary (for backward compatibility)."""
        schema_file = self.get_schema_path(device_type)

        if not schema_file.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_file}")

        try:
            with open(schema_file) as f:
                schema_data = json.load(f)
                if not isinstance(schema_data, dict):
                    raise ValueError(
                        f"Schema file {schema_file} does not contain a valid JSON object"
                    )
                return schema_data

        except Exception as e:
            self.logger.error(f"Failed to load raw schema for {device_type}: {e}")
            raise

    def save_schema(
        self, device_type: str, schema: Union[dict[str, Any], DeviceSchema]
    ) -> None:
        """Save device type schema."""
        schema_file = self.get_schema_path(device_type)

        try:
            # Convert DeviceSchema to dictionary if needed
            if isinstance(schema, DeviceSchema):
                schema_data = schema.model_dump(by_alias=True)
            else:
                schema_data = schema

            with open(schema_file, "w") as f:
                json.dump(schema_data, f, indent=2)

            self.logger.info(f"Schema saved for device type: {device_type}")

        except Exception as e:
            self.logger.error(f"Failed to save schema for {device_type}: {e}")
            raise
