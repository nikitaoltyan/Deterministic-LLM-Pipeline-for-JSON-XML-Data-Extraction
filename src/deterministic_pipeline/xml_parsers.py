from __future__ import annotations

from xml.etree import ElementTree as ET

from deterministic_pipeline.contracts import ValidationIssue


def _element_to_document(element: ET.Element) -> dict[str, object]:
    children = [_element_to_document(child) for child in list(element)]
    document: dict[str, object] = {"tag": element.tag}
    if element.attrib:
        document["attributes"] = dict(sorted(element.attrib.items()))
    text = (element.text or "").strip()
    if text:
        document["text"] = text
    if children:
        document["children"] = children
    return document


class XmlDocumentParser:
    def parse(self, raw_text: str) -> tuple[dict[str, object] | None, list[ValidationIssue]]:
        try:
            root = ET.fromstring(raw_text)
        except ET.ParseError as exc:
            return None, [ValidationIssue(path="$", message=str(exc), validator="xml_parse")]
        return _element_to_document(root), []
