from datetime import datetime, timezone
from typing import Any

from simulator.config.config_manager import ConfigManager
from simulator.config.schemas import DeviceSchema
from simulator.utils.schema.schema_generator import SchemaDataGenerator

from .base_message_generator import BaseMessageGenerator


class AlertsGenerator(BaseMessageGenerator):
    """Generator for events messages that cycles through schema-defined events in order."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._alert_index = 0  # Track current alert position for sequential sending
        self._is_off = 0
        self.schema_generator = SchemaDataGenerator()
        self._active_alerts: list[str] = []  # Track currently active alerts

    def generate_message(self, device_schema: DeviceSchema) -> dict[str, Any]:
        """Generate an alert message compliant with schema."""
        events = device_schema.get_alerts()

        if not events:
            return {}

        # Get the next alert in sequence
        current_alert = events[self._alert_index]
        alert_id = current_alert.get("id")
        current_state = "off" if self._is_off else "on"

        # Update active alerts list only if alert_id is not None
        if alert_id is not None:
            if current_state == "on":
                if alert_id not in self._active_alerts:
                    self._active_alerts.append(alert_id)
            else:  # "off"
                if alert_id in self._active_alerts:
                    self._active_alerts.remove(alert_id)

        # Move to next alert for next call (with wraparound)
        self._alert_index = (self._alert_index + 1) % len(events)
        self._is_off = 1 - self._is_off

        return {
            "type": "events",
            "data": [
                {
                    "deviceId": self.config_manager.device_config.device_id,
                    "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "eventId": alert_id,
                    "alertState": current_state,
                    "payload": self._generate_payload(current_alert.get("payload", {})),
                }
            ],
        }

    def _generate_payload(self, payload_schema: dict[str, Any]) -> Any:
        """Generate payload data based on the alert's payload schema."""
        if not payload_schema:
            return {}

        return self.schema_generator.create_schema_data(payload_schema)

    def get_active_alerts(self) -> list[str]:
        """Get list of currently active alert IDs."""
        return self._active_alerts.copy()
