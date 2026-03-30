from __future__ import annotations

import pytest

from deterministic_pipeline.capabilities import get_provider_capabilities
from deterministic_pipeline.config import ProviderConfig
from deterministic_pipeline.schema_tools import schema_to_grammar
from deterministic_pipeline.strategy_resolution import resolve_structured_output


def test_resolve_structured_output_auto_prefers_json_schema() -> None:
    provider_config = ProviderConfig(
        name="openai_compatible",
        model="gpt-test",
        structured_output_strategy="auto",
        use_json_response_format=True,
    )
    capabilities = get_provider_capabilities(provider_config)
    grammar = schema_to_grammar(
        {
            "type": "object",
            "required": ["title"],
            "properties": {"title": {"type": "string"}},
            "additionalProperties": False,
        },
        schema_id="auto-test",
    )

    resolution = resolve_structured_output(provider_config, capabilities, grammar)

    assert resolution.resolved_strategy == "json_schema"
    assert resolution.response_format is not None
    assert resolution.response_format["type"] == "json_schema"
    assert resolution.resolution_reason == "auto_prefer_json_schema"


def test_resolve_structured_output_auto_falls_back_to_prompt_only_for_mock() -> None:
    provider_config = ProviderConfig(
        name="mock",
        model="mock-json-generator-v1",
        structured_output_strategy="auto",
        use_json_response_format=False,
    )
    capabilities = get_provider_capabilities(provider_config)

    resolution = resolve_structured_output(provider_config, capabilities, grammar={})

    assert resolution.resolved_strategy == "prompt_only"
    assert resolution.response_format is None
    assert resolution.resolution_reason == "auto_fallback_prompt_only"


def test_resolve_structured_output_rejects_unsupported_json_object_for_mock() -> None:
    provider_config = ProviderConfig(
        name="mock",
        model="mock-json-generator-v1",
        structured_output_strategy="json_object",
        use_json_response_format=False,
    )
    capabilities = get_provider_capabilities(provider_config)

    with pytest.raises(RuntimeError, match="not supported by provider mock"):
        resolve_structured_output(provider_config, capabilities, grammar={})


def test_resolve_structured_output_requires_provider_contract_for_json_schema() -> None:
    provider_config = ProviderConfig(
        name="openai_compatible",
        model="gpt-test",
        structured_output_strategy="json_schema",
        use_json_response_format=True,
    )
    capabilities = get_provider_capabilities(provider_config)

    with pytest.raises(RuntimeError, match="no provider contract is available"):
        resolve_structured_output(provider_config, capabilities, grammar={})
