from __future__ import annotations

from typing import Any


class TypeValidationError(ValueError):
    pass


def coerce_typed_document(document: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    return _coerce_object(document, schema, "$")


def _coerce_object(value: Any, schema: dict[str, Any], path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeValidationError(f"{path}: expected object")
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))
    result: dict[str, Any] = {}
    for key, spec in sorted(properties.items()):
        next_path = f"{path}.{key}"
        if key not in value:
            if key in required:
                raise TypeValidationError(f"{next_path}: required field is missing")
            continue
        result[key] = _coerce_value(value[key], spec, next_path)
    if schema.get("additionalProperties") is False:
        extras = sorted(set(value.keys()) - set(properties.keys()))
        if extras:
            raise TypeValidationError(f"{path}: unexpected fields {extras}")
    return result


def _coerce_value(value: Any, schema: dict[str, Any], path: str) -> Any:
    schema_type = schema.get("type")
    if schema_type == "string":
        if type(value) is not str:
            raise TypeValidationError(f"{path}: expected string")
        return value
    if schema_type == "integer":
        if type(value) is not int:
            raise TypeValidationError(f"{path}: expected integer")
        return value
    if schema_type == "number":
        if type(value) not in (int, float):
            raise TypeValidationError(f"{path}: expected number")
        return value
    if schema_type == "boolean":
        if type(value) is not bool:
            raise TypeValidationError(f"{path}: expected boolean")
        return value
    if schema_type == "array":
        if not isinstance(value, list):
            raise TypeValidationError(f"{path}: expected array")
        item_schema = schema.get("items", {})
        return [_coerce_value(item, item_schema, f"{path}[{index}]") for index, item in enumerate(value)]
    if schema_type == "object":
        return _coerce_object(value, schema, path)
    raise TypeValidationError(f"{path}: unsupported schema type {schema_type!r}")
