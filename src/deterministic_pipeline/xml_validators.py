from __future__ import annotations

from typing import Any

from deterministic_pipeline.contracts import ValidationIssue


class XmlBaselineValidator:
    def validate(self, document: dict[str, Any], schema: dict[str, Any]) -> list[ValidationIssue]:
        if not document.get("tag"):
            return [ValidationIssue(path="$", message="XML root element must define a tag.", validator="xml_root")]
        children = document.get("children", [])
        if children is not None and not isinstance(children, list):
            return [ValidationIssue(path="$.children", message="XML children must be a list when present.", validator="xml_structure")]
        return []
