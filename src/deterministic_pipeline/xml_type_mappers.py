from __future__ import annotations

from typing import Any

from deterministic_pipeline.typing import TypeValidationError


class XmlBaselineTypeMapper:
    def map_to_typed(self, document: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        if schema.get("formalism") != "normalized-xsd-subset":
            return document
        typed = _map_element(document, schema["normalized_schema"]["root_element"], "$")
        if not isinstance(typed, dict):
            raise TypeValidationError("$.root: expected complex XML root element")
        return typed


def _map_element(document: dict[str, Any], schema_element: dict[str, Any], path: str) -> Any:
    if document.get("tag") != schema_element["name"]:
        raise TypeValidationError(f"{path}: expected XML element <{schema_element['name']}>")
    if schema_element.get("type") != "complex":
        return _coerce_scalar(document.get("text"), schema_element.get("type"), path)

    result: dict[str, Any] = {}
    attributes = document.get("attributes", {})
    if not isinstance(attributes, dict):
        raise TypeValidationError(f"{path}.attributes: expected XML attributes object")
    for name, attribute_schema in sorted(schema_element.get("attributes", {}).items()):
        attribute_path = f"{path}.@{name}"
        if name not in attributes:
            if attribute_schema.get("required"):
                raise TypeValidationError(f"{attribute_path}: required XML attribute is missing")
            continue
        result[name] = _coerce_scalar(attributes[name], attribute_schema.get("type"), attribute_path)

    children = document.get("children", [])
    if not isinstance(children, list):
        raise TypeValidationError(f"{path}.children: expected XML children list")
    grouped_children: dict[str, list[dict[str, Any]]] = {}
    for child in children:
        grouped_children.setdefault(child.get("tag"), []).append(child)

    for child_schema in schema_element.get("children", []):
        name = child_schema["name"]
        matched_children = grouped_children.get(name, [])
        min_occurs = child_schema.get("min_occurs", 1)
        max_occurs = child_schema.get("max_occurs", 1)
        if len(matched_children) < min_occurs:
            raise TypeValidationError(f"{path}.{name}: required XML element is missing")
        if max_occurs != "unbounded" and len(matched_children) > max_occurs:
            raise TypeValidationError(f"{path}.{name}: XML element occurs more than allowed")
        typed_values = [
            _map_element(child, child_schema, f"{path}.{name}[{index}]")
            for index, child in enumerate(matched_children)
        ]
        if max_occurs == 1:
            if typed_values:
                result[name] = typed_values[0]
        else:
            result[name] = typed_values
    return result


def _coerce_scalar(value: Any, expected_type: str | None, path: str) -> Any:
    if not isinstance(value, str):
        raise TypeValidationError(f"{path}: expected XML scalar text")
    if expected_type in {None, "string"}:
        return value
    if expected_type == "integer":
        try:
            return int(value)
        except ValueError as exc:
            raise TypeValidationError(f"{path}: expected integer") from exc
    if expected_type == "number":
        try:
            return float(value)
        except ValueError as exc:
            raise TypeValidationError(f"{path}: expected number") from exc
    if expected_type == "boolean":
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        raise TypeValidationError(f"{path}: expected boolean")
    raise TypeValidationError(f"{path}: unsupported XSD scalar type {expected_type!r}")
