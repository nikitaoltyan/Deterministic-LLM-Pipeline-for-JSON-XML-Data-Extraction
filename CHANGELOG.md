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
