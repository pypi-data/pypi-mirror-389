"""IoT Hub client for device connectivity."""

import json
import logging
import os
import uuid
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any, Optional

from azure.iot.device import X509, Message
from azure.iot.device.aio import IoTHubDeviceClient

from simulator.commands.command_handler import CommandHandler
from simulator.config.config_manager import ConfigManager


class IoTHubClient:
    """Azure IoT Hub client wrapper."""

    def __init__(self, config_manager: ConfigManager, command_handler: CommandHandler):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.client: Optional[IoTHubDeviceClient] = None
        self.is_connected = False
        self.command_handler_instance: CommandHandler = command_handler

        # Callback handlers
        self.twin_patch_handler: Optional[
            Callable[[dict[str, Any]], Awaitable[None]]
        ] = None

    async def connect(self) -> None:
        """Connect to IoT Hub using X.509 certificate authentication."""
        if not self.config_manager.device_config:
            raise ValueError("Device configuration not loaded")

        device_config = self.config_manager.device_config
        device_id = device_config.device_id

        try:
            # Use X.509 certificate authentication
            if await self._try_x509_auth(device_id):
                self.logger.info("Connected using X.509 certificate authentication")
                return

            # If we get here, X.509 authentication failed
            raise ValueError(
                f"X.509 certificate authentication failed for device {device_id}. "
                f"Please ensure certificates are available in certificates/{device_id}/"
            )

        except Exception as e:
            self.logger.error(f"Failed to connect to IoT Hub: {e}")
            raise

    async def _try_x509_auth(self, device_id: str) -> bool:
        """Try to authenticate using X.509 certificates."""
        try:
            # Look for certificate files
            cert_dir = os.path.join("certificates", device_id)
            cert_file = os.path.join(cert_dir, f"{device_id}.cert.pem")
            key_file = os.path.join(cert_dir, f"{device_id}.private.pem")

            if not (os.path.exists(cert_file) and os.path.exists(key_file)):
                return False

            # Create and connect X.509 client
            x509 = X509(cert_file, key_file)
            hostname = self.config_manager.app_config.iot_hub.host_name

            self.client = IoTHubDeviceClient.create_from_x509_certificate(
                x509=x509, hostname=hostname, device_id=device_id
            )

            await self.client.connect()
            await self._setup_handlers()
            return True

        except Exception as e:
            self.logger.debug(f"X.509 authentication failed: {e}")
            return False

    async def _setup_handlers(self) -> None:
        """Setup event handlers."""
        if self.client is None:
            raise ValueError("IoT Hub client is not initialized")

        self.client.on_twin_desired_properties_patch_received = (
            self._on_twin_patch_received
        )
        self.client.on_message_received = self._on_method_received
        self.is_connected = True
        self.logger.info(
            f"Connected to IoT Hub for device: {self.config_manager.device_config.device_id}"
        )

    async def disconnect(self) -> None:
        """Disconnect from IoT Hub."""
        if self.client and self.is_connected:
            try:
                await self.client.disconnect()
                self.is_connected = False
                self.logger.info("Disconnected from IoT Hub")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}")

    async def send_message(self, message_content: dict, message_type: str) -> None:
        """Send a message to IoT Hub."""
        if not self.client or not self.is_connected:
            raise ConnectionError("Not connected to IoT Hub")

        try:
            message = Message(json.dumps(message_content))
            message.message_id = uuid.uuid4()
            message.content_encoding = "utf-8"
            message.content_type = "application/json;charset=utf-8"

            await self.client.send_message(message)
            self.logger.debug(f"Sent {message_type} message: {message_content}")

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise

    async def get_twin(self) -> dict:
        """Get the current device twin."""
        if not self.client or not self.is_connected:
            raise ConnectionError("Not connected to IoT Hub")

        try:
            twin: dict = await self.client.get_twin()
            return twin
        except Exception as e:
            self.logger.error(f"Failed to get twin: {e}")
            raise

    async def patch_twin_reported_properties(self, reported_properties: dict) -> None:
        """Update reported properties in device twin."""
        if not self.client or not self.is_connected:
            raise ConnectionError("Not connected to IoT Hub")

        try:
            await self.client.patch_twin_reported_properties(reported_properties)
            self.logger.debug(f"Updated reported properties: {reported_properties}")
        except Exception as e:
            self.logger.error(f"Failed to update reported properties: {e}")
            raise

    def set_twin_patch_handler(
        self, handler: Callable[[dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Set the twin desired properties patch handler."""
        self.twin_patch_handler = handler

    async def _on_twin_patch_received(self, patch: dict) -> None:
        """Handle twin desired properties patch."""
        self.logger.debug(f"Received twin patch: {patch}")

        if self.twin_patch_handler:
            try:
                await self.twin_patch_handler(patch)
            except Exception as e:
                self.logger.error(f"Error in twin patch handler: {e}")

    async def _on_method_received(self, method_request: Message) -> None:
        try:
            message_str = (
                method_request.data.decode("utf-8")
                if isinstance(method_request.data, (bytes, bytearray))
                else method_request.data
            )
            message = json.loads(message_str)
            method_id = message.get("commandId")
            method_payload = message.get("payload")
            expiry_time = method_request.expiry_time_utc
            self.logger.info(
                f"Received method request: {method_id} with payload: {method_payload} expiring at {expiry_time}"
            )

            # Parse expiry_time if it's a string
            expiry_dt = None
            if expiry_time:
                if isinstance(expiry_time, str):
                    try:
                        expiry_dt = datetime.fromisoformat(
                            expiry_time.replace("Z", "+00:00")
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Could not parse expiry_time: {expiry_time} ({e})"
                        )
                else:
                    expiry_dt = expiry_time
            if expiry_dt and expiry_dt < datetime.now(timezone.utc):
                self.logger.warning(f"Method request {method_id} has expired")
                return
            await self.command_handler_instance.handle_command(
                method_id, method_payload
            )
        except Exception as e:
            self.logger.error(f"Error handling method request: {e}")
