from __future__ import annotations

from dataclasses import dataclass

from deterministic_pipeline.config import ProviderConfig


@dataclass(frozen=True)
class ProviderCapabilityProfile:
    provider_name: str
    supports_prompt_only: bool
    supports_json_object: bool
    supports_json_schema: bool
    supports_strict_schema_output: bool


def get_provider_capabilities(provider_config: ProviderConfig) -> ProviderCapabilityProfile:
    if provider_config.name == "mock":
        return ProviderCapabilityProfile(
            provider_name="mock",
            supports_prompt_only=True,
            supports_json_object=False,
            supports_json_schema=False,
            supports_strict_schema_output=False,
        )
    if provider_config.name == "openai_compatible":
        return ProviderCapabilityProfile(
            provider_name="openai_compatible",
            supports_prompt_only=True,
            supports_json_object=provider_config.use_json_response_format,
            supports_json_schema=True,
            supports_strict_schema_output=True,
        )
    if provider_config.name == "anthropic_compatible":
        return ProviderCapabilityProfile(
            provider_name="anthropic_compatible",
            supports_prompt_only=True,
            supports_json_object=False,
            supports_json_schema=False,
            supports_strict_schema_output=False,
        )
    raise ValueError("Unsupported provider for capability resolution: {0}".format(provider_config.name))
