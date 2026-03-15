# Implementation Notes

- The current MVP uses a `mock` provider adapter to keep determinism claims local and testable.
- A real `openai_compatible` adapter is implemented behind the provider contract.
- The grammar layer is now implemented as a normalized schema compiler that emits provider-specific structured output contracts.
- `Omega` is now persisted as a run manifest with deterministic artifact fingerprints.
- Formal artifacts are now resolved through an `ArtifactRegistry` bundle instead of being assembled ad hoc inside the pipeline.
- Performance optimizations are not implemented because they are not an MVP requirement.
- Future work: batch execution, provider capability negotiation, schema induction workflow, and corpus-driven evaluation.
