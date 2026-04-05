from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_xsd_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalize_json_schema_artifact(schema: dict[str, Any], schema_id: str = "schema") -> dict[str, Any]:
    normalized_schema = _normalize_schema(schema)
    schema_name = _to_schema_name(schema_id or schema.get("title", "schema"))
    canonical_schema = json.dumps(normalized_schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(canonical_schema.encode("utf-8")).hexdigest()

    return {
        "artifact_version": "v1",
        "formalism": "normalized-json-schema-subset",
        "schema_name": schema_name,
        "fingerprint": fingerprint,
        "root_type": normalized_schema.get("type", "object"),
        "normalized_schema": normalized_schema,
    }


def build_json_grammar_artifact(normalized_schema_artifact: dict[str, Any]) -> dict[str, Any]:
    normalized_schema = normalized_schema_artifact["normalized_schema"]
    schema_name = normalized_schema_artifact["schema_name"]

    return {
        "artifact_version": "v1",
        "formalism": "normalized-json-schema-subset",
        "schema_name": schema_name,
        "fingerprint": normalized_schema_artifact["fingerprint"],
        "root_type": normalized_schema.get("type", "object"),
        "required": list(normalized_schema.get("required", [])),
        "properties": sorted(normalized_schema.get("properties", {}).keys()),
        "normalized_schema": normalized_schema,
        "schema_artifact_ref": {
            "formalism": normalized_schema_artifact["formalism"],
            "artifact_version": normalized_schema_artifact["artifact_version"],
            "fingerprint": normalized_schema_artifact["fingerprint"],
        },
        "provider_contracts": {
            "openai_compatible": {
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_name,
                        "strict": True,
                        "schema": normalized_schema,
                    },
                }
            }
        },
    }


def schema_to_grammar(schema: dict[str, Any], schema_id: str = "schema") -> dict[str, Any]:
    normalized_schema_artifact = normalize_json_schema_artifact(schema, schema_id=schema_id)
    return build_json_grammar_artifact(normalized_schema_artifact)


