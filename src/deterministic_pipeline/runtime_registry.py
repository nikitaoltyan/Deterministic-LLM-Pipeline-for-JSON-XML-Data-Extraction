from __future__ import annotations

from deterministic_pipeline.canonicalizers import JsonCanonicalizer
from deterministic_pipeline.formats import FormatRuntime, StructuredFormat, UnsupportedFormatError
from deterministic_pipeline.parsers import JsonDocumentParser
from deterministic_pipeline.repairers import JsonDocumentRepairer
from deterministic_pipeline.type_mappers import JsonTypeMapper
from deterministic_pipeline.validators_core import JsonSchemaDocumentValidator
from deterministic_pipeline.xml_canonicalizers import XmlCanonicalizer
from deterministic_pipeline.xml_parsers import XmlDocumentParser
from deterministic_pipeline.xml_repairers import XmlBaselineRepairer
from deterministic_pipeline.xml_type_mappers import XmlBaselineTypeMapper
from deterministic_pipeline.xml_validators import XmlBaselineValidator


def get_format_runtime(output_format: StructuredFormat) -> FormatRuntime:
    if output_format == StructuredFormat.JSON:
        return FormatRuntime(
            output_format=StructuredFormat.JSON,
            parser=JsonDocumentParser(),
            validator=JsonSchemaDocumentValidator(),
            repairer=JsonDocumentRepairer(),
            canonicalizer=JsonCanonicalizer(),
            type_mapper=JsonTypeMapper(),
        )
    if output_format == StructuredFormat.XML:
        return FormatRuntime(
            output_format=StructuredFormat.XML,
            parser=XmlDocumentParser(),
            validator=XmlBaselineValidator(),
            repairer=XmlBaselineRepairer(),
            canonicalizer=XmlCanonicalizer(),
            type_mapper=XmlBaselineTypeMapper(),
        )
    raise UnsupportedFormatError(f"Unsupported output format: {output_format.value}")
