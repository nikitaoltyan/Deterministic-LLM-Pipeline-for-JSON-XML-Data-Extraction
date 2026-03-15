# User Instruction

## Current state

The project now supports:

- deterministic local execution with the `mock` provider,
- real API execution through an `openai_compatible` provider adapter for endpoints compatible with `/v1/chat/completions`.

## What to add for real API providers

Add credentials through environment variables, not directly into tracked source files.

Recommended environment variables:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `QWEN_API_KEY`
- `DEEPSEEK_API_KEY`
- `OPENAI_BASE_URL` if using an OpenAI-compatible endpoint

Planned config locations:

- provider runtime config: `configs/*.json`
- schema files: `schemas/*.json`
- input examples: `examples/inputs/*`
- expected outputs or goldens: `examples/expected/*`, `goldens/*`

Do not store secrets in:

- `configs/*.json`
- source files under `src/`
- test files under `tests/`

Minimal environment setup:

```bash
export OPENAI_API_KEY='your_real_key'
export OPENAI_BASE_URL='https://api.openai.com/v1'
```

If you use the default OpenAI endpoint, `OPENAI_BASE_URL` is optional.

## What is already in the repository

- runnable pipeline package: `src/deterministic_pipeline/`
- demo config: `configs/mock_run.json`
- demo schema: `schemas/extraction_record.schema.json`
- flood schema: `schemas/flood_evacuation.schema.json`
- demo input: `examples/inputs/demo.txt`
- flood input example: `examples/inputs/flood_example.txt`
- mock provider output fixture: `fixtures/mock_generation_valid.json`
- expected canonical output: `goldens/demo.golden.json`
- real API config template: `configs/openai_run.example.json`
- flood live config template: `configs/openai_flood_run.example.json`
- env template: `.env.example`

## How to run the MVP

Run from the project root:

```bash
PYTHONPATH=src python3 -m deterministic_pipeline.cli \
  --config configs/mock_run.json \
  --input examples/inputs/demo.txt
```

If you want to also save the final canonical JSON into a file:

```bash
PYTHONPATH=src python3 -m deterministic_pipeline.cli \
  --config configs/mock_run.json \
  --input examples/inputs/demo.txt \
  --output reports/demo-output.json
```

## How to run a real OpenAI-compatible check

1. Export your API key:

```bash
export OPENAI_API_KEY='your_real_key'
```

2. Copy the example config and adjust the model if needed:

```bash
cp configs/openai_run.example.json configs/openai_run.json
```

3. Run the live check:

```bash
PYTHONPATH=src python3 -m deterministic_pipeline.cli \
  --config configs/openai_run.json \
  --input examples/inputs/demo.txt \
  --output reports/openai-output.json
```

If you use a different OpenAI-compatible provider, change in `configs/openai_run.json`:

- `provider.api_base_url`
- `provider.model`
- optionally `provider.api_key_env`
- optionally `provider.use_json_response_format`
- optionally `provider.structured_output_strategy`

Structured output strategies:

- `auto`: use schema-derived provider contract when available, otherwise fallback
- `json_schema`: force provider-side schema contract
- `json_object`: request generic JSON object mode
- `prompt_only`: disable provider-side structured output and rely on prompt plus local validation

## Flood scenario schema

The repository now contains a dedicated schema for flood/evacuation extraction:

- `schemas/flood_evacuation.schema.json`

Expected output fields:

- `time` as string
- `water_level_rise` as integer
- `rise_speed` as integer
- `resident_count` as integer
- `evacuation_start_time` as string

To run this scenario:

1. Create your text file, for example:

- `examples/inputs/my_flood_text.txt`

2. Copy the flood config template:

```bash
cp configs/openai_flood_run.example.json configs/openai_flood_run.json
```

3. Run:

```bash
PYTHONPATH=src python3 -m deterministic_pipeline.cli \
  --config configs/openai_flood_run.json \
  --input examples/inputs/my_flood_text.txt \
  --output reports/flood-output.json
```

You can also test the pipeline structure with the sample input:

