# Architecture

This document reflects the approved architecture, the currently implemented JSON-track baseline, and the first-stage generalization of the core pipeline contracts.

## Architectural summary

The system is a deterministic pipeline:

`TextInput -> Preprocess -> PromptBuild -> GenerateCandidate -> FormalGate -> Validate -> Repair -> Canonicalize -> Type -> Report`

The LLM is treated as a candidate generator only. Correctness is enforced by deterministic post-generation mechanisms and explicit formal artifacts.

The orchestration layer is now format-neutral at the contract level:

- `RunConfig` carries an explicit `output_format`
- the pipeline resolves a `FormatRuntime`
- parsing, validation, repair, canonicalization, and typing are delegated to format-specific strategies

Current implementation status:

- generalized core contracts implemented
- JSON strategy implementations implemented
- normalized JSON schema subset expanded for nullable fields, enums, and nested constraints
- strict typing now fails explicitly on unsupported union/composition constructs
- repair logic now recurses through nested JSON objects and arrays for formally safe transformations
- XML declared as a target format identifier, but not implemented yet

## Chosen formal-constraint strategy

For the MVP, the primary formal strategy is:

1. Generate a deterministic JSON Schema artifact.
2. Derive a deterministic JSON grammar artifact from that schema for providers that support constrained structured output.
3. Use provider-native structured output only through a normalized adapter contract when it can be mapped to the schema-derived grammar semantics.
4. Always re-parse, re-validate, repair, and canonicalize locally, regardless of provider capabilities.

This choice is the most academically defensible and reproducible for the current constraints because it keeps the formal source of truth in repository-controlled artifacts rather than in opaque provider-specific behavior. Provider-native features are optimization or transport mechanisms, not the trust boundary.

Implementation status:
- implemented as separate normalized-schema and grammar artifact builders plus a provider-contract layer
- current provider integration is split into:
  - provider registry
  - provider capability profiles
  - deterministic structured-output strategy resolution
  - transport adapters
- current artifact formalism: `normalized-json-schema-subset`
- current normalized subset supports:
  - nested objects
  - arrays
  - enums
  - nullable fields encoded as `[type, "null"]`
  - selected scalar and collection constraints such as `minLength`, `maxLength`, `minimum`, `maximum`, `minItems`, and `maxItems`
- explicitly unsupported in the current subset:
  - `oneOf`
  - `anyOf`
  - `allOf`
- normalized schema artifact and grammar artifact are now constructed as separate stages
- current provider capability model implemented for:
  - `mock`
  - `openai_compatible`
- current strategy resolution order for `auto`:
  1. `json_schema`
  2. `json_object`
  3. `prompt_only`
- current provider binding: `openai_compatible -> response_format.json_schema`
- local validation and repair remain mandatory even when provider-side structured output is active

## Component model

### 1. Configuration layer

Responsibility:
- Load, validate, and serialize the environment configuration `Omega`

Inputs:
- CLI args, config files, runtime overrides

Outputs:
- Immutable run configuration object

Invariants:
- Supports `I4`

### 2. Input preprocessing

Responsibility:
- Normalize whitespace, line endings, encoding, and input metadata

Inputs:
- Raw text document

Outputs:
- `NormalizedText`

Invariants:
- Supports `I4`

### 3. Prompt builder

Responsibility:
- Build deterministic prompts from normalized input, schema references, and policy config

Inputs:
- `NormalizedText`, schema metadata, grammar strategy, run config

Outputs:
- `PromptPackage`

Invariants:
- Supports `I4`

### 4. Provider adapter

Responsibility:
- Provide a unified API for OpenAI, Anthropic, Qwen, DeepSeek, and compatible backends

Inputs:
- `PromptPackage`, model config, optional grammar artifact

Outputs:
- `RawGeneration`

Invariants:
- Supports `I4` by making all provider parameters explicit and logged

### 4c. Provider registry

Responsibility:
- Resolve provider names into concrete adapter factories
- Isolate provider construction from pipeline orchestration

Current implementation:
- explicit registry-backed construction for `mock`
- explicit registry-backed construction for `openai_compatible`
- explicit registry-backed construction for `anthropic_compatible`

### 4a. Provider capability model

Responsibility:
- Represent which structured-output modes a provider can support

Current explicit capabilities:
- `supports_prompt_only`
- `supports_json_object`
- `supports_json_schema`
- `supports_strict_schema_output`

### 4b. Structured-output strategy resolver

Responsibility:
- Select the concrete structured-output mode deterministically from:
  - requested strategy in config
  - provider capability profile
  - provider-specific contract embedded in the grammar artifact

Current supported strategies:
- `prompt_only`
- `json_object`
- `json_schema`
- `auto`

Current `auto` resolution priority:
1. `json_schema`
2. `json_object`
3. `prompt_only`

### 5. Formal gate

Responsibility:
- Parse raw output using the active format strategy, apply grammar/schema-derived acceptance checks, reject malformed output early

Inputs:
- `RawGeneration`, grammar artifact, schema artifact

Outputs:
- `CandidateDocument` or failure

