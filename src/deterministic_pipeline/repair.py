from __future__ import annotations

from copy import deepcopy
from typing import Any

from deterministic_pipeline.config import RepairPolicy
from deterministic_pipeline.contracts import RepairAction, RepairResult


def repair_document(document: dict[str, Any], schema: dict[str, Any], policy: RepairPolicy) -> RepairResult:
    repaired = deepcopy(document)
    actions: list[RepairAction] = []
    repaired = _repair_value(repaired, schema, policy, "$", actions)
    return RepairResult(document=repaired, actions=actions, repaired=bool(actions))


def _repair_value(value: Any, schema: dict[str, Any], policy: RepairPolicy, path: str, actions: list[RepairAction]) -> Any:
    schema_type = schema.get("type")

    if value is None:
        return value

    converted, changed = _normalize_value(value, schema)
    if changed:
        value = converted
        actions.append(RepairAction(action="normalize_scalar", path=path, detail=f"Normalized value to {schema_type}"))

    if schema_type == "object" and isinstance(value, dict):
        repaired = deepcopy(value)
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))

        if policy.drop_unknown_fields:
            for key in sorted(list(repaired.keys())):
                if key not in properties:
                    repaired.pop(key)
                    actions.append(RepairAction(action="drop_unknown_field", path=f"{path}.{key}", detail="Removed unknown field"))

        for key, spec in sorted(properties.items()):
            child_path = f"{path}.{key}"
            if key not in repaired and policy.apply_schema_defaults and "default" in spec and key not in required:
                repaired[key] = deepcopy(spec["default"])
                actions.append(RepairAction(action="apply_default", path=child_path, detail="Applied schema default"))
            if key in repaired:
                repaired[key] = _repair_value(repaired[key], spec, policy, child_path, actions)
        return repaired

    if schema_type == "array" and isinstance(value, list):
        item_schema = schema.get("items", {})
        return [_repair_value(item, item_schema, policy, f"{path}[{index}]", actions) for index, item in enumerate(value)]

    return value


def _normalize_value(value: Any, spec: dict[str, Any]) -> tuple[Any, bool]:
    if value is None:
        return value, False
    schema_type = spec.get("type")
    if isinstance(value, str):
        if schema_type == "integer":
            try:
                return int(value), True
            except ValueError:
                return value, False
        if schema_type == "number":
            try:
                return float(value), True
            except ValueError:
                return value, False
        if schema_type == "boolean":
            lower = value.lower()
            if lower == "true":
                return True, True
            if lower == "false":
                return False, True
    return value, False
