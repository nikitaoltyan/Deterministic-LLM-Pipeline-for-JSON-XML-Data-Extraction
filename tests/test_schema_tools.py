from __future__ import annotations

import pytest

from deterministic_pipeline.schema_tools import build_json_grammar_artifact, normalize_json_schema_artifact, schema_to_grammar


def test_normalize_json_schema_artifact_builds_stable_normalized_schema() -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "FloodEvacuationRecord",
        "type": "object",
        "required": ["rise_speed", "time"],
        "properties": {
            "rise_speed": {"type": "integer"},
            "time": {"type": "string"},
        },
    }

    normalized = normalize_json_schema_artifact(schema, schema_id="flood-evacuation-v1")

    assert normalized["artifact_version"] == "v1"
    assert normalized["formalism"] == "normalized-json-schema-subset"
    assert normalized["schema_name"] == "flood_evacuation_v1"
    assert normalized["root_type"] == "object"
    assert normalized["normalized_schema"]["additionalProperties"] is False
    assert list(normalized["normalized_schema"]["properties"].keys()) == ["rise_speed", "time"]
    assert normalized["fingerprint"]


def test_build_json_grammar_artifact_compiles_provider_contract() -> None:
    normalized_schema_artifact = normalize_json_schema_artifact(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "FloodEvacuationRecord",
            "type": "object",
            "required": ["rise_speed", "time"],
            "properties": {
                "rise_speed": {"type": "integer"},
                "time": {"type": "string"},
            },
        },
        schema_id="flood-evacuation-v1",
    )
    grammar = build_json_grammar_artifact(normalized_schema_artifact)

    assert grammar["artifact_version"] == "v1"
    assert grammar["formalism"] == "normalized-json-schema-subset"
    assert grammar["schema_name"] == "flood_evacuation_v1"
    assert grammar["required"] == ["rise_speed", "time"]
    assert grammar["schema_artifact_ref"]["artifact_version"] == "v1"
    assert grammar["schema_artifact_ref"]["formalism"] == "normalized-json-schema-subset"
    assert grammar["schema_artifact_ref"]["fingerprint"] == normalized_schema_artifact["fingerprint"]
    response_format = grammar["provider_contracts"]["openai_compatible"]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"]["type"] == "object"


def test_schema_to_grammar_normalizes_nullable_enum_and_nested_constraints() -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "NestedRecord",
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["draft", "published"]},
            "owner": {"type": ["string", "null"]},
            "items": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                    },
                },
            },
        },
    }

    grammar = schema_to_grammar(schema, schema_id="nested-record-v1")
    normalized = grammar["normalized_schema"]

    assert normalized["properties"]["status"]["enum"] == ["draft", "published"]
    assert normalized["properties"]["owner"]["type"] == "string"
    assert normalized["properties"]["owner"]["nullable"] is True
    assert normalized["properties"]["items"]["minItems"] == 1
    assert normalized["properties"]["items"]["items"]["properties"]["name"]["minLength"] == 1


def test_schema_to_grammar_rejects_unsupported_union_constructs() -> None:
    schema = {
        "type": "object",
        "properties": {
            "value": {
                "oneOf": [{"type": "string"}, {"type": "integer"}],
            },
        },
    }

    with pytest.raises(ValueError, match="not supported"):
        schema_to_grammar(schema, schema_id="unsupported-union")
