from __future__ import annotations

import sys
import types
import asyncio

import pytest

from application.ports.llm import LLMRequest
from infrastructure.llm.litellm_client import LiteLLMClient


def test_litellm_client_builds_kwargs_from_request_and_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LITELLM_PROXY_API_BASE", "https://litellm.internal/")
    monkeypatch.setenv("LITELLM_PROXY_API_KEY", "test-key")

    request = LLMRequest(
        operation="unit.test",
        model="litellm_proxy/test",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0,
        max_tokens=20,
        response_format={"type": "json_object"},
        metadata={"entity_id": "entity-1"},
    )

    kwargs = LiteLLMClient()._kwargs(request)

    assert kwargs == {
        "model": "litellm_proxy/test",
        "messages": [{"role": "user", "content": "hello"}],
        "metadata": {"operation": "unit.test", "entity_id": "entity-1"},
        "api_base": "https://litellm.internal",
        "api_key": "test-key",
        "temperature": 0,
        "max_tokens": 20,
        "response_format": {"type": "json_object"},
    }


def test_litellm_client_uses_groq_api_key_when_proxy_key_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("LITELLM_PROXY_API_KEY", raising=False)
    monkeypatch.delenv("LITELLM_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")

    kwargs = LiteLLMClient()._kwargs(
        LLMRequest(
            operation="unit.test",
            model="groq/llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "hello"}],
        )
    )

    assert kwargs["api_key"] == "groq-key"


def test_litellm_client_uses_direct_groq_config_for_groq_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LITELLM_PROXY_API_BASE", "https://litellm.internal/")
    monkeypatch.setenv("LITELLM_PROXY_API_KEY", "proxy-key")
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")

    kwargs = LiteLLMClient()._kwargs(
        LLMRequest(
            operation="unit.test",
            model="groq/llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "hello"}],
        )
    )

    assert kwargs["api_key"] == "groq-key"
    assert "api_base" not in kwargs


def test_litellm_client_maps_completion_response(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def completion(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {
            "choices": [{"message": {"content": "hello from model"}}],
            "usage": {"total_tokens": 5},
        }

    module = types.SimpleNamespace(completion=completion)
    monkeypatch.setitem(sys.modules, "litellm", module)

    response = LiteLLMClient().complete(
        LLMRequest(
            operation="unit.complete",
            model="litellm_proxy/test",
            messages=[{"role": "user", "content": "hello"}],
        )
    )

    assert captured["model"] == "litellm_proxy/test"
    assert response.text == "hello from model"
    assert response.usage == {"total_tokens": 5}


def test_litellm_client_async_falls_back_when_acompletion_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def completion(**_: object) -> dict[str, object]:
        return {"choices": [{"message": {"content": "fallback"}}]}

    module = types.SimpleNamespace(completion=completion)
    monkeypatch.setitem(sys.modules, "litellm", module)

    request = LLMRequest(
        operation="unit.async",
        model="litellm_proxy/test",
        messages=[{"role": "user", "content": "hello"}],
    )

    response = asyncio.run(async_call(LiteLLMClient(), request))

    assert response.text == "fallback"


async def async_call(client: LiteLLMClient, request: LLMRequest):
    return await client.acomplete(request)
