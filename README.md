# Deterministic LLM Structuring Pipeline

Research-grade project for deterministic transformation of unstructured text into strictly valid structured JSON and typed application objects.

## Status

The project has an implemented MVP vertical slice with a deterministic local pipeline and a mock provider adapter.

## Scope of MVP

- Output format: JSON only
- Runtime: Python 3.12
- Interfaces: library + CLI
- LLM access: remote API adapters
- Providers to support via abstraction: OpenAI, Anthropic, Qwen, DeepSeek and compatible APIs
- Storage: repository-local files for configs, fixtures, traces, reports, and golden outputs

## Core invariants

- `I1`: syntactic JSON validity
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

- `PYTHONPATH=src pytest -q` -> `8 passed`
- mock CLI path verified successfully

Live external API verification is now supported by the codebase, but still must be run by the user with a real API key because network execution is not available in the current agent environment.

Reproducibility layer now includes:

- run manifest serialization
- run fingerprint
- schema, grammar, prompt-template, repair-policy, and config hashes
- artifact registry snapshot with versioned bundle resolution
