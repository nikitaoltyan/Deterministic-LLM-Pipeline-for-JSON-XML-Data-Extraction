from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from deterministic_pipeline.config import ProviderConfig
from deterministic_pipeline.providers import AnthropicCompatibleAdapter, MockProviderAdapter, OpenAICompatibleAdapter, ProviderAdapter


ProviderFactory = Callable[[ProviderConfig, Optional[Path]], ProviderAdapter]


@dataclass(frozen=True)
class RegisteredProvider:
    name: str
    factory: ProviderFactory


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, RegisteredProvider] = {}

    def register(self, name: str, factory: ProviderFactory) -> None:
        self._providers[name] = RegisteredProvider(name=name, factory=factory)

    def create(self, provider_config: ProviderConfig, mock_response_path: Optional[Path] = None) -> ProviderAdapter:
        registered = self._providers.get(provider_config.name)
        if registered is None:
            raise ValueError("Unsupported provider: {0}".format(provider_config.name))
        return registered.factory(provider_config, mock_response_path)


def build_default_provider_registry() -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register("mock", _build_mock_provider)
    registry.register("openai_compatible", _build_openai_compatible_provider)
    registry.register("anthropic_compatible", _build_anthropic_compatible_provider)
    return registry


def _build_mock_provider(provider_config: ProviderConfig, mock_response_path: Optional[Path]) -> ProviderAdapter:
    return MockProviderAdapter(mock_response_path=mock_response_path)


def _build_openai_compatible_provider(provider_config: ProviderConfig, mock_response_path: Optional[Path]) -> ProviderAdapter:
    return OpenAICompatibleAdapter(provider_config)


def _build_anthropic_compatible_provider(provider_config: ProviderConfig, mock_response_path: Optional[Path]) -> ProviderAdapter:
    return AnthropicCompatibleAdapter(provider_config)
