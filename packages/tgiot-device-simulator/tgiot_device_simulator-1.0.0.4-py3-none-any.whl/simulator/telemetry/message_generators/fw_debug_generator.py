"""Firmware debug message generator for telemetry messages."""

import random
from datetime import datetime, timezone
from typing import Any

from simulator.config.config_manager import ConfigManager
from simulator.config.schemas import DeviceSchema

from .base_message_generator import BaseMessageGenerator


class FwDebugGenerator(BaseMessageGenerator):
    """Generator for sw_logs messages with firmware debug logs."""

    def __init__(self, config_manager: ConfigManager) -> None:
        self.config_manager = config_manager

    def generate_message(self, _: DeviceSchema) -> dict[str, Any]:
        """Generate a sw_logs message compliant with schema."""
        return {
            "type": "sw_logs",
            "data": [
                {
                    "deviceId": self.config_manager.device_config.device_id,
                    "logs": self._generate_debug_logs(),
                }
            ],
        }

    def _generate_debug_logs(self) -> list[dict[str, Any]]:
        """Generate realistic firmware debug log entries."""
        # Number of log entries to generate (1-5)
        num_logs = random.randint(1, 5)

        debug_messages = [
            "Boot complete",
            "WiFi connected",
            "Sensor init OK",
            "Memory check pass",
            "Config loaded",
            "Timer started",
            "Data sync OK",
            "Signal strong",
            "Power stable",
            "Buffer cleared",
            "Heartbeat sent",
            "Task scheduled",
            "Error handled",
            "Reset complete",
            "Backup created",
            "Update applied",
            "Watchdog reset",
            "Cache flushed",
            "Module loaded",
            "Thread started",
        ]

        logs = []
        base_time = datetime.now(timezone.utc)

        for i in range(num_logs):
            # Generate timestamps going backwards in time (seconds ago)
            import datetime as dt

            seconds_ago = random.randint(i * 10, (i + 1) * 30)
            log_time = base_time - dt.timedelta(seconds=seconds_ago)

            # Select random debug message and ensure it's max 20 chars
            message = random.choice(debug_messages)
            if len(message) > 20:
                message = message[:20]

            logs.append(
                {"ts": log_time.isoformat().replace("+00:00", "Z"), "value": message}
            )

        # Sort logs by timestamp (most recent first)
        logs.sort(key=lambda x: x["ts"], reverse=True)

        return logs
