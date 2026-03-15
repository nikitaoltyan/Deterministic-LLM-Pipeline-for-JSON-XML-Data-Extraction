from __future__ import annotations

import json

from deterministic_pipeline.config import CanonicalizationPolicy


def canonicalize_json(document: dict, policy: CanonicalizationPolicy) -> str:
    return json.dumps(
        document,
        ensure_ascii=policy.ensure_ascii,
        sort_keys=policy.sort_keys,
        separators=policy.separators,
    )
