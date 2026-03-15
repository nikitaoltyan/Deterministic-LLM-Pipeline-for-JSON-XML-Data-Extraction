from __future__ import annotations

from copy import deepcopy
from typing import Any

from deterministic_pipeline.config import RepairPolicy
from deterministic_pipeline.contracts import RepairAction, RepairResult


def repair_document(document: dict[str, Any], schema: dict[str, Any], policy: RepairPolicy) -> RepairResult:
    repaired = deepcopy(document)
    actions: list[RepairAction] = []

    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    if policy.drop_unknown_fields:
        for key in sorted(list(repaired.keys())):
            if key not in properties:
                repaired.pop(key)
                actions.append(RepairAction(action="drop_unknown_field", path=f"$.{key}", detail="Removed unknown field"))

    for key, spec in sorted(properties.items()):
        if key not in repaired and policy.apply_schema_defaults and "default" in spec and key not in required:
            repaired[key] = spec["default"]
            actions.append(RepairAction(action="apply_default", path=f"$.{key}", detail="Applied schema default"))

    if policy.normalize_scalar_strings:
        for key, spec in sorted(properties.items()):
            if key in repaired:
                converted, changed = _normalize_value(repaired[key], spec)
                if changed:
                    repaired[key] = converted
                    actions.append(
                        RepairAction(action="normalize_scalar", path=f"$.{key}", detail=f"Normalized value to {spec.get('type')}")
                    )

    return RepairResult(document=repaired, actions=actions, repaired=bool(actions))


def _normalize_value(value: Any, spec: dict[str, Any]) -> tuple[Any, bool]:
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
