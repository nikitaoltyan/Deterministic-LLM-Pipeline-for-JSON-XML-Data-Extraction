# Deterministic LLM Structuring Pipeline

Research-grade project for deterministic transformation of unstructured text into strictly valid structured representations and typed application objects.

## Status

The project has an implemented JSON-track MVP and a format-neutral core orchestration layer with:

- format-aware run configuration
- format runtime registry for parser, validator, repair, canonicalization, and typing strategies
- richer normalized JSON schema subset with nullable and enum support
- recursive deterministic repair for nested JSON objects and arrays
- deterministic local pipeline execution
- mock provider adapter
- openai-compatible live adapter
- anthropic-compatible live adapter
- explicit provider registry for adapter construction
- separated normalized-schema and grammar artifact builders
- explicit provider capability profiles
- deterministic structured-output strategy resolver
- stabilized provider transport layer with shared request and metadata helpers
- reproducibility layer with manifests and run fingerprints
- artifact registry for formal pipeline artifacts

## Scope of MVP

- Output formats:
  - implemented: JSON
  - planned through the generalized core: XML
- Runtime: Python 3.12
- Interfaces: library + CLI
- LLM access: remote API adapters
- Providers to support via abstraction: OpenAI, Anthropic, Qwen, DeepSeek and compatible APIs
- Storage: repository-local files for configs, fixtures, traces, reports, and golden outputs

## Core invariants

- `I1`: syntactic structured-output validity
- `I2`: schema validity
- `I3`: strict typing
- `I4`: determinism under fixed environment configuration

## Key documents

- `SPEC.md` - project assumptions, checklists, risks, staged plan
- `ARCHITECTURE.md` - approved system architecture
- `TEST_PLAN.md` - verification strategy for invariants
- `CHANGELOG.md` - project decisions and milestones

## Proposed repository layout

```text
docs/
examples/
schemas/
grammars/
configs/
traces/
reports/
goldens/
src/
tests/
```

The layout is now partially materialized for the MVP scaffold.

## Verification

Local verification completed:

- `PYTHONPATH=src pytest -q` -> `21 passed`
- mock CLI path verified successfully

Live external API verification is now supported by the codebase, but still must be run by the user with a real API key because network execution is not available in the current agent environment.

## Git workflow

Project development now follows this repository rule:

- after each completed development step, create a descriptive git commit
- do not push automatically after a milestone
- push to the GitHub remote only after an explicit user instruction
- before finishing the step, synchronize markdown documentation with the implementation

Reproducibility layer now includes:

- run manifest serialization
- run fingerprint
- schema, grammar, prompt-template, repair-policy, and config hashes
- artifact registry snapshot with versioned bundle resolution
