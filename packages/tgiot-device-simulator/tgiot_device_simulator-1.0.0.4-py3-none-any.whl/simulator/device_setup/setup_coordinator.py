"""Main coordinator for device setup orchestration."""

import logging

from rich.console import Console
from rich.panel import Panel

from simulator.api import FirmwareVersionApi
from simulator.api.device_creation_metadata_api import DeviceCreationMetadataApi
from simulator.auth.oauth2_client import OAuth2Client
from simulator.auth.oauth_flow import OAuthFlow
from simulator.config.config_manager import ConfigManager
from simulator.provisioning.device_provisioner import DeviceProvisioner

from .configuration_ui import ConfigurationUI
from .device_selector import DeviceSelector


class SetupCoordinator:
    """Coordinates the complete device setup process."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.console = Console()

        # Initialize OAuth2 client
        oauth2_config = config_manager.app_config.iot_platform.oauth2
        self.oauth_client = OAuth2Client(
            client_id=oauth2_config.client_id,
            authorization_endpoint=oauth2_config.authorization_endpoint,
            token_endpoint=oauth2_config.token_endpoint,
        )

        # Initialize platform API
        self.device_metadata_api = DeviceCreationMetadataApi(
            base_url=config_manager.app_config.iot_platform.base_url,
            oauth_client=self.oauth_client,
        )

        # Initialize Device Provisioner
        self.device_provisioner = DeviceProvisioner(
            config_manager=config_manager, oauth_client=self.oauth_client
        )

        # Initialize Firmware Version API
        self.firmware_version_api = FirmwareVersionApi(
            oauth_client=self.oauth_client, config_manager=config_manager
        )

        # Initialize UI components
        self.oauth_flow = OAuthFlow(self.oauth_client, self.console)
        self.device_selector = DeviceSelector(self.console)
        self.configuration_ui = ConfigurationUI(
            config_manager=config_manager,
            device_metadata_api=self.device_metadata_api,
            device_provisioner=self.device_provisioner,
            device_selector=self.device_selector,
            firmware_version_api=self.firmware_version_api,
            console=self.console,
        )

    async def run_setup(self) -> None:
        """Run the complete device setup process."""
        self._show_welcome_message()

        try:
            # Step 1: Authentication
            await self.oauth_flow.authenticate()

            # Step 2: Configure new device
            await self.configuration_ui.setup_new_device()

            self._show_success_message()

        except Exception as e:
            self.logger.error(f"Setup failed: {e}")
            self.console.print(f"[bold red]❌ Setup failed: {e}[/bold red]")
            raise

    def _show_welcome_message(self) -> None:
        """Display welcome message."""
        self.console.print(
            Panel.fit(
                "[bold blue]Device Simulator Setup[/bold blue]\n"
                "Welcome to the Device Simulator configuration wizard.",
                title="🚀 Setup Wizard",
            )
        )

    def _show_success_message(self) -> None:
        """Display success message."""
        self.console.print(
            Panel.fit(
                "[bold green]✅ Setup completed successfully![/bold green]\n"
                "Your device is now ready to start simulation.",
                title="🎉 Success",
            )
        )
