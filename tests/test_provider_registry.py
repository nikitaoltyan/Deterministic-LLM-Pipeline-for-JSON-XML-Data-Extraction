from __future__ import annotations

from pathlib import Path

import pytest

from deterministic_pipeline.config import ProviderConfig
from deterministic_pipeline.provider_registry import ProviderRegistry, build_default_provider_registry
from deterministic_pipeline.providers import AnthropicCompatibleAdapter, MockProviderAdapter, OpenAICompatibleAdapter


def test_default_provider_registry_creates_registered_mock_provider() -> None:
    registry = build_default_provider_registry()

    provider = registry.create(
        ProviderConfig(name="mock", model="mock-json-generator-v1"),
        mock_response_path=Path("fixtures/mock_generation_valid.json"),
    )

    assert isinstance(provider, MockProviderAdapter)


def test_default_provider_registry_creates_registered_openai_provider() -> None:
    registry = build_default_provider_registry()

    provider = registry.create(
        ProviderConfig(name="openai_compatible", model="gpt-test"),
    )

    assert isinstance(provider, OpenAICompatibleAdapter)


def test_provider_registry_rejects_unknown_provider() -> None:
    registry = ProviderRegistry()

    with pytest.raises(ValueError, match="Unsupported provider"):
        registry.create(ProviderConfig(name="unknown-provider", model="x"))


def test_default_provider_registry_creates_registered_anthropic_provider() -> None:
    registry = build_default_provider_registry()

    provider = registry.create(
        ProviderConfig(name="anthropic_compatible", model="claude-test"),
    )

    assert isinstance(provider, AnthropicCompatibleAdapter)
