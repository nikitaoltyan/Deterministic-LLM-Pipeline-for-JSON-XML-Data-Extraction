from __future__ import annotations

from copy import deepcopy
from typing import Any

from deterministic_pipeline.config import RepairPolicy
from deterministic_pipeline.contracts import RepairAction, RepairResult


class XmlBaselineRepairer:
    def repair(self, document: dict[str, Any], schema: dict[str, Any], policy: RepairPolicy) -> RepairResult:
        if schema.get("formalism") != "normalized-xsd-subset":
            return RepairResult(document=document, actions=[], repaired=False)
        repaired = deepcopy(document)
        actions: list[RepairAction] = []
        repaired = _repair_element(repaired, schema["normalized_schema"]["root_element"], policy, "$", actions)
        return RepairResult(document=repaired, actions=actions, repaired=bool(actions))


def _repair_element(
    document: dict[str, Any],
    schema_element: dict[str, Any],
    policy: RepairPolicy,
    path: str,
    actions: list[RepairAction],
) -> dict[str, Any]:
    repaired = deepcopy(document)
    attributes = deepcopy(repaired.get("attributes", {}))
    expected_attributes = schema_element.get("attributes", {})

    if policy.drop_unknown_fields:
        for name in sorted(list(attributes.keys())):
            if name not in expected_attributes:
                attributes.pop(name)
                actions.append(RepairAction(action="drop_unknown_attribute", path=f"{path}.@{name}", detail="Removed unknown XML attribute"))

    for name, raw_value in list(attributes.items()):
        normalized, changed = _normalize_scalar_text(raw_value, expected_attributes.get(name, {}).get("type"))
        if changed:
            attributes[name] = normalized
            actions.append(RepairAction(action="normalize_scalar", path=f"{path}.@{name}", detail="Normalized XML attribute value"))
    if attributes:
        repaired["attributes"] = attributes
    elif "attributes" in repaired:
        repaired.pop("attributes")

    if repaired.get("text") is not None and isinstance(repaired["text"], str):
        normalized_text = repaired["text"].strip()
        if normalized_text != repaired["text"]:
            repaired["text"] = normalized_text
            actions.append(RepairAction(action="normalize_scalar", path=path, detail="Trimmed XML text content"))
        if schema_element.get("type") != "complex":
            scalar_text, changed = _normalize_scalar_text(repaired["text"], schema_element.get("type"))
            if changed:
                repaired["text"] = scalar_text
                actions.append(RepairAction(action="normalize_scalar", path=path, detail="Normalized XML scalar text"))

    children = deepcopy(repaired.get("children", []))
    expected_children = {child["name"]: child for child in schema_element.get("children", [])}
    if policy.drop_unknown_fields:
        filtered_children = []
        for index, child in enumerate(children):
            if child.get("tag") not in expected_children:
                actions.append(
                    RepairAction(
                        action="drop_unknown_field",
                        path=f"{path}.{child.get('tag', 'unknown')}[{index}]",
                        detail="Removed unexpected XML child element",
                    )
                )
                continue
            filtered_children.append(child)
        children = filtered_children

    for index, child in enumerate(children):
        child_schema = expected_children.get(child.get("tag"))
        if child_schema is None:
            continue
        child_path = f"{path}.{child['tag']}[{index}]"
        children[index] = _repair_element(child, child_schema, policy, child_path, actions)

    ordered_children = _order_children(children, schema_element.get("children", []))
    if ordered_children != children:
        children = ordered_children
        actions.append(RepairAction(action="reorder_children", path=path, detail="Reordered XML children to match XSD sequence"))
    if children:
        repaired["children"] = children
    elif "children" in repaired:
        repaired.pop("children")

    return repaired


def _order_children(children: list[dict[str, Any]], ordered_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order_index = {spec["name"]: index for index, spec in enumerate(ordered_specs)}
    indexed_children = list(enumerate(children))
    indexed_children.sort(key=lambda item: (order_index.get(item[1].get("tag"), len(order_index)), item[0]))
    return [child for _, child in indexed_children]


def _normalize_scalar_text(value: Any, expected_type: str | None) -> tuple[Any, bool]:
    if not isinstance(value, str):
        return value, False
    trimmed = value.strip()
    changed = trimmed != value
    if expected_type == "boolean":
        lowered = trimmed.lower()
        if lowered in {"true", "false"}:
            return lowered, True
    if expected_type in {"integer", "number", "string", None}:
        return trimmed, changed
    return trimmed, changed
