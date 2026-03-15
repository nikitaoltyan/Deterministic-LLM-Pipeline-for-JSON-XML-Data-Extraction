from __future__ import annotations

from pathlib import Path

from deterministic_pipeline.artifact_registry import ArtifactRegistry
from deterministic_pipeline.config import load_run_config


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_artifact_registry_resolves_consistent_bundle() -> None:
    config = load_run_config(PROJECT_ROOT / "configs" / "mock_run.json")

    bundle = ArtifactRegistry().resolve_bundle(config)

    assert bundle.schema.artifact_id == "extraction-record-v1"
    assert bundle.grammar.artifact_id == "extraction-record-v1:schema-derived"
    assert bundle.prompt_template.version == "v1"
    assert bundle.repair_policy.fingerprint
    assert bundle.canonicalization_policy.fingerprint
    snapshot = bundle.registry_snapshot()
    assert snapshot["schema"]["fingerprint"] == bundle.schema.fingerprint
    assert snapshot["grammar"]["fingerprint"] == bundle.grammar.fingerprint
