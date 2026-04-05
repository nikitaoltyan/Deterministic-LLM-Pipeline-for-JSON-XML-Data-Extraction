from __future__ import annotations

from typing import Any


class XmlBaselineTypeMapper:
    def map_to_typed(self, document: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        return document
