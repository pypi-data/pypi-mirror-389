"""Device provisioning module using API instead of direct IoT Hub connection."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import aiohttp

from simulator.auth.oauth2_client import OAuth2Client
from simulator.config.config_manager import ConfigManager


@dataclass
class ProvisioningResult:
    """Result of device provisioning operation."""

    device_id: str
    private_key: str
    public_key: str
    private_key_path: str
    public_key_path: str


@dataclass
class ProvisionData:
    """Structured data from provisioning API response."""

    private_key: str
    public_key: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProvisionData":
        """Create ProvisionData from API response dictionary."""
        return cls(private_key=data["privateKey"], public_key=data["publicKey"])


class DeviceProvisioner:
    """Handles device provisioning using the provisioner API."""

    def __init__(self, config_manager: ConfigManager, oauth_client: OAuth2Client):
        self.config_manager = config_manager
        self.oauth_client = oauth_client
        self.logger = logging.getLogger(__name__)

        # URLs from config
        self.provisioner_url = config_manager.app_config.provisioner.base_url

        # Certificate storage
        self.certs_dir = Path("certificates")
        self.certs_dir.mkdir(exist_ok=True)

    async def provision_device(
        self,
        device_id: str,
        device_type: str,
        group_id: str,
        override_if_exists: bool = True,
    ) -> ProvisioningResult:
        """
        Provision a device using the provisioner API.

        Args:
            device_id: Unique identifier for the device
            device_type: Type of device being provisioned
            group_id: ID of the managed group to add the device to
            override_if_exists: Whether to override if device already exists

        Returns:
            ProvisioningResult with certificate paths and keys

        Raises:
            Exception: If provisioning fails
        """
        self.logger.info(f"Provisioning device: {device_id}")

        # Ensure we have valid authentication
        if not self.oauth_client.ensure_valid_access_token():
            raise Exception("No valid authentication token available for provisioning")

        # Step 1: Provision device certificates
        provision_data = await self._provision_certificates(
            device_id, override_if_exists
        )

        # Step 2: Store certificates to files
        cert_paths = await self._store_certificates(device_id, provision_data)

        # Step 3: Add device to platform
        await self._add_device_to_platform(device_id, device_type, group_id)

        return ProvisioningResult(
            device_id=device_id,
            private_key=provision_data.private_key,
            public_key=provision_data.public_key,
            private_key_path=cert_paths["private_key_path"],
            public_key_path=cert_paths["public_key_path"],
        )

    async def _provision_certificates(
        self, device_id: str, override_if_exists: bool
    ) -> ProvisionData:
        """Provision device certificates from the provisioner API."""
        url = f"{self.provisioner_url}/gateways"

        headers = self._get_headers()

        data = {
            "id": device_id,
            "overrideIfExists": override_if_exists,
            "isEnabled": True,
        }

        self.logger.info(f"Requesting certificates from: {url}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()

                    # Validate response has required keys
                    if "privateKey" not in result or "publicKey" not in result:
                        raise Exception("Provisioning response missing required keys")

                    if not result["privateKey"] or not result["publicKey"]:
                        raise Exception("Provisioning returned empty keys")

                    self.logger.info("Device certificates provisioned successfully")
                    return ProvisionData.from_dict(result)
                else:
                    error_text = await response.text()
                    raise Exception(
                        f"Certificate provisioning failed: {response.status} - {error_text}"
                    )

    async def _store_certificates(
        self, device_id: str, provision_data: ProvisionData
    ) -> dict[str, str]:
        """Store certificates to filesystem."""
        device_dir = self.certs_dir / device_id
        device_dir.mkdir(exist_ok=True)

        private_key_path = device_dir / f"{device_id}.private.pem"
        public_key_path = device_dir / f"{device_id}.cert.pem"

        # Clean and store private key
        private_key_path.write_text(provision_data.private_key.replace("\\n", "\n"))

        # Clean and store public key/certificate
        public_key_path.write_text(provision_data.public_key.replace("\\n", "\n"))

        self.logger.info("Certificates stored")

        return {
            "private_key_path": str(private_key_path),
            "public_key_path": str(public_key_path),
        }

    async def _add_device_to_platform(
        self, device_id: str, device_type: str, group_id: str
    ) -> None:
        """Add the device to the platform."""
        url = f"{self.config_manager.app_config.iot_platform.base_url}/devices/{device_id}"

        headers = self._get_headers()

        data = {
            "managedGroup": group_id,
            "metadata": {},
            "gateway": {"id": device_id},
            "type": device_type,
        }

        self.logger.info(f"Adding device to platform: {url}")

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status in [200, 201]:
                    self.logger.info("Device added to platform successfully")
                else:
                    error_text = await response.text()
                    self.logger.warning(
                        f"Failed to add device to platform: {response.status} - {error_text}"
                    )
                    # Don't raise exception here as certificates are already provisioned

    def get_certificate_paths(self, device_id: str) -> dict[str, str]:
        """Get certificate file paths for a device."""
        device_dir = self.certs_dir / device_id

        return {
            "private_key_path": str(device_dir / f"{device_id}.private.pem"),
            "public_key_path": str(device_dir / f"{device_id}.cert.pem"),
            "device_dir": str(device_dir),
        }

    def _get_headers(self) -> dict[str, str]:
        """Get standard headers for API requests."""
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.oauth_client.access_token}",
        }

    def has_certificates(self, device_id: str) -> bool:
        """Check if certificates exist for a device."""
        paths = self.get_certificate_paths(device_id)
        private_key_exists = Path(paths["private_key_path"]).exists()
        public_key_exists = Path(paths["public_key_path"]).exists()

        return private_key_exists and public_key_exists
