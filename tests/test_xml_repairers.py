from __future__ import annotations

from pathlib import Path

from deterministic_pipeline.config import RepairPolicy
from deterministic_pipeline.schema_tools import load_xsd_text, normalize_xsd_schema_artifact
from deterministic_pipeline.xml_parsers import XmlDocumentParser
from deterministic_pipeline.xml_repairers import XmlBaselineRepairer
from deterministic_pipeline.xml_validators import XmlBaselineValidator


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_xml_repairer_drops_unknowns_and_reorders_sequence() -> None:
    schema = normalize_xsd_schema_artifact(load_xsd_text(PROJECT_ROOT / "schemas" / "extraction_record.xsd"), schema_id="extraction-record-v1")
    document, issues = XmlDocumentParser().parse(
        '<record priority=" 2 " published="TRUE" extra="drop-me"><summary>Short summary</summary><title>Demo title</title><tags/><noise/></record>'
    )

    assert issues == []
    result = XmlBaselineRepairer().repair(document, schema, RepairPolicy())

    assert result.repaired is True
    assert result.document == {
        "tag": "record",
        "attributes": {"priority": "2", "published": "true"},
        "children": [
            {"tag": "title", "text": "Demo title"},
            {"tag": "summary", "text": "Short summary"},
            {"tag": "tags"},
        ],
    }
    assert XmlBaselineValidator().validate(result.document, schema) == []
