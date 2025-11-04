#!/usr/bin/env python3
"""
Device Simulator - Main Entry Point

A comprehensive IoT device simulator that connects to Azure IoT Hub and IoT Platform servers.
"""

import argparse
import asyncio
import logging
import shutil
import sys
from pathlib import Path

from .commands.command_handler import CommandHandler
from .config.config_manager import ConfigManager
from .connectivity.iot_hub_client import IoTHubClient
from .device_setup.setup_coordinator import SetupCoordinator
from .telemetry import TelemetrySender
from .twin.twin_manager import TwinManager
from .utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main application entry point."""

    # Initialize variables to avoid unbound errors

    telemetry_sender = None
    iot_client = None
    tasks: list[asyncio.Task] = []

    try:
        # Initialize configuration manager (loads config including logging config)
        config_manager = ConfigManager()

        # Setup logging using config values
        log_level = (
            config_manager.app_config.logging.level
            if config_manager.app_config.logging.level
            else "INFO"
        )
        log_file = (
            config_manager.app_config.logging.file
            if config_manager.app_config.logging.file
            else "logs/simulator.log"
        )
        setup_logging(log_level, log_file)

        logger.info("Starting Device Simulator...")

        # Check if device is already configured
        if not config_manager.has_device_config():
            logger.info("No device configuration found. Starting setup...")
            device_setup = SetupCoordinator(config_manager)
            await device_setup.run_setup()
        else:
            logger.info("Device configuration found. Loading existing configuration...")
            config_manager.load_device_config()

        # Initialize components first
        command_handler = CommandHandler(config_manager)

        # Initialize IoT Hub client with command handler
        iot_client = IoTHubClient(config_manager, command_handler)
        await iot_client.connect()

        # Initialize components
        twin_manager = TwinManager(iot_client, config_manager)
        telemetry_sender = TelemetrySender(iot_client, config_manager)

        # Start services as background tasks
        tasks = []
        tasks.append(asyncio.create_task(twin_manager.start()))
        tasks.append(asyncio.create_task(telemetry_sender.start()))
        tasks.append(asyncio.create_task(command_handler.start()))

        logger.info("All services started. Press Ctrl+C to stop...")

        # Keep the application running until interrupted
        try:
            while True:
                # Check if any tasks have completed unexpectedly
                completed_tasks = [task for task in tasks if task.done()]
                if completed_tasks:
                    # Log what happened with each completed task
                    for task in completed_tasks:
                        try:
                            result = task.result()
                            logger.info(f"Service task completed normally: {result}")
                        except Exception as e:
                            logger.error(f"Service task failed with error: {e}")

                    logger.warning(
                        f"{len(completed_tasks)} service(s) completed. Continuing to run (use Ctrl+C to stop)..."
                    )

                    # Remove completed tasks and continue running
                    for task in completed_tasks:
                        tasks.remove(task)

                    # If all services stopped, we still continue running the main loop
                    # This allows the user to still use Ctrl+C to exit
                    if not tasks:
                        logger.warning(
                            "All services stopped, but main application continues. Press Ctrl+C to exit."
                        )

                # Sleep briefly to allow KeyboardInterrupt to be processed
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            logger.info("Application cancelled...")

        # If we reach here, Ctrl+C was pressed
        logger.info("Main loop exited, shutting down...")

        # Cancel all running tasks
        logger.info("Stopping services...")
        await wait_for_task_completions(tasks)

    except KeyboardInterrupt:
        logger.info("Received Ctrl+C (KeyboardInterrupt). Shutting down...")
        # Cancel all running tasks immediately
        logger.info("Stopping services...")
        await wait_for_task_completions(tasks)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
    finally:
        """Clean up application resources on shutdown."""
        logger.info("Shutting down services...")

        try:
            # Stop telemetry sender
            if telemetry_sender:
                await telemetry_sender.stop()

            # Disconnect from IoT Hub
            if iot_client:
                await iot_client.disconnect()

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        logger.info("Device Simulator stopped.")


async def wait_for_task_completions(tasks: list[asyncio.Task]) -> None:
    for task in tasks:
        if not task.done():
            task.cancel()

        # Wait for tasks to complete cancellation (with timeout)
    if tasks:
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout=5.0
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Some services didn't stop within timeout, forcing shutdown..."
            )


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path.cwd() / "config"


def get_config_file() -> Path:
    """Get the main configuration file path."""
    return get_config_dir() / "config.json"


def get_template_path() -> Path:
    """Get the path to the config template within the package."""
    # Get the directory where this module is located
    module_dir = Path(__file__).parent
    return module_dir / "config" / "templates" / "config.template.json"


def config_exists() -> bool:
    """Check if config.json already exists."""
    return get_config_file().exists()


def create_config_from_template() -> bool:
    """
    Create config directory and copy template to config.json.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        config_dir = get_config_dir()
        config_file = get_config_file()
        template_path = get_template_path()

        # Create config directory if it doesn't exist
        config_dir.mkdir(exist_ok=True)

        # Check if template exists
        if not template_path.exists():
            print(f"Error: Template file not found at {template_path}")
            return False

        # Copy template to config.json
        shutil.copy2(template_path, config_file)
        print("✅ Configuration initialized successfully!")
        print(f"📂 Created: {config_file}")
        print(
            f"📝 Please edit {config_file} with your specific settings before running the simulator."
        )

        return True

    except Exception as e:
        print(f"❌ Error creating configuration: {e}")
        return False


def init_config() -> None:
    """Initialize configuration from template."""
    print("🚀 IoT Simulator Configuration Initialization")
    print("=" * 50)

    if config_exists():
        config_file = get_config_file()
        print(f"✅ Configuration file already exists: {config_file}")

        # Ask if user wants to overwrite
        response = input("Do you want to overwrite it? (y/N): ").lower().strip()
        if response not in ["y", "yes"]:
            print("📋 Configuration initialization cancelled.")
            return

    # Create config from template
    if create_config_from_template():
        print("\n📋 Next steps:")
        print("1. Edit config/config.json with your specific settings")
        print("2. Run 'iot-simulator' to start the simulator")
    else:
        print("\n❌ Configuration initialization failed.")
        sys.exit(1)


def cli_main() -> None:
    """Synchronous entry point for console script."""
    parser = argparse.ArgumentParser(
        description="IoT Device Simulator - A comprehensive IoT device simulator for Azure IoT Hub and IoT Platform servers"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize configuration from template (creates config/config.json)",
    )

    args = parser.parse_args()

    # Handle --init flag
    if args.init:
        init_config()
        return

    # Check if configuration exists before starting
    config_file = Path.cwd() / "config" / "config.json"
    if not config_file.exists():
        print("❌ Configuration file not found!")
        print(f"   Expected: {config_file}")
        print()
        print("📋 To set up your configuration, run:")
        print("   iot-simulator --init")
        print()
        print("   This will create a config directory with a template configuration")
        print("   that you can customize for your environment.")
        return

    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
