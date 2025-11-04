"""Type mapping utilities for schema data generation."""

import random
from typing import Any

from faker import Faker


class SchemaValueGenerator:
    """Maps schema types to appropriate Faker methods for realistic data generation."""

    def __init__(self, fake: Faker):
        self.fake = fake

    def generate_value_by_schema(self, schema: dict[str, Any]) -> Any:
        """Generate realistic values based on field name and schema type, ensuring type safety."""
        schema = schema or {}

        if "default" in schema:
            return schema["default"]

        return self._generate_by_type(schema)

    def _generate_by_type(self, schema: dict[str, Any]) -> Any:
        """Generate data based on schema type definition."""
        data_type = schema.get("type", "").lower()
        if data_type in ["integer", "int"]:
            return self._generate_integer(schema)
        elif data_type in ["number", "float"]:
            return self._generate_number(schema)
        elif data_type in ["boolean", "bool"]:
            return bool(self.fake.boolean())
        elif data_type in ["string", "str"]:
            return self._generate_string(schema)
        else:
            return None

    def _generate_integer(self, schema: dict[str, Any]) -> int:
        """Generate integer value."""
        min_val = schema.get("minimum", schema.get("min", 0))
        max_val = schema.get("maximum", schema.get("max", 100))
        return self.fake.random_int(min_val, max_val)

    def _generate_number(self, schema: dict[str, Any]) -> float:
        """Generate float value."""
        min_val = schema.get("minimum", schema.get("min", 0.0))
        max_val = schema.get("maximum", schema.get("max", 100.0))
        precision = 3 if min_val == 0.0 and max_val == 1.0 else 2
        return round(random.uniform(min_val, max_val), precision)

    def _generate_string(self, schema: dict[str, Any]) -> str:
        """Generate string value."""
        if "enum" in schema:
            return str(random.choice(schema["enum"]))
        elif "choices" in schema:
            return str(random.choice(schema["choices"]))

        format_type = schema.get("format", "").lower()
        if format_type == "email":
            return str(self.fake.email())
        elif format_type in ("uri", "url"):
            return str(self.fake.url())
        elif format_type == "uuid":
            return str(self.fake.uuid4())
        elif format_type == "datetime":
            return self.fake.date_time_between().isoformat()

        max_length = schema.get("maxLength", 20)
        if max_length <= 10:
            return self.fake.word()[:max_length]
        elif max_length <= 50:
            return self.fake.text(max_nb_chars=max_length).replace("\n", " ").strip()
        else:
            return ""
