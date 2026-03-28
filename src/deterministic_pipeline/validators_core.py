from __future__ import annotations

from typing import Any

from deterministic_pipeline.contracts import ValidationIssue
from deterministic_pipeline.validator import validate_document


class JsonSchemaDocumentValidator:
    def validate(self, document: dict[str, Any], schema: dict[str, Any]) -> list[ValidationIssue]:
        return validate_document(document, schema)
