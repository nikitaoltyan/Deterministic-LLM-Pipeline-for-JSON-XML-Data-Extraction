# Changelog

## 2026-03-09

- Established project design phase and initial documentation set.
- Fixed baseline stack: `Python 3.12`, JSON-only MVP, `library + CLI`.
- Recorded that schemas and real examples are currently absent.
- Recorded future requirement for user-supplied and automatically generated schemas.
- Selected formal constraint strategy: schema-derived grammar artifacts with provider-adapter normalization and mandatory local validation/repair/canonicalization.
- Implemented repository scaffold and Python package layout.
- Implemented deterministic MVP pipeline with preprocessing, prompt building, provider abstraction, JSON parsing, schema validation, repair, canonicalization, strict typing, tracing, and reporting.
- Added mock provider, demo schema, demo fixtures, CLI entrypoint, and invariant tests.
- Added real `openai_compatible` HTTP adapter with environment-based API key handling.
- Added live-run config template, `.env.example`, provider tests, and updated user instructions.
- Implemented schema-derived grammar layer with normalized schema artifacts and provider-specific structured output contracts.
- Switched `openai_compatible` integration from generic `json_object` mode to schema-derived `json_schema` mode when available.
- Added reproducibility layer with run manifest, artifact hashes, and deterministic run fingerprint.
- Added artifact registry layer for schema, grammar, prompt template, repair policy, and canonicalization policy.
- Embedded resolved artifact bundle snapshot into the run manifest.
- Added registry-aware tests and verified the code locally with tests: `8 passed`.

## 2026-03-15

- Added project git workflow rule: commit after each completed development step and push after each major milestone.
- Synchronized core markdown documents with the current implementation stage.
- Updated working frame, user instruction, test plan, and architecture status to reflect grammar layer, reproducibility layer, and artifact registry.

## 2026-03-28

- Completed Stage 1 of the extension roadmap: generalized the core pipeline contracts toward format-neutral orchestration.
- Added explicit `output_format` to run configuration and serialized `Omega`.
- Introduced runtime strategy abstractions for parsing, validation, repair, canonicalization, and strict typing.
- Added JSON strategy implementations behind the new format runtime registry.
- Refactored pipeline, tracing, and CLI to use format-neutral result fields with JSON backward compatibility retained through `canonical_json`.
- Updated configs and tests to reflect the format-aware orchestration layer while preserving the current JSON-track baseline.

## 2026-03-30

- Completed Stage 2 of the extension roadmap: strengthened the normalized JSON schema subset and strict typing model.
- Extended schema normalization to preserve nullable fields, enums, and selected scalar and collection constraints.
- Made unsupported `oneOf`, `anyOf`, and `allOf` constructs fail explicitly in the normalized subset and typing layer.
- Added recursive deterministic repair for nested JSON objects and arrays while keeping repairs policy-bounded.
- Added tests for nested structures, nullable values, enum enforcement, and unsupported union/composition cases.
- Completed Stage 3, substep 1: separated normalized schema artifact construction from grammar artifact construction while preserving current provider-contract behavior.
- Updated artifact registry integration to use explicit normalized-schema and grammar builders.
- Completed Stage 3, substep 2: introduced explicit provider capability profiles for `mock` and `openai_compatible`.
- Completed Stage 3, substep 3: extracted deterministic structured-output strategy resolution into a standalone resolver and simplified provider transport logic.
- Added tests for provider capabilities, structured-output strategy resolution, and the updated provider request path.
