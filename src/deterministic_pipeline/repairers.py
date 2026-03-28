from __future__ import annotations

from typing import Any

from deterministic_pipeline.config import RepairPolicy
from deterministic_pipeline.contracts import RepairResult
from deterministic_pipeline.repair import repair_document


class JsonDocumentRepairer:
    def repair(self, document: dict[str, Any], schema: dict[str, Any], policy: RepairPolicy) -> RepairResult:
        return repair_document(document, schema, policy)
