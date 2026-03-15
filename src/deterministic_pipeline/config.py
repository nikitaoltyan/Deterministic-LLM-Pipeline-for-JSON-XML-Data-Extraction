from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Tuple


@dataclass(frozen=True)
class DecodingConfig:
    temperature: float = 0.0
    top_p: float = 1.0
    max_output_tokens: int = 512

    def as_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RepairPolicy:
    max_iterations: int = 1
    drop_unknown_fields: bool = True
    normalize_scalar_strings: bool = True
    apply_schema_defaults: bool = True

    def as_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CanonicalizationPolicy:
    ensure_ascii: bool = False
    sort_keys: bool = True
    separators: Tuple[str, str] = (",", ":")


@dataclass(frozen=True)
class TracePolicy:
    write_trace: bool = True
    trace_dir: Path = Path("traces")
    report_dir: Path = Path("reports")
    manifest_dir: Path = Path("manifests")


@dataclass(frozen=True)
class ProviderConfig:
    name: str = "mock"
    model: str = "mock-json-generator-v1"
    api_base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    request_timeout_seconds: int = 60
    use_json_response_format: bool = True
    structured_output_strategy: str = "auto"

    def as_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RunConfig:
    schema_id: str
    schema_path: Path
    provider: ProviderConfig = field(default_factory=ProviderConfig)
    decoding: DecodingConfig = field(default_factory=DecodingConfig)
    repair_policy: RepairPolicy = field(default_factory=RepairPolicy)
    canonicalization: CanonicalizationPolicy = field(default_factory=CanonicalizationPolicy)
    trace_policy: TracePolicy = field(default_factory=TracePolicy)
    prompt_template_version: str = "v1"
    grammar_strategy: str = "schema-derived"
    grammar_version: str = "v1"
    type_model_version: str = "json-schema-subset-v1"
    input_id: str = "adhoc-input"
    mock_response_path: Optional[Path] = None

    def omega(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "schema_path": str(self.schema_path),
            "provider": self.provider.as_json(),
            "decoding": self.decoding.as_json(),
            "repair_policy": self.repair_policy.as_json(),
            "canonicalization": {
                "ensure_ascii": self.canonicalization.ensure_ascii,
                "sort_keys": self.canonicalization.sort_keys,
                "separators": list(self.canonicalization.separators),
            },
            "trace_policy": {
                "write_trace": self.trace_policy.write_trace,
                "trace_dir": str(self.trace_policy.trace_dir),
                "report_dir": str(self.trace_policy.report_dir),
                "manifest_dir": str(self.trace_policy.manifest_dir),
            },
            "prompt_template_version": self.prompt_template_version,
            "grammar_strategy": self.grammar_strategy,
            "grammar_version": self.grammar_version,
            "type_model_version": self.type_model_version,
            "input_id": self.input_id,
            "mock_response_path": str(self.mock_response_path) if self.mock_response_path else None,
        }


def load_run_config(path: Path) -> RunConfig:
    import json

    data = json.loads(path.read_text(encoding="utf-8"))
    provider_data = data.get("provider", {})
    decoding_data = data.get("decoding", {})
    repair_data = data.get("repair_policy", {})
    canonicalization_data = data.get("canonicalization", {})
    trace_data = data.get("trace_policy", {})

    return RunConfig(
        schema_id=data["schema_id"],
        schema_path=Path(data["schema_path"]),
        provider=ProviderConfig(**provider_data),
        decoding=DecodingConfig(**decoding_data),
        repair_policy=RepairPolicy(**repair_data),
        canonicalization=CanonicalizationPolicy(**canonicalization_data),
        trace_policy=TracePolicy(
            write_trace=trace_data.get("write_trace", True),
            trace_dir=Path(trace_data.get("trace_dir", "traces")),
            report_dir=Path(trace_data.get("report_dir", "reports")),
            manifest_dir=Path(trace_data.get("manifest_dir", "manifests")),
        ),
        prompt_template_version=data.get("prompt_template_version", "v1"),
        grammar_strategy=data.get("grammar_strategy", "schema-derived"),
        grammar_version=data.get("grammar_version", "v1"),
        type_model_version=data.get("type_model_version", "json-schema-subset-v1"),
        input_id=data.get("input_id", "adhoc-input"),
        mock_response_path=Path(data["mock_response_path"]) if data.get("mock_response_path") else None,
    )
