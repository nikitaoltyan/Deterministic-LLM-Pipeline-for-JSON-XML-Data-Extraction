from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from deterministic_pipeline.contracts import ValidationIssue


def validate_document(document: dict[str, Any], schema: dict[str, Any]) -> list[ValidationIssue]:
    validator = Draft202012Validator(schema)
    issues: list[ValidationIssue] = []
    for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path)):
        path = "$"
        if error.path:
            path = "$." + ".".join(str(part) for part in error.path)
        issues.append(
            ValidationIssue(
                path=path,
                message=error.message,
                validator=error.validator,
            )
        )
    return issues
