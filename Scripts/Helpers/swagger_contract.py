"""
Minimal Swagger 2.0 response validator used by the API contract tests.

Checks JSON types, enums and nested $ref definitions of a response against the schema
the backend publishes at /swagger/v0.1/swagger.json. Intentionally small: no external
dependency, and it only reports what is actually wrong.
"""
from __future__ import annotations

from typing import Any

_TYPE_CHECKS = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "boolean": lambda v: isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
}


class SwaggerContract:
    def __init__(self, spec: dict[str, Any]):
        self.spec = spec
        self.definitions: dict[str, Any] = spec.get("definitions", {})

    def has_operation(self, method: str, path: str) -> bool:
        """Path match is case-insensitive and treats every {param} segment as equal."""
        wanted = self._normalize(path)
        for spec_path, ops in self.spec.get("paths", {}).items():
            if self._normalize(spec_path) == wanted and method.lower() in ops:
                return True
        return False

    def response_schema(self, path: str, method: str = "get") -> dict[str, Any] | None:
        op = self.spec.get("paths", {}).get(path, {}).get(method.lower(), {})
        return op.get("responses", {}).get("200", {}).get("schema")

    def validate(self, value: Any, schema: dict[str, Any] | None, where: str = "$") -> list[str]:
        if not schema:
            return []
        if "$ref" in schema:
            name = schema["$ref"].rsplit("/", 1)[-1]
            return self.validate(value, self.definitions.get(name, {}), where)

        errors: list[str] = []
        if value is None:
            return errors  # .NET serialises unset references as null; schema has no nullability info

        expected = schema.get("type")
        if expected and expected in _TYPE_CHECKS and not _TYPE_CHECKS[expected](value):
            return [f"{where}: expected {expected}, got {type(value).__name__} ({value!r:.60})"]

        if "enum" in schema and value not in schema["enum"]:
            errors.append(f"{where}: {value!r} not in enum {schema['enum']}")

        if isinstance(value, dict):
            for key, prop_schema in schema.get("properties", {}).items():
                if key in value:
                    errors += self.validate(value[key], prop_schema, f"{where}.{key}")
            extra = schema.get("additionalProperties")
            if isinstance(extra, dict):
                for key, item in value.items():
                    if key not in schema.get("properties", {}):
                        errors += self.validate(item, extra, f"{where}.{key}")
        elif isinstance(value, list):
            for i, item in enumerate(value):
                errors += self.validate(item, schema.get("items"), f"{where}[{i}]")
        return errors

    @staticmethod
    def _normalize(path: str) -> str:
        parts = path.strip("/").split("?")[0].split("/")
        return "/".join("{}" if p.startswith("{") else p.lower() for p in parts)
