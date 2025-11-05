"""Measurement generator for telemetry messages."""

import random
from datetime import datetime, timezone
from typing import Any

from simulator.config.config_manager import ConfigManager
from simulator.config.schemas import DeviceSchema

from .base_message_generator import BaseMessageGenerator


class MeasurementGenerator(BaseMessageGenerator):
    """Generator for measurement messages."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def generate_message(self, device_schema: DeviceSchema) -> dict[str, Any]:
        """Generate a measurement message compliant with schema."""
        return {
            "type": "measurements",
            "data": [
                {
                    "deviceId": self.config_manager.device_config.device_id,
                    "measurements": self._generate_measurements(device_schema),
                }
            ],
        }

    def _generate_measurements(
        self, device_schema: DeviceSchema
    ) -> list[dict[str, Any]]:
        """Generate measurement data with timestamp and sensor values."""
        measurements_schema = device_schema.get_measurements()

        measurements = []

        for measurement_schema in measurements_schema:
            measurement: dict[str, Any] = {
                "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            }

            # Add random sensor measurements as additionalProperties
            # Common IoT sensor types with realistic ranges
            sensor_data = self._generate_sensor_data(measurement_schema)
            measurement.update(sensor_data)

            measurements.append(measurement)

        return measurements

    def _generate_sensor_data(
        self, measurement_schema: dict[str, Any]
    ) -> dict[str, float]:
        """Generate realistic sensor measurement data."""
        sensor_data = {}

        id_field = measurement_schema.get("field")

        if id_field:
            sensor_data[id_field] = random.uniform(0, 100)

        return sensor_data
