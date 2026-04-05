from __future__ import annotations

from deterministic_pipeline.config import CanonicalizationPolicy
from deterministic_pipeline.xml_canonicalizers import XmlCanonicalizer


def test_xml_canonicalizer_renders_stable_text() -> None:
    canonicalizer = XmlCanonicalizer()

    canonical = canonicalizer.canonicalize(
        {
            "tag": "record",
            "attributes": {"published": "true", "priority": "2"},
            "children": [
                {"tag": "title", "text": "Demo title"},
                {"tag": "summary", "text": "Short summary"},
                {"tag": "tags"},
            ],
        },
        CanonicalizationPolicy(),
    )

    assert canonical == (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<record priority="2" published="true"><title>Demo title</title>'
        "<summary>Short summary</summary><tags/></record>"
    )
