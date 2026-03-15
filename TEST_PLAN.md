# Test Plan

## Objective

Verify the four invariants and the reproducibility claims of the pipeline.

## Test categories

### Unit tests

- config loading and freezing
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
- repeated runs produce identical traces except for allowed timestamps or run ids
- prompt package hashing remains stable for equal inputs

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
- `I2`: every successful result passes JSON Schema validation
- `I3`: every successful result converts to strict typed objects without lossy coercion
- `I4`: repeated runs under fixed environment configuration are byte-identical after canonicalization

## Constraints to note during implementation

- Provider-backed tests must be isolated from core determinism tests because external APIs may introduce variability.
- Real API integration should be covered by contract tests, but reproducibility claims must rely on frozen fixtures and mock adapters.
