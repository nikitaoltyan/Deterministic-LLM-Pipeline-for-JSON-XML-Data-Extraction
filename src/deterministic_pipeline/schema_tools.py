from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_to_grammar(schema: dict[str, Any], schema_id: str = "schema") -> dict[str, Any]:
    normalized_schema = _normalize_schema(schema)
    schema_name = _to_schema_name(schema_id or schema.get("title", "schema"))
    canonical_schema = json.dumps(normalized_schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    fingerprint = hashlib.sha256(canonical_schema.encode("utf-8")).hexdigest()

    return {
        "artifact_version": "v2",
        "formalism": "normalized-json-schema-subset",
        "schema_name": schema_name,
        "fingerprint": fingerprint,
        "root_type": normalized_schema.get("type", "object"),
        "required": list(normalized_schema.get("required", [])),
        "properties": sorted(normalized_schema.get("properties", {}).keys()),
        "normalized_schema": normalized_schema,
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


def _normalize_schema(schema: dict[str, Any]) -> dict[str, Any]:
    schema_type = schema.get("type")
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
    else:
        if "default" in schema:
            normalized["default"] = schema["default"]

    return normalized


def _to_schema_name(value: str) -> str:
    lowered = value.strip().lower()
    sanitized = re.sub(r"[^a-z0-9]+", "_", lowered)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")
    return sanitized or "schema"
