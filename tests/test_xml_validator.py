from __future__ import annotations

from pathlib import Path

from deterministic_pipeline.schema_tools import load_xsd_text, normalize_xsd_schema_artifact
from deterministic_pipeline.xml_parsers import XmlDocumentParser
from deterministic_pipeline.xml_validators import XmlBaselineValidator


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_xml_validator_accepts_document_matching_xsd() -> None:
    xsd = normalize_xsd_schema_artifact(load_xsd_text(PROJECT_ROOT / "schemas" / "extraction_record.xsd"), schema_id="extraction-record-v1")
    document, parse_issues = XmlDocumentParser().parse(
        '<record priority="2" published="true"><title>Demo title</title><summary>Short summary</summary><tags/></record>'
    )

    assert parse_issues == []
    issues = XmlBaselineValidator().validate(document, xsd)

    assert issues == []


def test_xml_validator_rejects_document_not_matching_xsd() -> None:
    xsd = normalize_xsd_schema_artifact(load_xsd_text(PROJECT_ROOT / "schemas" / "extraction_record.xsd"), schema_id="extraction-record-v1")
    document, parse_issues = XmlDocumentParser().parse(
        '<record priority="high" published="yes"><title>Demo title</title><tags/></record>'
    )

    assert parse_issues == []
    issues = XmlBaselineValidator().validate(document, xsd)

    assert any(issue.validator == "xsd_attribute_type" for issue in issues)
    assert any(issue.validator == "xsd_min_occurs" for issue in issues)
