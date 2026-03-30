from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from urllib import error, request as urllib_request

from deterministic_pipeline.capabilities import get_provider_capabilities
from deterministic_pipeline.config import ProviderConfig
from deterministic_pipeline.contracts import GenerationRequest, RawGeneration
from deterministic_pipeline.strategy_resolution import resolve_structured_output


class ProviderAdapter(ABC):
    @abstractmethod
    def generate(self, request: GenerationRequest) -> RawGeneration:
        raise NotImplementedError


class MockProviderAdapter(ProviderAdapter):
    def __init__(self, mock_response_path: Optional[Path] = None) -> None:
        self._mock_response_path = mock_response_path

    def generate(self, request: GenerationRequest) -> RawGeneration:
        if self._mock_response_path is not None:
            text = self._mock_response_path.read_text(encoding="utf-8").strip()
        else:
            properties = request.prompt.schema.get("properties", {})
            generated = {}
            for key, spec in sorted(properties.items()):
                schema_type = spec.get("type")
                if schema_type == "string":
                    generated[key] = f"{key}-value"
                elif schema_type == "integer":
                    generated[key] = 1
                elif schema_type == "number":
                    generated[key] = 1.0
                elif schema_type == "boolean":
                    generated[key] = True
                elif schema_type == "array":
                    generated[key] = []
                elif schema_type == "object":
                    generated[key] = {}
            text = json.dumps(generated, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return RawGeneration(text=text, provider_metadata={"provider": "mock"})


class OpenAICompatibleAdapter(ProviderAdapter):
    def __init__(self, provider_config: ProviderConfig) -> None:
        self._provider_config = provider_config

    def generate(self, request: GenerationRequest) -> RawGeneration:
        api_key_env = self._provider_config.api_key_env or "OPENAI_API_KEY"
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise RuntimeError("Missing API key environment variable: {0}".format(api_key_env))

        base_url = (self._provider_config.api_base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        endpoint = base_url + "/chat/completions"
        payload = {
            "model": self._provider_config.model,
            "messages": [
                {"role": "system", "content": request.prompt.system_prompt},
                {"role": "user", "content": request.prompt.user_prompt},
            ],
            "temperature": request.decoding.get("temperature", 0.0),
            "top_p": request.decoding.get("top_p", 1.0),
            "max_tokens": request.decoding.get("max_output_tokens", 512),
        }
        capabilities = get_provider_capabilities(self._provider_config)
        resolution = resolve_structured_output(self._provider_config, capabilities, request.prompt.grammar)
        if resolution.response_format is not None:
            payload["response_format"] = resolution.response_format

        body = json.dumps(payload).encode("utf-8")
        http_request = urllib_request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": "Bearer {0}".format(api_key),
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib_request.urlopen(http_request, timeout=self._provider_config.request_timeout_seconds) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError("Provider HTTP error {0}: {1}".format(exc.code, details))
        except error.URLError as exc:
            raise RuntimeError("Provider connection error: {0}".format(exc.reason))

        text = _extract_message_text(response_data)
        return RawGeneration(
            text=text,
            provider_metadata={
                "provider": "openai_compatible",
                "model": response_data.get("model", self._provider_config.model),
                "id": response_data.get("id"),
                "usage": response_data.get("usage", {}),
                "structured_output_strategy": resolution.resolved_strategy,
                "structured_output_strategy_requested": self._provider_config.structured_output_strategy,
                "structured_output_resolution_reason": resolution.resolution_reason,
                "used_response_format": resolution.response_format,
            },
        )


class AnthropicCompatibleAdapter(ProviderAdapter):
    def __init__(self, provider_config: ProviderConfig) -> None:
        self._provider_config = provider_config

    def generate(self, request: GenerationRequest) -> RawGeneration:
        api_key_env = self._provider_config.api_key_env or "ANTHROPIC_API_KEY"
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise RuntimeError("Missing API key environment variable: {0}".format(api_key_env))

        base_url = (self._provider_config.api_base_url or os.environ.get("ANTHROPIC_BASE_URL") or "https://api.anthropic.com/v1").rstrip("/")
        endpoint = base_url + "/messages"
        capabilities = get_provider_capabilities(self._provider_config)
        resolution = resolve_structured_output(self._provider_config, capabilities, request.prompt.grammar)

        payload = {
            "model": self._provider_config.model,
            "system": request.prompt.system_prompt,
            "messages": [
                {"role": "user", "content": request.prompt.user_prompt},
            ],
            "temperature": request.decoding.get("temperature", 0.0),
            "top_p": request.decoding.get("top_p", 1.0),
            "max_tokens": request.decoding.get("max_output_tokens", 512),
        }

        body = json.dumps(payload).encode("utf-8")
        http_request = urllib_request.Request(
            endpoint,
            data=body,
            headers={
                "X-API-Key": api_key,
                "Anthropic-Version": "2023-06-01",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib_request.urlopen(http_request, timeout=self._provider_config.request_timeout_seconds) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError("Provider HTTP error {0}: {1}".format(exc.code, details))
        except error.URLError as exc:
            raise RuntimeError("Provider connection error: {0}".format(exc.reason))

        text = _extract_anthropic_message_text(response_data)
        return RawGeneration(
            text=text,
            provider_metadata={
                "provider": "anthropic_compatible",
                "model": response_data.get("model", self._provider_config.model),
                "id": response_data.get("id"),
                "usage": response_data.get("usage", {}),
                "structured_output_strategy": resolution.resolved_strategy,
                "structured_output_strategy_requested": self._provider_config.structured_output_strategy,
                "structured_output_resolution_reason": resolution.resolution_reason,
                "used_response_format": resolution.response_format,
            },
        )


def _extract_message_text(response_data: dict) -> str:
    choices = response_data.get("choices")
    if not choices:
        raise RuntimeError("Provider response does not contain choices.")
    message = choices[0].get("message", {})
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(block.get("text", ""))
        combined = "".join(text_parts).strip()
        if combined:
            return combined
    raise RuntimeError("Provider response does not contain JSON text content.")


def _extract_anthropic_message_text(response_data: dict) -> str:
    content = response_data.get("content")
    if not isinstance(content, list):
        raise RuntimeError("Provider response does not contain content blocks.")
    text_parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(block.get("text", ""))
    combined = "".join(text_parts).strip()
    if combined:
        return combined
    raise RuntimeError("Provider response does not contain JSON text content.")


def make_provider(provider_config: ProviderConfig, mock_response_path: Optional[Path] = None) -> ProviderAdapter:
    from deterministic_pipeline.provider_registry import build_default_provider_registry

    return build_default_provider_registry().create(provider_config, mock_response_path=mock_response_path)
