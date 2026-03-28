from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from deterministic_pipeline.contracts import RepairResult, ValidationIssue
from deterministic_pipeline.typing import TypeValidationError


class StructuredFormat(str, Enum):
    JSON = "json"
    XML = "xml"


class DocumentParser(Protocol):
    def parse(self, raw_text: str) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
        ...


class DocumentValidator(Protocol):
    def validate(self, document: dict[str, Any], schema: dict[str, Any]) -> list[ValidationIssue]:
        ...


class DocumentRepairer(Protocol):
    def repair(self, document: dict[str, Any], schema: dict[str, Any], policy: Any) -> RepairResult:
        ...


class DocumentCanonicalizer(Protocol):
    def canonicalize(self, document: dict[str, Any], policy: Any) -> str:
        ...


class DocumentTypeMapper(Protocol):
    def map_to_typed(self, document: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class FormatRuntime:
    output_format: StructuredFormat
    parser: DocumentParser
    validator: DocumentValidator
    repairer: DocumentRepairer
    canonicalizer: DocumentCanonicalizer
    type_mapper: DocumentTypeMapper


class UnsupportedFormatError(RuntimeError):
    pass


def map_type_error(exc: TypeValidationError) -> ValidationIssue:
    return ValidationIssue(path="$", message=str(exc), validator="strict_typing")
