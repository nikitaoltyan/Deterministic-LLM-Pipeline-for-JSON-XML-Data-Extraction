from __future__ import annotations

import json
from typing import Any

from deterministic_pipeline.config import CanonicalizationPolicy


class JsonCanonicalizer:
    def canonicalize(self, document: dict[str, Any], policy: CanonicalizationPolicy) -> str:
        return json.dumps(
            document,
            ensure_ascii=policy.ensure_ascii,
            sort_keys=policy.sort_keys,
            separators=policy.separators,
        )
