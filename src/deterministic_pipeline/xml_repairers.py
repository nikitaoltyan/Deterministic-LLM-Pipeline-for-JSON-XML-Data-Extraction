from __future__ import annotations

from typing import Any

from deterministic_pipeline.config import RepairPolicy
from deterministic_pipeline.contracts import RepairResult


class XmlBaselineRepairer:
    def repair(self, document: dict[str, Any], schema: dict[str, Any], policy: RepairPolicy) -> RepairResult:
        return RepairResult(document=document, actions=[], repaired=False)
