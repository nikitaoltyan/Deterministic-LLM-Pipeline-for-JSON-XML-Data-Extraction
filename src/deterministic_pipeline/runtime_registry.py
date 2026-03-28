from __future__ import annotations

from deterministic_pipeline.canonicalizers import JsonCanonicalizer
from deterministic_pipeline.formats import FormatRuntime, StructuredFormat, UnsupportedFormatError
from deterministic_pipeline.parsers import JsonDocumentParser
from deterministic_pipeline.repairers import JsonDocumentRepairer
from deterministic_pipeline.type_mappers import JsonTypeMapper
from deterministic_pipeline.validators_core import JsonSchemaDocumentValidator


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
    raise UnsupportedFormatError(f"Unsupported output format: {output_format.value}")
