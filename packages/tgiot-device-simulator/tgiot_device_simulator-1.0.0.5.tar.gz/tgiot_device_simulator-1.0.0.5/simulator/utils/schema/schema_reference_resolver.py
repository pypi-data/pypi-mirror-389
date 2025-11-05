"""Schema validation and resolution utilities."""

import logging
from typing import Any, Union

# Type alias for schema values that can be recursively processed
SchemaValue = Union[dict[str, Any], list[Any], Any]


class SchemaReferenceResolver:
    """Handles only schema reference resolution."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def resolve_all_refs(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Centralized method to resolve all $ref references in the schema."""
        defs = schema.get("$defs", {})
        result = self._resolve_refs_recursive(schema, defs)
        # Since we start with a dict, we should get a dict back
        assert isinstance(result, dict), "Expected dict result from dict input"
        return result

    def _resolve_refs_recursive(
        self, schema: SchemaValue, defs: dict[str, Any]
    ) -> SchemaValue:
        """Recursively resolve all $ref references in a schema structure.

        Args:
            schema: Can be a dict, list, or any other type.
                   - dict: Returns a dict with resolved refs
                   - List: Returns a list with resolved refs in each item
                   - Other: Returns the value unchanged
            defs: Schema definitions for resolving $ref references

        Returns:
            The same type as input schema, with all $ref references resolved.
        """
        if isinstance(schema, dict):
            # Handle direct $ref
            if "$ref" in schema:
                return self.resolve_ref(schema, defs)

            # Recursively resolve refs in nested structures
            resolved = {}
            for key, value in schema.items():
                resolved[key] = self._resolve_refs_recursive(value, defs)
            return resolved
        elif isinstance(schema, list):
            return [self._resolve_refs_recursive(item, defs) for item in schema]
        else:
            return schema

    def resolve_ref(
        self, schema: dict[str, Any], defs: dict[str, Any]
    ) -> dict[str, Any]:
        """Resolve $ref references in schema."""
        if isinstance(schema, dict) and "$ref" in schema:
            ref_path = schema["$ref"]
            if ref_path.startswith("#/$defs/"):
                def_name = ref_path.replace("#/$defs/", "")
                if def_name in defs:
                    resolved = defs[def_name].copy()
                    # Recursively resolve any nested refs
                    return self._resolve_nested_refs(resolved, defs)
        return schema

    def _resolve_nested_refs(
        self, schema: dict[str, Any], defs: dict[str, Any]
    ) -> dict[str, Any]:
        """Recursively resolve nested $ref references."""
        result = {}
        for key, value in schema.items():
            if key == "$ref" and isinstance(value, str):
                # This is a reference, resolve it
                if value.startswith("#/$defs/"):
                    def_name = value.replace("#/$defs/", "")
                    if def_name in defs:
                        # Replace the $ref with the actual definition
                        resolved = defs[def_name].copy()
                        result.update(self._resolve_nested_refs(resolved, defs))
                        continue

            if isinstance(value, dict):
                result[key] = self._resolve_nested_refs(value, defs)
            elif isinstance(value, list):
                result[key] = [
                    self._resolve_nested_refs(item, defs)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
