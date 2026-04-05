from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from deterministic_pipeline.config import RunConfig
from deterministic_pipeline.prompting import get_prompt_template_spec
from deterministic_pipeline.reproducibility import sha256_json
from deterministic_pipeline.schema_tools import build_json_grammar_artifact, load_schema, normalize_json_schema_artifact


@dataclass(frozen=True)
class ArtifactRecord:
    kind: str
    artifact_id: str
    version: str
    fingerprint: str
    source: str
    payload: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ArtifactBundle:
    schema: ArtifactRecord
    grammar: ArtifactRecord
    prompt_template: ArtifactRecord
    repair_policy: ArtifactRecord
    canonicalization_policy: ArtifactRecord

    def registry_snapshot(self) -> dict[str, Any]:
        return {
            "schema": _record_snapshot(self.schema),
            "grammar": _record_snapshot(self.grammar),
            "prompt_template": _record_snapshot(self.prompt_template),
            "repair_policy": _record_snapshot(self.repair_policy),
            "canonicalization_policy": _record_snapshot(self.canonicalization_policy),
        }


class ArtifactRegistry:
    def resolve_bundle(self, run_config: RunConfig) -> ArtifactBundle:
        schema_artifact = self.resolve_schema(run_config)
        grammar_artifact = self.resolve_grammar(run_config, schema_artifact)
        prompt_template_artifact = self.resolve_prompt_template(run_config)
        repair_policy_artifact = self.resolve_repair_policy(run_config)
        canonicalization_artifact = self.resolve_canonicalization_policy(run_config)
        return ArtifactBundle(
            schema=schema_artifact,
            grammar=grammar_artifact,
            prompt_template=prompt_template_artifact,
            repair_policy=repair_policy_artifact,
            canonicalization_policy=canonicalization_artifact,
        )

    def resolve_schema(self, run_config: RunConfig) -> ArtifactRecord:
        payload = load_schema(run_config.schema_path)
        return ArtifactRecord(
            kind="schema",
            artifact_id=run_config.schema_id,
            version="v1",
            fingerprint=sha256_json(payload),
            source=str(run_config.schema_path),
            payload=payload,
            metadata={"path": str(run_config.schema_path)},
        )

    def resolve_grammar(self, run_config: RunConfig, schema_artifact: ArtifactRecord) -> ArtifactRecord:
        normalized_schema_artifact = normalize_json_schema_artifact(schema_artifact.payload, schema_id=run_config.schema_id)
        payload = build_json_grammar_artifact(normalized_schema_artifact)
        return ArtifactRecord(
            kind="grammar",
            artifact_id="{0}:{1}".format(run_config.schema_id, run_config.grammar_strategy),
            version=run_config.grammar_version,
            fingerprint=payload["fingerprint"],
            source="schema-derived",
            payload=payload,
            metadata={"grammar_strategy": run_config.grammar_strategy},
        )

    def resolve_prompt_template(self, run_config: RunConfig) -> ArtifactRecord:
        payload = get_prompt_template_spec(run_config.prompt_template_version, run_config.output_format)
        return ArtifactRecord(
            kind="prompt_template",
            artifact_id="prompt-template",
            version=run_config.prompt_template_version,
            fingerprint=sha256_json(payload),
            source="builtin",
            payload=payload,
            metadata={},
        )

    def resolve_repair_policy(self, run_config: RunConfig) -> ArtifactRecord:
        payload = run_config.repair_policy.as_json()
        return ArtifactRecord(
            kind="repair_policy",
            artifact_id="repair-policy",
            version="v1",
            fingerprint=sha256_json(payload),
            source="run-config",
            payload=payload,
            metadata={},
        )

    def resolve_canonicalization_policy(self, run_config: RunConfig) -> ArtifactRecord:
        payload = {
            "ensure_ascii": run_config.canonicalization.ensure_ascii,
            "sort_keys": run_config.canonicalization.sort_keys,
            "separators": list(run_config.canonicalization.separators),
        }
        return ArtifactRecord(
            kind="canonicalization_policy",
            artifact_id="canonicalization-policy",
            version="v1",
            fingerprint=sha256_json(payload),
            source="run-config",
            payload=payload,
            metadata={},
        )


def _record_snapshot(record: ArtifactRecord) -> dict[str, Any]:
    return {
        "kind": record.kind,
        "artifact_id": record.artifact_id,
        "version": record.version,
        "fingerprint": record.fingerprint,
        "source": record.source,
        "metadata": record.metadata,
    }
