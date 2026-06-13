from __future__ import annotations

from application.ports.llm import LLMClient
from infrastructure.llm.litellm_client import LiteLLMClient


def build_llm_client() -> LLMClient:
    return LiteLLMClient()
