"""Enhanced schema-based data generator using Faker."""

import logging
from typing import Any

from faker import Faker

from .schema_reference_resolver import SchemaReferenceResolver
from .schema_value_generator import SchemaValueGenerator


class SchemaDataGenerator:
    """Generate realistic data based on JSON schema using Faker."""

    def __init__(self, locale: str = "en_US"):
        self.fake = Faker(locale)
        self.logger = logging.getLogger(__name__)
        self.schema_value_generator = SchemaValueGenerator(self.fake)
        self.reference_resolver = SchemaReferenceResolver()

    def create_schema_data(self, schema: dict[str, Any]) -> Any:
        """Generate data for the full schema, resolving references as needed."""
        try:
            if not schema:
                self.logger.debug("Empty schema provided for data generation.")
                return {}

            resolved_schema = self.reference_resolver.resolve_all_refs(schema)
            return self._generate_from_schema("root", resolved_schema)
        except Exception as e:
            self.logger.error(f"Failed to generate complete schema data: {e}")
            return {}

    def _generate_object(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Generate object from resolved schema (no $ref resolution needed)."""
        obj = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for prop_key, prop_schema in properties.items():
            # Always include required properties, randomly include others
            if prop_key in required or self.fake.boolean(chance_of_getting_true=80):
                obj[prop_key] = self._generate_from_schema(prop_key, prop_schema)
        return obj

    def _generate_array(self, key: str, schema: dict[str, Any]) -> list:
        """Generate array value with proper item schema handling."""
        min_items = schema.get("minItems", 1)
        max_items = schema.get("maxItems", 3)
        array_length = self.fake.random_int(min_items, max_items)
        items_schema = schema.get("items", {})
        return [
            self._generate_from_schema(f"{key}_item_{i}", items_schema)
            for i in range(array_length)
        ]

    def _generate_from_schema(self, key: str, schema: dict[str, Any]) -> Any:
        """Generate data from a fully resolved schema (no more $ref resolution needed)."""
        # Check for explicit default value
        if "default" in schema:
            return schema["default"]

        # Generate value using the appropriate method based on type
        data_type = schema.get("type", "").lower()
        if data_type in ["array", "list"]:
            return self._generate_array(key, schema)
        elif data_type in ["object", "dict"]:
            return self._generate_object(schema)
        return self.schema_value_generator.generate_value_by_schema(schema)