```bash
PYTHONPATH=src python3 -m deterministic_pipeline.cli \
  --config configs/openai_flood_run.json \
  --input examples/inputs/flood_example.txt \
  --output reports/flood-output.json
```

## How to run tests

```bash
PYTHONPATH=src pytest -q
```

Expected result at the current stage:

- `7 passed`

## Where to look at the results

After a successful CLI run, inspect:

- trace: `traces/demo-run.trace.json`
- report: `reports/demo-run.report.json`
- manifest: `manifests/demo-run.manifest.json`
- optional saved output: `reports/demo-output.json`

For a live API run, inspect:

- trace: `traces/openai-live-run.trace.json`
- report: `reports/openai-live-run.report.json`
- manifest: `manifests/openai-live-run.manifest.json`
- optional saved output: `reports/openai-output.json`

For the flood scenario, inspect:

- trace: `traces/flood-live-run.trace.json`
- report: `reports/flood-live-run.report.json`
- manifest: `manifests/flood-live-run.manifest.json`
- output: `reports/flood-output.json`

The CLI also prints a JSON summary to stdout with:

- `ok`
- `issues`
- `repairs`
- `trace_path`
- `report_path`
- `manifest_path`
- `run_fingerprint`
- `canonical_json`

The manifest now also includes an `artifact_registry` section, where you can inspect:

- which schema artifact was used
- which grammar artifact was derived from it
- which prompt template version was used
- which repair policy and canonicalization policy were active
- fingerprints and sources for all of these artifacts

## How to evaluate that the system works

The current MVP should be considered working if all of the following are true:

1. The test command finishes with `3 passed`.
2. The CLI command exits successfully.
3. The CLI output contains `"ok": true`.
4. The file `traces/demo-run.trace.json` is created.
5. The file `reports/demo-run.report.json` is created.
6. The file `manifests/demo-run.manifest.json` is created.
7. The final canonical JSON matches `goldens/demo.golden.json`.
8. The CLI output contains a non-empty `run_fingerprint`.
9. The repair log shows deterministic cleanup of the mock response:
   - unknown field removed
   - default field inserted
   - string-to-integer normalization applied
   - string-to-boolean normalization applied

The live OpenAI-compatible path should be considered working if all of the following are true:

1. The live CLI command exits successfully.
2. The CLI output contains `"ok": true`.
3. The file `traces/openai-live-run.trace.json` is created.
4. The file `reports/openai-live-run.report.json` is created.
5. The file `manifests/openai-live-run.manifest.json` is created.
6. The saved output is valid JSON.
7. The trace and manifest contain the exact provider/model configuration used for the run.
8. Repeating the same run with the same config produces a semantically valid result each time.

Important note:

- external APIs can still introduce variability even with `temperature=0`,
- therefore real-provider runs demonstrate integration correctness,
- while strict determinism claims are still grounded primarily in local fixtures and mock-based regression tests.

## How to interpret the current demo

The fixture `fixtures/mock_generation_valid.json` intentionally contains a not-yet-valid candidate:

- `priority` is a string instead of integer
- `published` is a string instead of boolean
- `extra` is an unknown field
- `tags` is missing

The pipeline proves the deterministic control path by:

1. parsing provider output as JSON,
2. validating it against the schema,
3. repairing only policy-allowed issues,
4. canonicalizing the final JSON,
5. converting it into a strict typed document,
6. writing trace, report, and manifest artifacts.

## How to add your own demo case

1. Create a new input text file under `examples/inputs/`.
2. Create or update a JSON Schema under `schemas/`.
3. Create a new config under `configs/` pointing to that schema.
4. Point `mock_response_path` to a fixture under `fixtures/`.
5. Run the CLI with the new config and input.
6. Save the successful canonical output into `goldens/` for future regression tests.

## Important limitation

At this stage, the repository proves:

- repository structure,
- deterministic local pipeline behavior,
- real OpenAI-compatible HTTP integration,
- schema validation,
- bounded repair,
- canonicalization,
- strict typing,
- tracing and reporting.

It does not yet prove:

- cross-provider reproducibility,
- live constrained decoding over external APIs.
