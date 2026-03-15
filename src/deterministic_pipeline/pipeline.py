from __future__ import annotations

from deterministic_pipeline.artifact_registry import ArtifactRegistry
from deterministic_pipeline.canonicalize import canonicalize_json
from deterministic_pipeline.config import RunConfig
from deterministic_pipeline.contracts import GenerationRequest, PipelineResult, ValidationIssue
from deterministic_pipeline.formal_gate import parse_json_document
from deterministic_pipeline.preprocess import normalize_text
from deterministic_pipeline.prompting import build_prompt
from deterministic_pipeline.providers import make_provider
from deterministic_pipeline.repair import repair_document
from deterministic_pipeline.tracing import build_run_manifest, write_trace_report_and_manifest
from deterministic_pipeline.typing import TypeValidationError, coerce_typed_document
from deterministic_pipeline.validator import validate_document


class Pipeline:
    def run(self, text: str, run_config: RunConfig) -> PipelineResult:
        normalized_text = normalize_text(text)
        artifact_bundle = ArtifactRegistry().resolve_bundle(run_config)
        schema = artifact_bundle.schema.payload
        grammar = artifact_bundle.grammar.payload
        prompt = build_prompt(normalized_text, schema, grammar, artifact_bundle.prompt_template.payload)
        provider = make_provider(run_config.provider, mock_response_path=run_config.mock_response_path)
        request = GenerationRequest(
            prompt=prompt,
            provider_name=run_config.provider.name,
            model=run_config.provider.model,
            decoding=run_config.decoding.as_json(),
            omega=run_config.omega(),
        )
        raw_generation = provider.generate(request)
        manifest = build_run_manifest(
            run_config=run_config,
            prompt_metadata=prompt.template_metadata,
            normalized_text=normalized_text,
            artifact_bundle=artifact_bundle,
            raw_generation=raw_generation.text,
        )

        candidate, issues = parse_json_document(raw_generation.text)
        repairs = []
        if candidate is None:
            result = PipelineResult(
                ok=False,
                canonical_json=None,
                typed_document=None,
                issues=issues,
                repairs=repairs,
                trace_path=None,
                report_path=None,
                manifest_path=None,
                run_fingerprint=manifest["run_fingerprint"],
            )
            trace_path, report_path, manifest_path = write_trace_report_and_manifest(
                run_config, manifest, normalized_text, schema, grammar, raw_generation.text, issues, repairs, result
            )
            return PipelineResult(**{**result.__dict__, "trace_path": trace_path, "report_path": report_path, "manifest_path": manifest_path})

        issues = validate_document(candidate, schema)
        for _ in range(run_config.repair_policy.max_iterations):
            if not issues:
                break
            repair_result = repair_document(candidate, schema, run_config.repair_policy)
            if not repair_result.repaired:
                break
            candidate = repair_result.document
            repairs.extend(repair_result.actions)
            issues = validate_document(candidate, schema)

        if issues:
            result = PipelineResult(
                ok=False,
                canonical_json=None,
                typed_document=None,
                issues=issues,
                repairs=repairs,
                trace_path=None,
                report_path=None,
                manifest_path=None,
                run_fingerprint=manifest["run_fingerprint"],
            )
            trace_path, report_path, manifest_path = write_trace_report_and_manifest(
                run_config, manifest, normalized_text, schema, grammar, raw_generation.text, issues, repairs, result
            )
            return PipelineResult(**{**result.__dict__, "trace_path": trace_path, "report_path": report_path, "manifest_path": manifest_path})

        try:
            typed_document = coerce_typed_document(candidate, schema)
        except TypeValidationError as exc:
            type_issue = ValidationIssue(path="$", message=str(exc), validator="strict_typing")
            result = PipelineResult(
                ok=False,
                canonical_json=None,
                typed_document=None,
                issues=[type_issue],
                repairs=repairs,
                trace_path=None,
                report_path=None,
                manifest_path=None,
                run_fingerprint=manifest["run_fingerprint"],
            )
            trace_path, report_path, manifest_path = write_trace_report_and_manifest(
                run_config, manifest, normalized_text, schema, grammar, raw_generation.text, [type_issue], repairs, result
            )
            return PipelineResult(**{**result.__dict__, "trace_path": trace_path, "report_path": report_path, "manifest_path": manifest_path})

        canonical_json = canonicalize_json(candidate, run_config.canonicalization)
        result = PipelineResult(
            ok=True,
            canonical_json=canonical_json,
            typed_document=typed_document,
            issues=[],
            repairs=repairs,
            trace_path=None,
            report_path=None,
            manifest_path=None,
            run_fingerprint=manifest["run_fingerprint"],
        )
        trace_path, report_path, manifest_path = write_trace_report_and_manifest(
            run_config, manifest, normalized_text, schema, grammar, raw_generation.text, [], repairs, result
        )
        return PipelineResult(**{**result.__dict__, "trace_path": trace_path, "report_path": report_path, "manifest_path": manifest_path})
