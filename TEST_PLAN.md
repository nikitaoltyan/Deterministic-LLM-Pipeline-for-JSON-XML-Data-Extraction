# Test Plan

## Objective

Verify the four invariants and the reproducibility claims of the pipeline.

## Current coverage status

Implemented tests currently cover:

- end-to-end success path
- deterministic repeated run for fixed input/config
- non-repairable failure path
- format-neutral pipeline result contract on the JSON track
- grammar compiler output
- openai-compatible provider contract request building
- missing API key handling
- artifact registry bundle resolution

Current local baseline:

- `PYTHONPATH=src pytest -q` -> `8 passed`

## Test categories

### Unit tests

- config loading and freezing
- format runtime resolution
- prompt building determinism
- schema validation behavior
- repair rule determinism
- canonical JSON serialization
- type conversion strictness

### Integration tests

- end-to-end pipeline run with mock provider output
- pipeline run with valid candidate
- pipeline run with repairable candidate
- pipeline run with non-repairable candidate

### Determinism tests

- repeated runs with identical input and identical `Omega` produce byte-identical output
- repeated runs produce identical `run_fingerprint`
- prompt package hashing remains stable for equal inputs
- manifest artifact hashes remain stable for equal inputs

### Negative tests

- malformed JSON from provider
- schema-mismatched JSON
- prohibited unknown fields
- ambiguous type coercions

### Repair tests

- deterministic insertion of defaults where policy allows
- deterministic field pruning where policy allows
- repair refusal for semantic ambiguity

### Golden tests

- canonical output matches stored golden files
- trace summaries match expected stage outcomes

### Schema stress tests

- nested objects
- arrays of objects
- enums
- unions if introduced in the schema model

## Acceptance criteria

- `I1`: every successful result parses as JSON without error
- current implemented path: JSON
- `I2`: every successful result passes JSON Schema validation
- `I3`: every successful result converts to strict typed objects without lossy coercion
- `I4`: repeated runs under fixed environment configuration are byte-identical after canonicalization

## Known gaps

- corpus-level golden tests are still limited
- live API reproducibility is not treated as a hard determinism proof
- batch evaluation and stress harnesses are not implemented yet

## Constraints to note during implementation

- Provider-backed tests must be isolated from core determinism tests because external APIs may introduce variability.
- Real API integration should be covered by contract tests, but reproducibility claims must rely on frozen fixtures and mock adapters.
- As new formats are added, the same invariant-oriented test structure must be preserved behind the format-neutral orchestration layer.
