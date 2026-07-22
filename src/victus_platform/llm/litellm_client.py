from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from victus_platform.llm.contracts import LLMRequest, LLMResponse
from victus_platform.telemetry.phoenix import record_llm_usage, trace_llm_call


class LiteLLMClient:
    def complete(self, request: LLMRequest) -> LLMResponse:
        import litellm

        with trace_llm_call(request) as span:
            raw = litellm.completion(**self._kwargs(request))
            response = self._to_response(raw)
            record_llm_usage(span, response.usage)
            return response

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        return await asyncio.to_thread(self.complete, request)

    def _kwargs(self, request: LLMRequest) -> dict[str, Any]:
        proxy_base = os.getenv("LITELLM_PROXY_API_BASE")
        kwargs: dict[str, Any] = {
            "model": _provider_model(request.model, proxy_configured=bool(proxy_base)),
            "messages": request.messages,
            "metadata": {"operation": request.operation, **request.metadata},
        }

        is_direct_groq_model = request.model.startswith("groq/")

        if not is_direct_groq_model and proxy_base:
            kwargs["api_base"] = proxy_base.rstrip("/")

        api_key = (
            os.getenv("GROQ_API_KEY")
            if is_direct_groq_model
            else os.getenv("LITELLM_PROXY_API_KEY")
            or os.getenv("LITELLM_KEY")
            or os.getenv("GROQ_API_KEY")
        )
        if api_key:
            kwargs["api_key"] = api_key

        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        if request.response_format is not None:
            kwargs["response_format"] = request.response_format
        if request.tools is not None:
            kwargs["tools"] = request.tools
        if request.tool_choice is not None:
            kwargs["tool_choice"] = request.tool_choice

        return kwargs

    def _to_response(self, raw: Any) -> LLMResponse:
        if hasattr(raw, "model_dump"):
            data = raw.model_dump()
        else:
            data = dict(raw)

        choices = data.get("choices") or []
        message = choices[0].get("message") if choices else {}
        text = str((message or {}).get("content") or "")
        usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
        return LLMResponse(
            text=text,
            raw=data,
            usage=usage,
            tool_calls=_tool_calls(message or {}),
        )


def _provider_model(model: str, *, proxy_configured: bool) -> str:
    if proxy_configured and model.startswith("litellm_proxy/"):
        return f"openai/{model.removeprefix('litellm_proxy/')}"
    return model


def _tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for call in message.get("tool_calls") or []:
        function = call.get("function") if isinstance(call, dict) else None
        if not isinstance(function, dict) or not function.get("name"):
            continue
        raw_arguments = function.get("arguments") or "{}"
        try:
            arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        except json.JSONDecodeError:
            arguments = {"_invalid_json": raw_arguments}
        result.append(
            {
                "id": call.get("id"),
                "name": str(function["name"]),
                "arguments": arguments if isinstance(arguments, dict) else {},
            }
        )
    return result
