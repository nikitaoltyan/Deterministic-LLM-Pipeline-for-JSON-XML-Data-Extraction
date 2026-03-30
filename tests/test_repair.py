from __future__ import annotations

from deterministic_pipeline.config import RepairPolicy
from deterministic_pipeline.repair import repair_document


def test_repair_document_recurses_through_nested_objects_and_arrays() -> None:
    schema = {
        "type": "object",
        "required": ["meta"],
        "additionalProperties": False,
        "properties": {
            "meta": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "priority": {"type": "integer"},
                    "enabled": {"type": "boolean"},
                    "tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "label": {"type": "string"},
                                "score": {"type": "number"},
                            },
                        },
                    },
                    "notes": {
                        "type": "array",
                        "default": [],
                        "items": {"type": "string"},
                    },
                },
            },
        },
    }
    document = {
        "meta": {
            "priority": "2",
            "enabled": "true",
            "extra": "drop-me",
            "tags": [
                {"label": "a", "score": "1.5", "unknown": "x"},
            ],
        },
    }

    result = repair_document(document, schema, RepairPolicy())

    assert result.repaired is True
    assert result.document == {
        "meta": {
            "priority": 2,
            "enabled": True,
            "tags": [
                {"label": "a", "score": 1.5},
            ],
            "notes": [],
        },
    }
    assert any(action.path == "$.meta.extra" for action in result.actions)
    assert any(action.path == "$.meta.tags[0].unknown" for action in result.actions)
    assert any(action.path == "$.meta.priority" for action in result.actions)
    assert any(action.path == "$.meta.tags[0].score" for action in result.actions)
