"""Telemetry sender for managing and sending telemetry messages."""

import asyncio
import json
import logging

from simulator.config.config_manager import ConfigManager
from simulator.config.schemas import DeviceSchema
from simulator.connectivity.iot_hub_client import IoTHubClient

from .telemetry_generator import TelemetryGenerator


class TelemetrySender:
    """Manages telemetry generation and sending."""

    def __init__(
        self,
        iot_client: IoTHubClient,
        config_manager: ConfigManager,
    ):
        self.iot_client = iot_client
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

        # Initialize generator
        self.generator = TelemetryGenerator(config_manager)

        # Task management
        self.running = False
        self.tasks: list[asyncio.Task] = []

    def _load_schema(self) -> DeviceSchema:
        """Load the telemetry schema."""
        try:
            # Load device schema
            device_type = self.config_manager.device_config.device_type
            return self.config_manager.load_schema(device_type)
        except Exception as e:
            self.logger.error(f"Error loading schema: {e}")
            raise

    async def start(self) -> None:
        """Start telemetry sending."""
        self.logger.info("Starting telemetry sender...")

        # Load schema
        schema = self._load_schema()

        self.running = True

        # Start telemetry tasks for each enabled message type
        all_message_types = ["measurement", "sw_logs", "state", "events"]
        enabled_message_types = [
            mt for mt in all_message_types if self._is_message_type_enabled(mt)
        ]

        self.logger.info(f"Enabled message types: {enabled_message_types}")

        for message_type in enabled_message_types:
            task = asyncio.create_task(self._telemetry_loop(message_type, schema))
            self.tasks.append(task)

        self.logger.info("Telemetry sender started successfully")

    async def stop(self) -> None:
        """Stop telemetry sending."""
        self.logger.info("Stopping telemetry sender...")
        self.running = False

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()

        self.logger.info("Telemetry sender stopped")

    async def _telemetry_loop(
        self, message_type: str, device_schema: DeviceSchema
    ) -> None:
        """Telemetry sending loop for a specific message type."""
        self.logger.info(f"Starting {message_type} telemetry loop")

        while self.running:
            try:
                # Get interval from configuration
                interval = self._get_telemetry_interval(message_type)

                # Generate and send all messages of this type
                messages = self.generator.generate_telemetry(
                    message_type, device_schema
                )

                for message in messages:
                    await self.iot_client.send_message(message, message_type)
                    self.logger.info(
                        f"[D2C] Sent {message_type}: {json.dumps(message, indent=2)}"
                    )

                # Wait for next interval
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in {message_type} telemetry loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

    def _get_telemetry_interval(self, message_type: str) -> int:
        return self.config_manager.app_config.messaging.intervals.get(message_type, 60)

    def _is_message_type_enabled(self, message_type: str) -> bool:
        """Check if a message type is enabled in configuration."""
        return self.config_manager.app_config.messaging.enabled.get(message_type, True)
