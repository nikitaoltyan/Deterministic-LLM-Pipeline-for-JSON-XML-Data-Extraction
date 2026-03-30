from __future__ import annotations

from deterministic_pipeline.capabilities import get_provider_capabilities
from deterministic_pipeline.config import ProviderConfig


def test_mock_provider_capabilities_are_explicit() -> None:
    capabilities = get_provider_capabilities(ProviderConfig(name="mock", model="mock-json-generator-v1"))

    assert capabilities.provider_name == "mock"
    assert capabilities.supports_prompt_only is True
    assert capabilities.supports_json_object is False
    assert capabilities.supports_json_schema is False
    assert capabilities.supports_strict_schema_output is False


def test_openai_compatible_capabilities_follow_provider_config() -> None:
    capabilities = get_provider_capabilities(
        ProviderConfig(
            name="openai_compatible",
            model="gpt-test",
            use_json_response_format=True,
        )
    )

    assert capabilities.provider_name == "openai_compatible"
    assert capabilities.supports_prompt_only is True
    assert capabilities.supports_json_object is True
    assert capabilities.supports_json_schema is True
    assert capabilities.supports_strict_schema_output is True


def test_anthropic_compatible_capabilities_are_prompt_only() -> None:
    capabilities = get_provider_capabilities(
        ProviderConfig(
            name="anthropic_compatible",
            model="claude-test",
        )
    )

    assert capabilities.provider_name == "anthropic_compatible"
    assert capabilities.supports_prompt_only is True
    assert capabilities.supports_json_object is False
    assert capabilities.supports_json_schema is False
    assert capabilities.supports_strict_schema_output is False
