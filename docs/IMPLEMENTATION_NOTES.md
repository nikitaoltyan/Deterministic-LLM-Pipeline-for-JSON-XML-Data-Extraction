# Implementation Notes

- The current MVP uses a `mock` provider adapter to keep determinism claims local and testable.
- A real `openai_compatible` adapter is implemented behind the provider contract.
- The core pipeline orchestration is now format-aware and delegates parser, validator, repair, canonicalization, and typing through a runtime strategy layer.
- The currently implemented strategy set is JSON-only, but the contract layer now reserves `xml` as a first-class target format identifier for later implementation.
- The grammar layer is now implemented as a normalized schema compiler that emits provider-specific structured output contracts.
- The normalized schema artifact and grammar artifact are now built through separate explicit builder steps, which prepares the codebase for later capability modeling and strategy resolution.
- Provider creation is now routed through an explicit registry rather than hardcoded branching in the factory path.
- Provider capabilities are now represented explicitly rather than inferred indirectly inside provider adapters.
- Structured-output strategy resolution is now handled by a separate deterministic resolver instead of being embedded in transport code.
- The normalized JSON schema subset now supports nullable fields, enums, nested objects, arrays, and selected scalar and collection constraints.
- The current typing layer rejects unsupported `oneOf`/`anyOf`/`allOf` constructs explicitly rather than coercing them ambiguously.
- The repair layer now applies deterministic safe transformations recursively inside nested objects and arrays.
- `Omega` is now persisted as a run manifest with deterministic artifact fingerprints.
- Formal artifacts are now resolved through an `ArtifactRegistry` bundle instead of being assembled ad hoc inside the pipeline.
- Performance optimizations are not implemented because they are not an MVP requirement.
- Future work: batch execution, provider capability negotiation, schema induction workflow, and corpus-driven evaluation.