Invariants:
- Directly enforces `I1`

### 6. Schema validator

Responsibility:
- Validate the candidate document against the active formal schema model

Inputs:
- `CandidateDocument`, schema artifact

Outputs:
- validation result with machine-readable errors

Invariants:
- Directly enforces `I2`

### 7. Repair engine

Responsibility:
- Apply deterministic, policy-bounded structural repairs

Allowed operations for MVP:
- insert missing optional fields with deterministic defaults
- reorder keys
- normalize primitive representations before re-validation
- drop forbidden unknown fields only if policy allows it explicitly
- recurse into nested objects and arrays when applying the same formally safe rules

Forbidden operations for MVP:
- infer missing semantic content
- rewrite values based on probabilistic heuristics
- alter meaning-bearing fields without explicit formal rule

Inputs:
- invalid candidate, validator errors, repair policy

Outputs:
- repaired candidate plus repair trace

Invariants:
- Supports `I1`, `I2`, `I4`

### 8. Canonicalizer

Responsibility:
- Produce byte-stable canonical serialization for the active output format

Canonicalization rules:
- stable key ordering
- UTF-8 output
- normalized numeric formatting
- normalized null/empty handling by explicit policy
- fixed date/time normalization rules once date types are introduced

Outputs:
- canonical serialized representation

Invariants:
- Directly enforces `I4`; stabilizes outputs after `I1` and `I2`

### 9. Type layer

Responsibility:
- Map canonical validated structured data into strict application types

Inputs:
- canonical JSON document, type spec

Outputs:
- typed object or typed failure

Invariants:
- Directly enforces `I3`

### 10. Trace/report layer

Responsibility:
- Persist run config, stage outcomes, repair actions, and final status

Outputs:
- run report, trace file, reproducibility metadata

Invariants:
- Supports `I4` and auditability

## Data flow

1. Load and freeze `Omega`
2. Normalize input text
3. Resolve active schema and grammar artifacts
4. Build deterministic prompt package
5. Call provider adapter with explicit settings
6. Parse and formally gate output
7. Validate against JSON Schema
8. If needed, run bounded deterministic repair and validate again
9. Canonicalize the valid structured document
10. Convert to strict typed model
11. Persist report, trace, artifacts, and final result

## Interface contracts

### Core pipeline contract

```python
Pipeline.run(text: str, run_config: RunConfig) -> PipelineResult
```

The result contract is now format-neutral:

```python
PipelineResult.ok: bool
PipelineResult.output_format: str
PipelineResult.canonical_text: str | None
PipelineResult.typed_document: dict | None
```

### Provider adapter contract

```python
ProviderAdapter.generate(request: GenerationRequest) -> RawGeneration
```

### Grammar compiler contract

```python
GrammarCompiler.from_schema(schema: JsonSchemaDocument) -> GrammarArtifact
```

### Repair engine contract

```python
RepairEngine.repair(candidate: dict, errors: list[ValidationError], policy: RepairPolicy) -> RepairResult
```

## Environment model `Omega`

`Omega` must include:

- output format
- provider name
- model identifier and version
- decoding parameters
- prompt template version
- schema identifier and version
- grammar strategy and grammar version
- repair policy version
- canonicalization policy version
- type model version
- trace/report policy

Implementation status:
- `Omega` is serialized into a run manifest
- manifest includes artifact hashes for schema, grammar, prompt template, repair policy, decoding, provider config, and trace policy
- each run gets a deterministic `run_fingerprint`

## Schema strategy

Short term:
- user-supplied JSON Schema is the source of truth

Planned extension:
- deterministic schema induction workflow stored separately from extraction runtime

Rationale:
- schema generation is important, but should be a distinct controlled workflow to preserve reproducibility of the extraction pipeline itself

## Artifact registry

The pipeline now resolves formal artifacts through a registry layer rather than ad hoc direct file usage.

Current registry-managed artifacts:
- schema
- grammar
- prompt template
- repair policy
- canonicalization policy

Each artifact has:
- artifact id
- version
- fingerprint
- source
- metadata

The resolved artifact bundle is embedded into the run manifest, which makes inter-artifact dependencies explicit and replayable.

## Handling future examples and adaptation corpora

The repository should reserve space for:

- `examples/inputs/`
- `examples/expected/`
- `examples/schema_candidates/`
- `reports/evaluations/`

These artifacts must be versioned independently from runtime code so future tuning or dataset-driven refinement does not blur the formal runtime path.

## Invariant mapping

- `I1`: formal gate, parser, repair guardrails
- `I2`: schema validator, repair re-validation
- `I3`: type layer
- `I4`: frozen `Omega`, deterministic prompt construction, bounded repair policy, canonicalizer, trace/report persistence

## Open architectural trade-offs

1. Whether the first implementation should include a real provider adapter or start with a mock-only adapter plus contract tests.
2. Whether grammar artifacts should be expressed as EBNF, JSON Schema-derived automata, or provider-specific structured-output envelopes behind one abstraction.
3. How much auto-defaulting is acceptable in repair before semantic risk becomes too high.
