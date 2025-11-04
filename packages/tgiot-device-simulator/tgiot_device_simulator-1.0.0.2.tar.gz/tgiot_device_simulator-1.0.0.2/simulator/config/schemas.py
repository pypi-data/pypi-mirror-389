"""Device schema models for configuration management."""

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceModelSpecSupportedMethods(BaseModel):
    """Device model supported method specification."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(description="Method identifier")
    description: Optional[str] = Field(default=None, description="Method description")
    payload_schema: Optional[dict[str, Any]] = Field(
        alias="payloadSchema", default=None, description="Payload schema"
    )
    response_schema: Optional[dict[str, Any]] = Field(
        alias="responseSchema", default=None, description="Response schema"
    )
    multi_device_support: Optional[bool] = Field(
        alias="multiDeviceSupport",
        default=None,
        description="Multi-device support flag",
    )


class SchemaModelInfo(BaseModel):
    """Schema model information."""

    model_config = ConfigDict(populate_by_name=True)

    configurations: dict[str, Any] = Field(default_factory=dict)
    status_additional_data: dict[str, Any] = Field(
        alias="statusAdditionalData", default_factory=dict
    )
    supported_methods: list[DeviceModelSpecSupportedMethods] = Field(
        alias="supportedMethods", default_factory=list
    )
    metadata: object = Field(default_factory=object)
    info: object = Field(default_factory=object)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    measurements: list[dict[str, Any]] = Field(default_factory=list)


class DeviceSchema(BaseModel):
    """Device type schema model."""

    model_config = ConfigDict(populate_by_name=True)

    model: SchemaModelInfo
    min_version: Optional[str] = Field(alias="minVersion", default=None)
    max_version: Optional[str] = Field(alias="maxVersion", default=None)
    device_type: str = Field(alias="deviceType")
    id: str
    schema_version: Optional[str] = Field(alias="schemaVersion", default=None)

    def get_measurements(self) -> list[dict[str, Any]]:
        """Get measurements from schema."""
        return self.model.measurements

    def get_alerts(self) -> list[dict[str, Any]]:
        """Get alerts from schema."""
        return self.model.alerts

    def get_supported_methods(self) -> list[DeviceModelSpecSupportedMethods]:
        """Get supported methods from schema."""
        return self.model.supported_methods

    def get_supported_method_ids(self) -> list[str]:
        """Get list of supported method IDs."""
        return [method.id for method in self.model.supported_methods]

    def get_configurations(self) -> dict[str, Any]:
        """Get configurations from schema."""
        return self.model.configurations

    def get_status_additional_data(self) -> dict[str, Any]:
        return self.model.status_additional_data

    def has_measurement(self, measurement_name: str) -> bool:
        """Check if schema has a specific measurement."""
        return any(m.get("name") == measurement_name for m in self.model.measurements)

    def has_alert(self, alert_name: str) -> bool:
        """Check if schema has a specific alert."""
        return any(a.get("name") == alert_name for a in self.model.alerts)

    def supports_method(self, method_id: str) -> bool:
        """Check if schema supports a specific method by ID."""
        return any(method.id == method_id for method in self.model.supported_methods)

    def get_method_by_id(
        self, method_id: str
    ) -> Optional[DeviceModelSpecSupportedMethods]:
        """Get a specific method by its ID."""
        for method in self.model.supported_methods:
            if method.id == method_id:
                return method
        return None
