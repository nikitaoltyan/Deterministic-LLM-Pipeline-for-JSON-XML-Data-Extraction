from __future__ import annotations

import json
from typing import Any

from deterministic_pipeline.artifact_registry import ArtifactBundle
from deterministic_pipeline.config import RunConfig
from deterministic_pipeline.contracts import PipelineResult, RepairAction, ValidationIssue
from deterministic_pipeline.reproducibility import file_sha256, runtime_environment_snapshot, sha256_json, sha256_text, stable_json_dumps


def build_run_manifest(
    run_config: RunConfig,
    prompt_metadata: dict[str, Any],
    normalized_text: str,
    artifact_bundle: ArtifactBundle,
    raw_generation: str,
) -> dict[str, Any]:
    manifest_core = {
        "manifest_version": "v1",
        "input_id": run_config.input_id,
        "schema_id": run_config.schema_id,
        "schema_path": str(run_config.schema_path),
        "omega": run_config.omega(),
        "runtime_environment": runtime_environment_snapshot(),
        "artifact_registry": artifact_bundle.registry_snapshot(),
        "artifacts": {
            "normalized_text_hash": sha256_text(normalized_text),
            "raw_generation_hash": sha256_text(raw_generation),
            "schema_hash": artifact_bundle.schema.fingerprint,
            "source_schema_file_hash": file_sha256(run_config.schema_path),
            "grammar_hash": artifact_bundle.grammar.fingerprint,
            "prompt_template_hash": artifact_bundle.prompt_template.fingerprint,
            "repair_policy_hash": artifact_bundle.repair_policy.fingerprint,
            "canonicalization_policy_hash": artifact_bundle.canonicalization_policy.fingerprint,
            "provider_config_hash": sha256_json(run_config.provider.as_json()),
            "decoding_hash": sha256_json(run_config.decoding.as_json()),
            "trace_policy_hash": sha256_json(
                {
                    "write_trace": run_config.trace_policy.write_trace,
                    "trace_dir": str(run_config.trace_policy.trace_dir),
                    "report_dir": str(run_config.trace_policy.report_dir),
                    "manifest_dir": str(run_config.trace_policy.manifest_dir),
                }
            ),
        },
        "prompt_template": prompt_metadata,
        "grammar_summary": {
            "artifact_version": artifact_bundle.grammar.payload.get("artifact_version"),
            "formalism": artifact_bundle.grammar.payload.get("formalism"),
            "schema_name": artifact_bundle.grammar.payload.get("schema_name"),
            "fingerprint": artifact_bundle.grammar.fingerprint,
        },
    }
    manifest = dict(manifest_core)
    manifest["run_fingerprint"] = sha256_json(manifest_core)
    return manifest


def write_trace_report_and_manifest(
    run_config: RunConfig,
    manifest: dict[str, Any],
    normalized_text: str,
    schema: dict[str, Any],
    grammar: dict[str, Any],
    raw_generation: str,
    issues: list[ValidationIssue],
    repairs: list[RepairAction],
    result: PipelineResult,
) -> tuple:
    if not run_config.trace_policy.write_trace:
        return None, None, None

    trace_dir = run_config.trace_policy.trace_dir
    report_dir = run_config.trace_policy.report_dir
    manifest_dir = run_config.trace_policy.manifest_dir
    trace_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    trace_path = trace_dir / f"{run_config.input_id}.trace.json"
    report_path = report_dir / f"{run_config.input_id}.report.json"
    manifest_path = manifest_dir / f"{run_config.input_id}.manifest.json"

    trace_data = {
        "manifest": manifest,
        "normalized_text": normalized_text,
        "schema": schema,
        "grammar": grammar,
        "raw_generation": raw_generation,
        "issues": [issue.__dict__ for issue in issues],
        "repairs": [repair.__dict__ for repair in repairs],
        "result_ok": result.ok,
        "canonical_json": result.canonical_json,
    }
    report_data = {
        "status": "ok" if result.ok else "failed",
        "input_id": run_config.input_id,
        "repair_count": len(repairs),
        "issue_count": len(issues),
        "run_fingerprint": manifest["run_fingerprint"],
        "omega": run_config.omega(),
    }

    trace_path.write_text(json.dumps(trace_data, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    report_path.write_text(json.dumps(report_data, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    manifest_path.write_text(stable_json_dumps(manifest) + "\n", encoding="utf-8")
    return str(trace_path), str(report_path), str(manifest_path)
