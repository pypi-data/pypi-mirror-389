"""Command handling module for C2D messages."""

import logging
from typing import Any, Optional

from simulator.config.config_manager import ConfigManager
from simulator.config.schemas import DeviceModelSpecSupportedMethods, DeviceSchema


class CommandHandler:
    """Handles commands (C2D messages) from IoT Platform."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.schema: DeviceSchema | None = None

    async def start(self) -> None:
        """Start command handler."""
        self.logger.info("Starting command handler...")
        try:
            device_type = self.config_manager.device_config.device_type
            self.schema = self.config_manager.load_schema(device_type)
            self.logger.info("Command handler started successfully")
        except Exception as e:
            self.logger.error(f"Failed to load schema for command validation: {e}")
            raise

    async def handle_command(self, command_id: str, payload: dict[str, Any]) -> None:
        """Handle incoming command and send D2C response (schema-aware)."""
        self.logger.info(
            f"[C2D] Received command: {command_id} with payload: {payload}"
        )

        try:
            method = self._find_supported_method(command_id)
            if not method:
                self.logger.warning(
                    f"Command '{command_id}' not found in supportedMethods or is not C2D command."
                )
                return

            # Validate payload against payloadSchema if present
            if method.payload_schema:
                if not self._validate_payload_against_schema(
                    payload, method.payload_schema
                ):
                    self.logger.error(
                        f"Payload validation failed for command '{command_id}'"
                    )
                    await self._send_schema_response(
                        command_id, status="RESULT_INTERNAL_ERROR", payload={}
                    )
                    return

            # TODO: generate response payload based on command
            response_payload: dict[str, Any] = {}

            await self._send_schema_response(
                command_id, status="RESULT_SUCCESS", payload=response_payload
            )

        except Exception as e:
            self.logger.error(f"Error executing command '{command_id}': {e}")
            await self._send_schema_response(
                command_id, status="RESULT_INTERNAL_ERROR", payload={}
            )

    def _find_supported_method(
        self, command_id: str
    ) -> Optional[DeviceModelSpecSupportedMethods]:
        if not self.schema:
            return None
        for method in self.schema.get_supported_methods():
            if method.id == command_id and not method.multi_device_support:
                return method
        return None

    def _validate_payload_against_schema(self, payload: dict, schema: dict) -> bool:
        # Only check required fields for now
        required = schema.get("required", [])
        for field in required:
            if field not in payload:
                self.logger.error(f"Required field '{field}' missing in payload.")
                return False
        return True

    async def _send_schema_response(
        self, command_id: str, status: str, payload: dict
    ) -> None:
        """Log command response (no actual sending for now)."""
        self.logger.info(
            f"Command '{command_id}' completed with status: {status}, payload: {payload}"
        )
        # TODO: Implement actual response sending if needed in the future
