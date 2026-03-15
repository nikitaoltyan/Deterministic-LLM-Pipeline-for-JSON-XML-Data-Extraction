from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from urllib import error, request as urllib_request

from deterministic_pipeline.config import ProviderConfig
from deterministic_pipeline.contracts import GenerationRequest, RawGeneration


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
        response_format = _resolve_structured_output_contract(request, self._provider_config)
        if response_format is not None:
            payload["response_format"] = response_format

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
                "structured_output_strategy": self._provider_config.structured_output_strategy,
                "used_response_format": response_format,
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


def make_provider(provider_config: ProviderConfig, mock_response_path: Optional[Path] = None) -> ProviderAdapter:
    if provider_config.name == "mock":
        return MockProviderAdapter(mock_response_path=mock_response_path)
    if provider_config.name == "openai_compatible":
        return OpenAICompatibleAdapter(provider_config)
    raise ValueError("Unsupported provider: {0}".format(provider_config.name))


def _resolve_structured_output_contract(request: GenerationRequest, provider_config: ProviderConfig) -> Optional[dict]:
    strategy = provider_config.structured_output_strategy
    provider_contracts = request.prompt.grammar.get("provider_contracts", {})
    openai_contract = provider_contracts.get("openai_compatible", {})

    if strategy == "prompt_only":
        return None
    if strategy == "json_object":
        return {"type": "json_object"} if provider_config.use_json_response_format else None
    if strategy == "json_schema":
        response_format = openai_contract.get("response_format")
        if response_format is None:
            raise RuntimeError("Structured output strategy json_schema requested, but no provider contract is available.")
        return response_format
    if strategy == "auto":
        if openai_contract.get("response_format") is not None:
            return openai_contract["response_format"]
        if provider_config.use_json_response_format:
            return {"type": "json_object"}
        return None
    raise RuntimeError("Unknown structured output strategy: {0}".format(strategy))
