from __future__ import annotations

import json
import os
from unittest.mock import patch

from deterministic_pipeline.config import ProviderConfig
from deterministic_pipeline.contracts import GenerationRequest, PromptPackage
from deterministic_pipeline.providers import OpenAICompatibleAdapter
from deterministic_pipeline.schema_tools import schema_to_grammar


class FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_openai_compatible_adapter_sends_request_and_extracts_text() -> None:
    provider_config = ProviderConfig(
        name="openai_compatible",
        model="gpt-test",
        api_base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        request_timeout_seconds=10,
        use_json_response_format=True,
    )
    adapter = OpenAICompatibleAdapter(provider_config)
    request_payload = GenerationRequest(
        prompt=PromptPackage(
            system_prompt="Return JSON only.",
            user_prompt="Produce a small JSON object.",
            schema={"type": "object"},
            grammar=schema_to_grammar(
                {
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                schema_id="live-test",
            ),
            template_metadata={"template_version": "test"},
        ),
        provider_name="openai_compatible",
        model="gpt-test",
        decoding={"temperature": 0.0, "top_p": 1.0, "max_output_tokens": 128},
        omega={"provider": {"name": "openai_compatible"}},
    )

    captured = {}

    def fake_urlopen(http_request, timeout):
        captured["url"] = http_request.full_url
        captured["authorization"] = http_request.get_header("Authorization")
        captured["content_type"] = http_request.get_header("Content-type")
        captured["timeout"] = timeout
        captured["body"] = json.loads(http_request.data.decode("utf-8"))
        return FakeHTTPResponse(
            {
                "id": "chatcmpl-test",
                "model": "gpt-test",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                "choices": [
                    {
                        "message": {
                            "content": '{"title":"Live title","summary":"Live summary","priority":1,"published":true}'
                        }
                    }
                ],
            }
        )

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        with patch("deterministic_pipeline.providers.urllib_request.urlopen", side_effect=fake_urlopen):
            response = adapter.generate(request_payload)

    assert response.text == '{"title":"Live title","summary":"Live summary","priority":1,"published":true}'
    assert captured["url"] == "https://api.openai.com/v1/chat/completions"
    assert captured["authorization"] == "Bearer test-key"
    assert captured["content_type"] == "application/json"
    assert captured["timeout"] == 10
    assert captured["body"]["response_format"]["type"] == "json_schema"
    assert captured["body"]["response_format"]["json_schema"]["strict"] is True
    assert captured["body"]["response_format"]["json_schema"]["name"] == "live_test"
    assert captured["body"]["messages"][0]["role"] == "system"
    assert captured["body"]["messages"][1]["role"] == "user"
    assert response.provider_metadata["structured_output_strategy"] == "json_schema"
    assert response.provider_metadata["structured_output_strategy_requested"] == "auto"
    assert response.provider_metadata["structured_output_resolution_reason"] == "auto_prefer_json_schema"


def test_openai_compatible_adapter_requires_api_key() -> None:
    provider_config = ProviderConfig(name="openai_compatible", model="gpt-test", api_key_env="OPENAI_API_KEY")
    adapter = OpenAICompatibleAdapter(provider_config)
    request_payload = GenerationRequest(
        prompt=PromptPackage(system_prompt="s", user_prompt="u", schema={}, grammar={}, template_metadata={"template_version": "test"}),
        provider_name="openai_compatible",
        model="gpt-test",
        decoding={},
        omega={},
    )

    with patch.dict(os.environ, {}, clear=True):
        try:
            adapter.generate(request_payload)
        except RuntimeError as exc:
            assert "Missing API key environment variable" in str(exc)
        else:
            raise AssertionError("Expected missing API key failure.")
