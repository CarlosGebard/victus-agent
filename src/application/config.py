from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_RUNTIME_CONFIG = Path("config/runtime.yml")


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str


@dataclass(frozen=True)
class SafetyConfig:
    model: str


@dataclass(frozen=True)
class RuntimeConfig:
    llm: LLMConfig
    safety: SafetyConfig


def load_runtime_config(path: str | Path = DEFAULT_RUNTIME_CONFIG) -> RuntimeConfig:
    data = _load_yaml(path)
    llm = data.get("llm")
    if not isinstance(llm, dict):
        raise ValueError("runtime config must contain an llm mapping")

    provider = llm.get("provider")
    model = llm.get("model")
    if not isinstance(provider, str) or not provider:
        raise ValueError("runtime llm.provider must be a non-empty string")
    if not isinstance(model, str) or not model:
        raise ValueError("runtime llm.model must be a non-empty string")

    safety = data.get("safety", {})
    if safety is None:
        safety = {}
    if not isinstance(safety, dict):
        raise ValueError("runtime safety must be a mapping")
    safety_model = safety.get("model", "meta-llama/Llama-Guard-3-1B")
    if not isinstance(safety_model, str) or not safety_model:
        raise ValueError("runtime safety.model must be a non-empty string")

    return RuntimeConfig(
        llm=LLMConfig(provider=provider, model=model),
        safety=SafetyConfig(model=safety_model),
    )


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping: {path}")
    return data
