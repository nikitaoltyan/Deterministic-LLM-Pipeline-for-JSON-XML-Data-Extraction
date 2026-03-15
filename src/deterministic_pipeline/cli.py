from __future__ import annotations

import argparse
import json
from pathlib import Path

from deterministic_pipeline.config import load_run_config
from deterministic_pipeline.pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic JSON structuring pipeline")
    parser.add_argument("--config", required=True, help="Path to run configuration JSON file")
    parser.add_argument("--input", required=True, help="Path to source text file")
    parser.add_argument("--output", help="Optional path to write canonical JSON result")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    run_config = load_run_config(Path(args.config))
    text = Path(args.input).read_text(encoding="utf-8")
    result = Pipeline().run(text, run_config)

    if args.output and result.canonical_json is not None:
        Path(args.output).write_text(result.canonical_json + "\n", encoding="utf-8")

    payload = {
        "ok": result.ok,
        "issues": [issue.__dict__ for issue in result.issues],
        "repairs": [repair.__dict__ for repair in result.repairs],
        "trace_path": result.trace_path,
        "report_path": result.report_path,
        "manifest_path": result.manifest_path,
        "run_fingerprint": result.run_fingerprint,
        "canonical_json": result.canonical_json,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
