"""Device selection and validation utilities."""

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table


class DeviceSelector:
    """Handles device and configuration selection with CLI interface."""

    def __init__(self, console: Console):
        self.console = console

    def select_from_list(
        self, title: str, items: list[dict], key_field: str, display_field: str
    ) -> dict:
        """Select an item from a list with CLI interface."""
        if not items:
            raise ValueError(f"No {title.lower()} available")

        if len(items) == 1:
            self.console.print(
                f"Only one {title.lower()} available. Selecting it by default."
            )
            return items[0]

        table = Table(title=title)
        table.add_column("Index", style="cyan")
        table.add_column("ID", style="green")
        table.add_column("Description", style="white")

        for i, item in enumerate(items):
            display_value = (
                display_field(item)
                if callable(display_field)
                else item.get(display_field, "")
            )
            table.add_row(str(i + 1), item[key_field], str(display_value))

        self.console.print(table)

        while True:
            try:
                choice = Prompt.ask(f"Select {title.lower()} (1-{len(items)})")
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return items[index]
                else:
                    self.console.print(
                        f"[red]Please enter a number between 1 and {len(items)}[/red]"
                    )
            except ValueError:
                self.console.print("[red]Please enter a valid number[/red]")

    def get_device_id(self) -> str:
        """Get device ID from user input."""
        return Prompt.ask("[bold]Enter Device ID[/bold]")

    def select_managed_group(self, groups: list[dict]) -> dict:
        """Select a managed group from available options."""
        return self.select_from_list("Select Managed Group", groups, "id", "name")

    def select_device_type(self, device_types: list[dict]) -> dict:
        """Select a device type from available options."""
        return self.select_from_list(
            "Select Device Type", device_types, "name", "description"
        )

    def select_existing_device(self, devices: list[dict]) -> dict:
        """Select an existing device from user's devices."""
        selected_device = self.select_from_list(
            "Select Device", devices, "deviceId", "deviceId"
        )

        # Return the full device data
        return next(d for d in devices if d["deviceId"] == selected_device)
