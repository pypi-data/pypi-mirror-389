"""Firmware version management service."""

import logging
from typing import Optional

from simulator.auth.oauth2_client import OAuth2Client
from simulator.config.config_manager import ConfigManager
from simulator.utils.version_parser import parse_version_string


class FirmwareVersionApi:
    """Service for managing firmware versions."""

    def __init__(self, oauth_client: OAuth2Client, config_manager: ConfigManager):
        self.oauth_client = oauth_client
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)

        self.base_url = config_manager.app_config.iot_platform.base_url

    async def get_latest_version(self, device_type: str) -> Optional[str]:
        """Get the latest firmware version for a device type by scanning all versions."""
        try:
            self.oauth_client.ensure_valid_access_token()
            url = f"{self.base_url}/fw_versions"
            async with self.oauth_client.get_authenticated_session() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        versions = data.get("data", [])
                        # Filter by deviceType
                        matching_versions = [
                            v for v in versions if v.get("deviceType") == device_type
                        ]
                        if not matching_versions:
                            self.logger.warning(
                                f"No firmware versions found for device type: {device_type}"
                            )
                            return None
                        # Sort by dateUploaded descending
                        matching_versions.sort(
                            key=lambda v: v.get("dateUploaded", ""), reverse=True
                        )
                        latest = matching_versions[0]
                        version_id = latest.get("versionId")
                        if version_id:
                            return parse_version_string(version_id)
                        self.logger.warning(
                            f"No versionId found in latest version for deviceType: {device_type}"
                        )
                        return None
                    else:
                        self.logger.error(
                            f"Failed to get firmware versions: {response.status}"
                        )
                        return None
        except Exception as e:
            self.logger.error(f"Error fetching firmware version for {device_type}: {e}")
            return None
