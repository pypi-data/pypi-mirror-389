"""Platform API client for IoT Platform server communication."""

import logging
from typing import Any

from simulator.auth.oauth2_client import OAuth2Client


class DeviceCreationMetadataApi:
    """API client for retrieving metadata needed for device creation from the IoT Platform server."""

    def __init__(self, base_url: str, oauth_client: OAuth2Client):
        self.base_url = base_url
        self.oauth_client = oauth_client
        self.logger = logging.getLogger(__name__)

    async def get_managed_groups(self) -> list[dict[str, Any]]:
        """Get available managed groups using direct HTTP request"""
        try:
            async with self.oauth_client.get_authenticated_session() as session:
                url = f"{self.base_url}/groups"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Convert to flat list format expected by the UI
                        groups = []
                        if isinstance(data, dict) and "data" in data:
                            for item in data["data"]:
                                groups.append(
                                    {
                                        "id": item.get("id"),
                                        "name": item.get("name"),
                                        "path": item.get("path", ""),
                                        "type": item.get("type", ""),
                                        "managedDevices": item.get(
                                            "managedDevices", []
                                        ),
                                    }
                                )
                        elif isinstance(data, list):
                            for item in data:
                                groups.append(
                                    {
                                        "id": item.get("id"),
                                        "name": item.get("name"),
                                        "path": item.get("path", ""),
                                        "type": item.get("type", ""),
                                        "managedDevices": item.get(
                                            "managedDevices", []
                                        ),
                                    }
                                )
                        return groups
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            f"Groups API error - Status: {response.status}, Response: {error_text}"
                        )
                        raise Exception(
                            f"Groups API error: HTTP {response.status} - {error_text}"
                        )

                # If all endpoints failed
                raise Exception("No valid groups endpoint found")
        except Exception as e:
            self.logger.error(f"Failed to get managed groups: {e}")
            raise

    async def get_device_types(self) -> list[dict[str, Any]]:
        """Get available device types using direct HTTP request (fallback due to urllib3 compatibility issues)."""
        try:
            async with self.oauth_client.get_authenticated_session() as session:
                # Try different endpoint paths for device models
                url = f"{self.base_url}/device_models"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        device_types = []

                        if not isinstance(data, dict):
                            raise ValueError("Expected response to be a dict or list")
                        if "data" not in data:
                            raise ValueError("Expected 'data' key in response")
                        if "data" not in data["data"]:
                            raise ValueError(
                                "Expected data['data']['data'] to be an array"
                            )
                        items: list[Any] = data.get("data", {}).get("data", [])

                        for item in items:
                            # Extract device type from various possible field locations
                            model_data = item.get("model", {})
                            device_types.append(
                                {
                                    "id": item.get("id"),
                                    "deviceType": item.get("deviceType"),
                                    "name": item.get("deviceType"),
                                    "description": f"Device Type: {item.get('deviceType')}",
                                    "model": model_data,
                                }
                            )

                        return device_types
                    else:
                        error_text = await response.text()
                        self.logger.error(
                            f"Device types API error - Status: {response.status}, Response: {error_text}"
                        )
                        raise Exception(
                            f"Device types API error: HTTP {response.status} - {error_text}"
                        )

                # If all endpoints failed
                raise Exception("No valid device types endpoint found")
        except Exception as e:
            self.logger.error(f"Failed to get device types: {e}")
            raise
