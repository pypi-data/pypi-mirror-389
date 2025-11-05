"""Message generators for different telemetry message types."""

import random
from datetime import datetime, timezone
from typing import Any

from simulator.config.config_manager import ConfigManager
from simulator.config.schemas import DeviceSchema
from simulator.telemetry.message_generators.alerts_generator import AlertsGenerator
from simulator.utils.schema.schema_generator import SchemaDataGenerator

from .base_message_generator import BaseMessageGenerator


class D2CStatusGenerator(BaseMessageGenerator):
    """Generator for d2c-status messages."""

    def __init__(
        self, config_manager: ConfigManager, alerts_generator: AlertsGenerator
    ):
        self.config_manager = config_manager
        self.schema_generator = SchemaDataGenerator()
        self.alerts_generator = (
            alerts_generator  # Reference to AlertsGenerator for active alerts
        )

    def generate_message(self, device_schema: DeviceSchema) -> dict[str, Any]:
        """Generate a d2c-status message compliant with schema."""
        return {
            "type": "state",
            "data": [
                {
                    "deviceId": self.config_manager.device_config.device_id,
                    "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "connection": random.choice(["ONLINE", "OFFLINE"]),
                    "alerts": self._generate_alerts(),
                    "rssi": self._generate_rssi(),
                    "networkInfo": self._generate_network_info(),
                    "batteryLevel": round(random.uniform(15.0, 95.0), 1),
                    "additionalData": self._generate_additional_data(device_schema),
                }
            ],
        }

    def _generate_alerts(self) -> list[str]:
        """Get currently active alerts from AlertsGenerator."""
        if self.alerts_generator:
            return self.alerts_generator.get_active_alerts()

        # Fallback to empty list if no AlertsGenerator is available
        return []

    def _generate_rssi(self) -> dict[str, Any]:
        """Generate RSSI information according to schema."""
        connection_types = ["WIFI", "RF", "2G", "4G"]

        return {
            "connection": random.choice(connection_types),
            "value": random.randint(-120, -50),
        }

    def _generate_additional_data(self, schema: DeviceSchema) -> Any:
        """Generate additional data according to schema."""
        try:
            item_schema = schema.get_status_additional_data()
            return self.schema_generator.create_schema_data(item_schema)
        except Exception as e:
            self.logger.error(f"Failed to generate default status data: {e}")
            return {}

    def _generate_network_info(self) -> dict[str, Any]:
        """Generate realistic cellular network information."""
        networks = ["NONE", "GSM", "NBIOT", "LTE_M", "ETHERNET", "WIFI", "5G", "HSPA"]

        return {
            "network": random.choice(networks),
            "ipv4": f"{random.randint(10, 192)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 254)}",
            "iccid": f"{''.join([str(random.randint(0, 9)) for _ in range(19)])}",
            "imei": f"{''.join([str(random.randint(0, 9)) for _ in range(15)])}",
            "rssi": random.randint(-120, -50),
            "rsrp": random.randint(-140, -44),
            "rsrq": random.randint(-20, -3),
            "sinr": random.randint(-20, 30),
        }
