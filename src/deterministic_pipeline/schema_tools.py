from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
