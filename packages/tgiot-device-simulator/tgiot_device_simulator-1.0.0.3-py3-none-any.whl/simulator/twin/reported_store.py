import json
import os
from typing import Any


class TwinReportedStore:
    def __init__(self, device_id: str):
        self.device_id = device_id
        self.path = os.path.join(
            os.getcwd(), "twin_schemas", f"reported_{device_id}.json"
        )

    def save(self, reported_data: dict[str, Any]) -> None:
        dir_path = os.path.dirname(self.path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(reported_data, f, indent=2)

    def load(self) -> dict[str, Any]:
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                return json.load(f) or {}
        return {}
