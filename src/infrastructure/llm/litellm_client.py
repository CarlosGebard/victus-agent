from __future__ import annotations

import asyncio
import os
from typing import Any

from application.ports.llm import LLMRequest, LLMResponse


class LiteLLMClient:
    def complete(self, request: LLMRequest) -> LLMResponse:
        import litellm

        raw = litellm.completion(**self._kwargs(request))
        return self._to_response(raw)

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        import litellm

        try:
            raw = await litellm.acompletion(**self._kwargs(request))
            return self._to_response(raw)
        except AttributeError:
            return await asyncio.to_thread(self.complete, request)

    def _kwargs(self, request: LLMRequest) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": request.model,
            "messages": request.messages,
            "metadata": {"operation": request.operation, **request.metadata},
        }

        if api_base := os.getenv("LITELLM_PROXY_API_BASE"):
            kwargs["api_base"] = api_base.rstrip("/")

        if api_key := os.getenv("LITELLM_PROXY_API_KEY") or os.getenv("LITELLM_KEY"):
            kwargs["api_key"] = api_key

        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        if request.response_format is not None:
            kwargs["response_format"] = request.response_format

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
        return LLMResponse(text=text, raw=data, usage=usage)
