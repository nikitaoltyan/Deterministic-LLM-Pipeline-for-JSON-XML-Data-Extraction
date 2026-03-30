from __future__ import annotations

import pytest

from deterministic_pipeline.typing import TypeValidationError, coerce_typed_document


def test_typed_document_supports_nested_objects_nullable_and_enum() -> None:
    schema = {
        "type": "object",
        "required": ["meta", "status"],
        "additionalProperties": False,
        "properties": {
            "meta": {
                "type": "object",
                "required": ["tags", "owner"],
                "additionalProperties": False,
                "properties": {
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "owner": {
                        "type": "string",
                        "nullable": True,
                    },
                },
            },
            "status": {
                "type": "string",
                "enum": ["draft", "published"],
            },
        },
    }

    typed = coerce_typed_document(
        {
            "meta": {"tags": ["alpha", "beta"], "owner": None},
            "status": "draft",
        },
        schema,
    )

    assert typed == {
        "meta": {"tags": ["alpha", "beta"], "owner": None},
        "status": "draft",
    }


def test_typed_document_rejects_enum_violation() -> None:
    schema = {
        "type": "object",
        "required": ["status"],
        "properties": {
            "status": {
                "type": "string",
                "enum": ["draft", "published"],
            },
        },
    }

    with pytest.raises(TypeValidationError, match="value must be one of"):
        coerce_typed_document({"status": "archived"}, schema)


def test_typed_document_rejects_unsupported_union_construct() -> None:
    schema = {
        "type": "object",
        "required": ["value"],
        "properties": {
            "value": {
                "oneOf": [{"type": "string"}, {"type": "integer"}],
            },
        },
    }

    with pytest.raises(TypeValidationError, match="unsupported schema construct oneOf"):
        coerce_typed_document({"value": "x"}, schema)
