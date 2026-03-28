from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class PromptPackage:
    system_prompt: str
    user_prompt: str
    schema: dict[str, Any]
    grammar: dict[str, Any]
    template_metadata: dict[str, Any]


@dataclass(frozen=True)
class GenerationRequest:
    prompt: PromptPackage
    provider_name: str
    model: str
    decoding: dict[str, Any]
    omega: dict[str, Any]


@dataclass(frozen=True)
class RawGeneration:
    text: str
    provider_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str
    validator: str


@dataclass(frozen=True)
class RepairAction:
    action: str
    path: str
    detail: str


@dataclass(frozen=True)
class RepairResult:
    document: dict[str, Any]
    actions: list[RepairAction]
    repaired: bool


@dataclass(frozen=True)
class PipelineResult:
    ok: bool
    output_format: str
    canonical_text: Optional[str]
    typed_document: Optional[dict[str, Any]]
    issues: list[ValidationIssue]
    repairs: list[RepairAction]
    trace_path: Optional[str]
    report_path: Optional[str]
    manifest_path: Optional[str]
    run_fingerprint: Optional[str]

    @property
    def canonical_json(self) -> Optional[str]:
        if self.output_format == "json":
            return self.canonical_text
        return None
