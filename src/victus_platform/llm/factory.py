from __future__ import annotations

from victus_platform.llm.contracts import LLMClient
from victus_platform.llm.litellm_client import LiteLLMClient


def build_llm_client() -> LLMClient:
    return LiteLLMClient()