def normalize_xsd_schema_artifact(xsd_text: str, schema_id: str = "schema") -> dict[str, Any]:
    root = ET.fromstring(xsd_text)
    namespace = _detect_xsd_namespace(root.tag)
    element_declarations = {
        child.attrib["name"]: child
        for child in root.findall(f"./{namespace}element")
        if child.attrib.get("name")
    }
    if not element_declarations:
        raise ValueError("XSD subset requires at least one top-level xs:element declaration.")
    if len(element_declarations) != 1:
        raise ValueError("XSD subset currently supports exactly one top-level xs:element declaration.")
    root_name, root_element = next(iter(element_declarations.items()))
    normalized_root = _normalize_xsd_element(root_element, namespace, element_declarations)
    canonical_schema = json.dumps(normalized_root, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(canonical_schema.encode("utf-8")).hexdigest()
    return {
        "artifact_version": "v1",
        "formalism": "normalized-xsd-subset",
        "schema_name": _to_schema_name(schema_id or root_name),
        "fingerprint": fingerprint,
        "root_type": "element",
        "normalized_schema": {
            "root_element": normalized_root,
        },
    }


def build_xml_grammar_artifact(normalized_schema_artifact: dict[str, Any]) -> dict[str, Any]:
    normalized_root = normalized_schema_artifact["normalized_schema"]["root_element"]
    required_attributes = [
        f"@{name}"
        for name, attribute in sorted(normalized_root.get("attributes", {}).items())
        if attribute.get("required")
    ]
    required_children = [
        child["name"]
        for child in normalized_root.get("children", [])
        if child.get("min_occurs", 1) > 0
    ]
    return {
        "artifact_version": "v1",
        "formalism": "normalized-xsd-subset",
        "schema_name": normalized_schema_artifact["schema_name"],
        "fingerprint": normalized_schema_artifact["fingerprint"],
        "root_type": "element",
        "required": required_attributes + required_children,
        "properties": [child["name"] for child in normalized_root.get("children", [])],
        "normalized_schema": normalized_schema_artifact["normalized_schema"],
        "schema_artifact_ref": {
            "formalism": normalized_schema_artifact["formalism"],
            "artifact_version": normalized_schema_artifact["artifact_version"],
            "fingerprint": normalized_schema_artifact["fingerprint"],
        },
        "provider_contracts": {},
    }


def _normalize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    if "oneOf" in schema or "anyOf" in schema or "allOf" in schema:
        raise ValueError("Union and composition constructs are not supported in the normalized schema subset.")

    schema_type, nullable = _normalize_type(schema.get("type"))
    normalized: dict[str, Any] = {}
    if "$schema" in schema:
        normalized["$schema"] = schema["$schema"]
    if "title" in schema:
        normalized["title"] = schema["title"]
    if "description" in schema:
        normalized["description"] = schema["description"]
    if "enum" in schema:
        normalized["enum"] = list(schema["enum"])
    if schema_type is not None:
        normalized["type"] = schema_type
    if nullable:
        normalized["nullable"] = True
    for key in ("default", "minLength", "maxLength", "minimum", "maximum", "minItems", "maxItems"):
        if key in schema:
            normalized[key] = schema[key]

    if schema_type == "object":
        properties = schema.get("properties", {})
        normalized["properties"] = {
            key: _normalize_schema(properties[key])
            for key in sorted(properties.keys())
        }
        normalized["required"] = sorted(schema.get("required", []))
        normalized["additionalProperties"] = schema.get("additionalProperties", False)
    elif schema_type == "array":
        normalized["items"] = _normalize_schema(schema.get("items", {}))

    return normalized


def _normalize_type(schema_type: Any) -> tuple[str | None, bool]:
    if schema_type is None:
        return None, False
    if isinstance(schema_type, str):
        return schema_type, False
    if isinstance(schema_type, list):
        unique_types = []
        for item in schema_type:
            if item not in unique_types:
                unique_types.append(item)
        non_null = [item for item in unique_types if item != "null"]
        has_null = len(non_null) != len(unique_types)
        if len(non_null) == 1:
            return non_null[0], has_null
    raise ValueError("Only single types and nullable [type, null] unions are supported in the normalized schema subset.")


def _to_schema_name(value: str) -> str:
    lowered = value.strip().lower()
    sanitized = re.sub(r"[^a-z0-9]+", "_", lowered)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return sanitized or "schema"


def _detect_xsd_namespace(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag[: tag.index("}") + 1]
    return ""


def _normalize_xsd_element(
    element: ET.Element,
    namespace: str,
    element_declarations: dict[str, ET.Element],
) -> dict[str, Any]:
    name = element.attrib.get("name")
    if not name:
        raise ValueError("XSD element declarations in the supported subset must define a name.")
    complex_type = element.find(f"./{namespace}complexType")
    schema_type = _map_xsd_scalar_type(element.attrib.get("type"))
    normalized: dict[str, Any] = {
        "name": name,
        "type": schema_type if schema_type else "complex",
        "min_occurs": int(element.attrib.get("minOccurs", "1")),
        "max_occurs": _parse_max_occurs(element.attrib.get("maxOccurs", "1")),
    }
    if complex_type is not None:
        normalized.update(_normalize_xsd_complex_type(complex_type, namespace, element_declarations))
    elif element.attrib.get("type") in element_declarations:
        referenced = _normalize_xsd_element(element_declarations[element.attrib["type"]], namespace, element_declarations)
        normalized.update({key: value for key, value in referenced.items() if key not in {"name", "min_occurs", "max_occurs"}})
    return normalized


def _normalize_xsd_complex_type(
    complex_type: ET.Element,
    namespace: str,
    element_declarations: dict[str, ET.Element],
) -> dict[str, Any]:
    sequence = complex_type.find(f"./{namespace}sequence")
    all_group = complex_type.find(f"./{namespace}all")
    choice_group = complex_type.find(f"./{namespace}choice")
    if choice_group is not None:
        raise ValueError("XSD choice is not supported in the normalized XSD subset.")
    if all_group is not None:
        raise ValueError("XSD all-group is not supported in the normalized XSD subset.")
    children: list[dict[str, Any]] = []
    if sequence is not None:
        children = [
            _normalize_xsd_element(child, namespace, element_declarations)
            for child in sequence.findall(f"./{namespace}element")
        ]
    attributes = {
        attribute.attrib["name"]: {
            "type": _map_xsd_scalar_type(attribute.attrib.get("type")),
            "required": attribute.attrib.get("use") == "required",
        }
        for attribute in complex_type.findall(f"./{namespace}attribute")
        if attribute.attrib.get("name")
    }
    return {
        "children": children,
        "attributes": attributes,
    }


def _parse_max_occurs(value: str) -> int | str:
    if value == "unbounded":
        return value
    return int(value)


def _map_xsd_scalar_type(type_name: str | None) -> str | None:
    if type_name is None:
        return None
    normalized = type_name.split(":")[-1]
    mapping = {
        "string": "string",
        "boolean": "boolean",
        "int": "integer",
        "integer": "integer",
        "decimal": "number",
    }
    if normalized not in mapping:
        raise ValueError(f"Unsupported XSD scalar type in normalized subset: {type_name}")
    return mapping[normalized]
