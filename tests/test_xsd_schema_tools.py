from __future__ import annotations

from pathlib import Path

from deterministic_pipeline.schema_tools import build_xml_grammar_artifact, load_xsd_text, normalize_xsd_schema_artifact


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_normalize_xsd_schema_artifact_extracts_root_structure() -> None:
    xsd_text = load_xsd_text(PROJECT_ROOT / "schemas" / "extraction_record.xsd")

    artifact = normalize_xsd_schema_artifact(xsd_text, schema_id="extraction-record-v1")

    assert artifact["formalism"] == "normalized-xsd-subset"
    root = artifact["normalized_schema"]["root_element"]
    assert root["name"] == "record"
    assert root["attributes"]["priority"] == {"type": "integer", "required": True}
    assert root["attributes"]["published"] == {"type": "boolean", "required": True}
    assert [child["name"] for child in root["children"]] == ["title", "summary", "tags"]


def test_build_xml_grammar_artifact_uses_normalized_xsd() -> None:
    xsd_text = load_xsd_text(PROJECT_ROOT / "schemas" / "extraction_record.xsd")
    normalized_artifact = normalize_xsd_schema_artifact(xsd_text, schema_id="extraction-record-v1")

    grammar = build_xml_grammar_artifact(normalized_artifact)

    assert grammar["formalism"] == "normalized-xsd-subset"
    assert grammar["root_type"] == "element"
    assert "@priority" in grammar["required"]
    assert "@published" in grammar["required"]
    assert "title" in grammar["properties"]
