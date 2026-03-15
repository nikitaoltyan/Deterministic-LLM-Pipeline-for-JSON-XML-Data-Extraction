from __future__ import annotations

import json
from typing import Any

from deterministic_pipeline.contracts import ValidationIssue


def parse_json_document(raw_text: str) -> tuple:
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return None, [ValidationIssue(path="$", message=str(exc), validator="json_parse")]
    if not isinstance(parsed, dict):
        return None, [ValidationIssue(path="$", message="Root JSON value must be an object.", validator="json_root")]
    return parsed, []
