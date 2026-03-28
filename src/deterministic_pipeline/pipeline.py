from __future__ import annotations

from deterministic_pipeline.artifact_registry import ArtifactRegistry
from deterministic_pipeline.config import RunConfig
from deterministic_pipeline.contracts import GenerationRequest, PipelineResult, ValidationIssue
from deterministic_pipeline.formats import map_type_error
from deterministic_pipeline.preprocess import normalize_text
from deterministic_pipeline.prompting import build_prompt
from deterministic_pipeline.providers import make_provider
from deterministic_pipeline.runtime_registry import get_format_runtime
from deterministic_pipeline.tracing import build_run_manifest, write_trace_report_and_manifest
from deterministic_pipeline.typing import TypeValidationError


class Pipeline:
    def run(self, text: str, run_config: RunConfig) -> PipelineResult:
        normalized_text = normalize_text(text)
        format_runtime = get_format_runtime(run_config.output_format)
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

        candidate, issues = format_runtime.parser.parse(raw_generation.text)
        repairs = []
        if candidate is None:
            result = PipelineResult(
                ok=False,
                output_format=run_config.output_format.value,
                canonical_text=None,
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

        issues = format_runtime.validator.validate(candidate, schema)
        for _ in range(run_config.repair_policy.max_iterations):
            if not issues:
                break
            repair_result = format_runtime.repairer.repair(candidate, schema, run_config.repair_policy)
            if not repair_result.repaired:
                break
            candidate = repair_result.document
            repairs.extend(repair_result.actions)
            issues = format_runtime.validator.validate(candidate, schema)

        if issues:
            result = PipelineResult(
                ok=False,
                output_format=run_config.output_format.value,
                canonical_text=None,
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
            typed_document = format_runtime.type_mapper.map_to_typed(candidate, schema)
        except TypeValidationError as exc:
            type_issue = map_type_error(exc)
            result = PipelineResult(
                ok=False,
                output_format=run_config.output_format.value,
                canonical_text=None,
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

        canonical_text = format_runtime.canonicalizer.canonicalize(candidate, run_config.canonicalization)
        result = PipelineResult(
            ok=True,
            output_format=run_config.output_format.value,
            canonical_text=canonical_text,
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
