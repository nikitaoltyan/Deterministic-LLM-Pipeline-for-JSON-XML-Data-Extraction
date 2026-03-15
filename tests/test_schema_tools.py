from __future__ import annotations

from deterministic_pipeline.schema_tools import schema_to_grammar


def test_schema_to_grammar_compiles_normalized_schema_and_provider_contract() -> None:
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

    grammar = schema_to_grammar(schema, schema_id="flood-evacuation-v1")

    assert grammar["artifact_version"] == "v2"
    assert grammar["formalism"] == "normalized-json-schema-subset"
    assert grammar["schema_name"] == "flood_evacuation_v1"
    assert grammar["required"] == ["rise_speed", "time"]
    assert grammar["normalized_schema"]["additionalProperties"] is False
    assert list(grammar["normalized_schema"]["properties"].keys()) == ["rise_speed", "time"]
    response_format = grammar["provider_contracts"]["openai_compatible"]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert response_format["json_schema"]["schema"]["type"] == "object"
