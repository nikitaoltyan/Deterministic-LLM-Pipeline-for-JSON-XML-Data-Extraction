from __future__ import annotations

from pathlib import Path

import pytest

from deterministic_pipeline.schema_tools import load_xsd_text, normalize_xsd_schema_artifact
from deterministic_pipeline.typing import TypeValidationError
from deterministic_pipeline.xml_parsers import XmlDocumentParser
from deterministic_pipeline.xml_type_mappers import XmlBaselineTypeMapper


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_xml_type_mapper_converts_valid_document_to_typed_object() -> None:
    schema = normalize_xsd_schema_artifact(load_xsd_text(PROJECT_ROOT / "schemas" / "extraction_record.xsd"), schema_id="extraction-record-v1")
    document, issues = XmlDocumentParser().parse(
        '<record priority="2" published="true"><title>Demo title</title><summary>Short summary</summary><tags/></record>'
    )

    assert issues == []
    typed = XmlBaselineTypeMapper().map_to_typed(document, schema)

    assert typed == {
        "priority": 2,
        "published": True,
        "title": "Demo title",
        "summary": "Short summary",
        "tags": {},
    }


def test_xml_type_mapper_rejects_invalid_scalar_value() -> None:
    schema = normalize_xsd_schema_artifact(load_xsd_text(PROJECT_ROOT / "schemas" / "extraction_record.xsd"), schema_id="extraction-record-v1")
    document, issues = XmlDocumentParser().parse(
        '<record priority="high" published="true"><title>Demo title</title><summary>Short summary</summary><tags/></record>'
    )

    assert issues == []
    with pytest.raises(TypeValidationError, match="expected integer"):
        XmlBaselineTypeMapper().map_to_typed(document, schema)
