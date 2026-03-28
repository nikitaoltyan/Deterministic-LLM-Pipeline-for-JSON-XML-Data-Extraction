from __future__ import annotations

from typing import Any

from deterministic_pipeline.typing import coerce_typed_document


class JsonTypeMapper:
    def map_to_typed(self, document: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        return coerce_typed_document(document, schema)
