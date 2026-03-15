# Project Working Frame

## Confirmed decisions

- Language and runtime: `Python 3.12`
- MVP output: `JSON` only
- Interfaces: `library + CLI`
- Offline mode: not required
- Storage: repository-local files only
- Schemas: absent initially, must support user-supplied schemas and future automatic schema generation
- Examples: absent initially, the project must reserve explicit places for future input/output corpora and evaluation datasets
- Performance: not a current constraint; optimization-sensitive areas must be marked for future work

## Working assumptions

1. The first implementation target is a deterministic vertical slice for one generic domain-neutral extraction scenario.
2. The system environment `Omega` is an explicit versioned object and includes model settings, schema version, grammar strategy, repair policy, canonicalization policy, and type policy.
3. Provider APIs may expose different structured-output capabilities; the core pipeline must remain provider-agnostic.
4. Automatic schema generation is a separate deterministic subsystem and should not be coupled to the main extraction pass.
5. Future training or adaptation data will be stored as versioned fixtures and reports inside the repository rather than embedded into pipeline logic.

## Unknowns retained for architecture

- Exact schema induction method for future auto-generation
- Domain ontology strategy once real examples appear
- Cross-provider capability normalization for constrained decoding APIs
- Acceptance criteria for heuristic repair vs. hard failure in ambiguous cases

## Main risks

1. Provider-specific structured-output features differ semantically, which can break reproducibility across model backends.
2. In absence of real documents, an overly domain-specific first schema/model would create rework later.
3. Automatic schema generation can easily become non-deterministic unless treated as a separate controlled workflow.
4. Repair logic may silently become semantic transformation unless its allowed operations are narrowly defined.
5. Determinism can be undermined by hidden provider-side variability even with `temperature=0`.

## Discovery checklist

- [x] Select target runtime and language
- [x] Fix MVP output format
- [x] Determine interface mode
- [x] Clarify provider access model
- [x] Clarify storage model
- [x] Clarify offline requirement
- [x] Clarify performance priority
- [x] Confirm absence of initial schemas and examples
- [x] Record need for future schema generation and corpus growth

## Architecture checklist

- [ ] Define environment configuration model `Omega`
- [ ] Define module boundaries for all pipeline stages
- [ ] Define provider adapter contract
- [ ] Define schema registry and versioning rules
- [ ] Define grammar artifact strategy
- [ ] Define deterministic repair policy
- [ ] Define canonical JSON serialization rules
- [ ] Define typed model derivation rules
- [ ] Define trace and run-report format
- [ ] Map every module to invariants `I1-I4`

## Implementation checklist

- [ ] Materialize repository structure
- [ ] Create base Python package and CLI entrypoint
- [ ] Implement configuration loading and serialization
- [ ] Implement pipeline contracts and result envelopes
- [ ] Implement schema registry and JSON Schema validation
- [ ] Implement provider abstraction and mock adapter
- [ ] Implement grammar strategy abstraction
- [ ] Implement deterministic repair engine
- [ ] Implement canonicalizer and type layer
- [ ] Implement trace writer and run reports
- [ ] Add invariant tests and golden tests

## Stage readiness criteria

### Stage A - Architecture approval

- Assumptions, risks, and architecture are documented
- Formal constraint strategy is selected
- User approves the proposed design

### Stage B - Repository scaffold

- Project tree exists
- Tooling and dependency management are configured
- Base docs and config schema are present

### Stage C - MVP vertical slice

- A text input can pass through the full pipeline
- Final output is valid JSON and typed
- Run metadata and traces are persisted
- Determinism tests exist for fixed fixtures

### Stage D - Stabilization

- Negative tests, repair tests, and golden tests exist
- Provider abstraction supports at least one real adapter and one mock adapter
- Extension points for future schema generation and corpora are documented
