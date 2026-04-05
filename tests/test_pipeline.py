from __future__ import annotations

import json
from pathlib import Path

from deterministic_pipeline.config import load_run_config
from deterministic_pipeline.pipeline import Pipeline


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_pipeline_end_to_end_success() -> None:
    config = load_run_config(PROJECT_ROOT / "configs" / "mock_run.json")
    text = (PROJECT_ROOT / "examples" / "inputs" / "demo.txt").read_text(encoding="utf-8")

    result = Pipeline().run(text, config)

    assert result.ok is True
    assert result.output_format == "json"
    assert result.canonical_text == (PROJECT_ROOT / "goldens" / "demo.golden.json").read_text(encoding="utf-8").strip()
    assert result.canonical_json == (PROJECT_ROOT / "goldens" / "demo.golden.json").read_text(encoding="utf-8").strip()
    assert result.typed_document == {
        "title": "Demo title",
        "summary": "Short summary",
        "priority": 2,
        "published": True,
        "tags": [],
    }
    assert len(result.repairs) == 4
    assert result.run_fingerprint is not None
    assert result.manifest_path is not None
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    assert manifest["run_fingerprint"] == result.run_fingerprint
    assert manifest["grammar_summary"]["fingerprint"]


def test_pipeline_is_deterministic_for_same_input() -> None:
    config = load_run_config(PROJECT_ROOT / "configs" / "mock_run.json")
    text = (PROJECT_ROOT / "examples" / "inputs" / "demo.txt").read_text(encoding="utf-8")

    first = Pipeline().run(text, config)
    second = Pipeline().run(text, config)

    assert first.output_format == second.output_format == "json"
    assert first.canonical_text == second.canonical_text
    assert first.canonical_json == second.canonical_json
    assert first.typed_document == second.typed_document
    assert first.run_fingerprint == second.run_fingerprint


def test_pipeline_fails_on_non_repairable_output(tmp_path: Path) -> None:
    bad_mock = tmp_path / "bad.json"
    bad_mock.write_text('{"title":"Demo","summary":"Short","priority":"NaN","published":"maybe"}', encoding="utf-8")

    config_data = json.loads((PROJECT_ROOT / "configs" / "mock_run.json").read_text(encoding="utf-8"))
    config_data["input_id"] = "failure-run"
    config_data["mock_response_path"] = str(bad_mock)
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    config = load_run_config(config_path)
    text = (PROJECT_ROOT / "examples" / "inputs" / "demo.txt").read_text(encoding="utf-8")

    result = Pipeline().run(text, config)

    assert result.ok is False
    assert any(issue.validator in {"type", "strict_typing"} for issue in result.issues)


def test_run_manifest_contains_stable_artifact_hashes() -> None:
    config = load_run_config(PROJECT_ROOT / "configs" / "mock_run.json")
    text = (PROJECT_ROOT / "examples" / "inputs" / "demo.txt").read_text(encoding="utf-8")

    result = Pipeline().run(text, config)
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))

    assert manifest["manifest_version"] == "v1"
    assert manifest["omega"]["trace_policy"]["manifest_dir"] == "manifests"
    assert manifest["prompt_template"]["template_version"] == "v1"
    assert manifest["artifacts"]["prompt_template_hash"]
    assert manifest["artifacts"]["repair_policy_hash"]
    assert manifest["artifacts"]["grammar_hash"]
    assert manifest["artifacts"]["source_schema_file_hash"]
    assert manifest["artifact_registry"]["schema"]["artifact_id"] == "extraction-record-v1"
    assert manifest["artifact_registry"]["grammar"]["artifact_id"] == "extraction-record-v1:schema-derived"


def test_pipeline_end_to_end_success_xml() -> None:
    config = load_run_config(PROJECT_ROOT / "configs" / "mock_run_xml.json")
    text = (PROJECT_ROOT / "examples" / "inputs" / "demo.txt").read_text(encoding="utf-8")

    result = Pipeline().run(text, config)

    assert result.ok is True
    assert result.output_format == "xml"
    assert result.canonical_text == (PROJECT_ROOT / "goldens" / "demo.golden.xml").read_text(encoding="utf-8").strip()
    assert result.canonical_json is None
    assert result.typed_document == {
        "tag": "record",
        "attributes": {"priority": "2", "published": "true"},
        "children": [
            {"tag": "title", "text": "Demo title"},
            {"tag": "summary", "text": "Short summary"},
            {"tag": "tags"},
        ],
    }
    manifest = json.loads(Path(result.manifest_path).read_text(encoding="utf-8"))
    assert manifest["omega"]["output_format"] == "xml"
    assert manifest["prompt_template"]["template_version"] == "v1"
    assert manifest["artifact_registry"]["prompt_template"]["fingerprint"]
