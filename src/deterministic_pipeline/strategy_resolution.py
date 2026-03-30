from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from deterministic_pipeline.capabilities import ProviderCapabilityProfile
from deterministic_pipeline.config import ProviderConfig


@dataclass(frozen=True)
class StructuredOutputResolution:
    resolved_strategy: str
    response_format: Optional[dict[str, Any]]
    resolution_reason: str


def resolve_structured_output(
    provider_config: ProviderConfig,
    capabilities: ProviderCapabilityProfile,
    grammar: dict[str, Any],
) -> StructuredOutputResolution:
    strategy = provider_config.structured_output_strategy
    provider_contracts = grammar.get("provider_contracts", {})
    provider_contract = provider_contracts.get(provider_config.name, {})
    response_format = provider_contract.get("response_format")

    if strategy == "prompt_only":
        if not capabilities.supports_prompt_only:
            raise RuntimeError("Structured output strategy prompt_only is not supported by provider {0}.".format(provider_config.name))
        return StructuredOutputResolution(
            resolved_strategy="prompt_only",
            response_format=None,
            resolution_reason="explicit_prompt_only",
        )

    if strategy == "json_object":
        if not capabilities.supports_json_object:
            raise RuntimeError("Structured output strategy json_object is not supported by provider {0}.".format(provider_config.name))
        return StructuredOutputResolution(
            resolved_strategy="json_object",
            response_format={"type": "json_object"},
            resolution_reason="explicit_json_object",
        )

    if strategy == "json_schema":
        if not capabilities.supports_json_schema:
            raise RuntimeError("Structured output strategy json_schema is not supported by provider {0}.".format(provider_config.name))
        if response_format is None:
            raise RuntimeError("Structured output strategy json_schema requested, but no provider contract is available.")
        return StructuredOutputResolution(
            resolved_strategy="json_schema",
            response_format=response_format,
            resolution_reason="explicit_json_schema",
        )

    if strategy == "auto":
        if capabilities.supports_json_schema and response_format is not None:
            return StructuredOutputResolution(
                resolved_strategy="json_schema",
                response_format=response_format,
                resolution_reason="auto_prefer_json_schema",
            )
        if capabilities.supports_json_object:
            return StructuredOutputResolution(
                resolved_strategy="json_object",
                response_format={"type": "json_object"},
                resolution_reason="auto_fallback_json_object",
            )
        if capabilities.supports_prompt_only:
            return StructuredOutputResolution(
                resolved_strategy="prompt_only",
                response_format=None,
                resolution_reason="auto_fallback_prompt_only",
            )
        raise RuntimeError("Automatic structured output resolution failed for provider {0}.".format(provider_config.name))

    raise RuntimeError("Unknown structured output strategy: {0}".format(strategy))
