from __future__ import annotations

from deterministic_pipeline.xml_parsers import XmlDocumentParser


def test_xml_document_parser_parses_valid_xml() -> None:
    parser = XmlDocumentParser()

    document, issues = parser.parse('<record priority="2"><title>Demo</title><tags/></record>')

    assert issues == []
    assert document == {
        "tag": "record",
        "attributes": {"priority": "2"},
        "children": [
            {"tag": "title", "text": "Demo"},
            {"tag": "tags"},
        ],
    }


def test_xml_document_parser_rejects_malformed_xml() -> None:
    parser = XmlDocumentParser()

    document, issues = parser.parse("<record><title>Demo</record>")

    assert document is None
    assert len(issues) == 1
    assert issues[0].validator == "xml_parse"
