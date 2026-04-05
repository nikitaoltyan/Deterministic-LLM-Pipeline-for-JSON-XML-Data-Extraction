from __future__ import annotations

from typing import Any

from deterministic_pipeline.config import CanonicalizationPolicy


def _render_element(node: dict[str, Any]) -> str:
    tag = node["tag"]
    attributes = node.get("attributes", {})
    attribute_text = "".join(
        f' {name}="{value}"'
        for name, value in sorted(attributes.items())
    )
    children = node.get("children", [])
    text = node.get("text")
    if not children and text is None:
        return f"<{tag}{attribute_text}/>"
    child_text = "".join(_render_element(child) for child in children)
    content = f"{text or ''}{child_text}"
    return f"<{tag}{attribute_text}>{content}</{tag}>"


class XmlCanonicalizer:
    def canonicalize(self, document: dict[str, Any], policy: CanonicalizationPolicy) -> str:
        declaration = '<?xml version="1.0" encoding="UTF-8"?>'
        rendered = _render_element(document)
        return f"{declaration}{rendered}"
