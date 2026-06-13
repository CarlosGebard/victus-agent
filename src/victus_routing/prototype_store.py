from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from victus_routing.models import IntentType, RouteName


@dataclass(frozen=True)
class IntentPrototype:
    intent_type: IntentType
    route: RouteName
    definition: list[str]
    positive_examples: list[str]
    negative_examples: list[str]
    boundary_examples: list[str]


@dataclass(frozen=True)
class RouterThresholds:
    accept_score: float
    accept_margin: float
    multi_score: float
    multi_second_score: float
    clarify_below: float


@dataclass(frozen=True)
class ScoreWeights:
    positive: float
    definition: float
    boundary: float
    context: float
    entity_signal: float
    negative_penalty: float


class PrototypeStore:
    def __init__(self, router_version: str, intents: list[IntentPrototype]) -> None:
        self.router_version = router_version
        self.intents = intents

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PrototypeStore":
        data = _load_yaml(path)
        intents = [
            IntentPrototype(
                intent_type=item["intent_type"],
                route=item["route"],
                definition=list(item.get("definition", [])),
                positive_examples=list(item.get("positive_examples", [])),
                negative_examples=list(item.get("negative_examples", [])),
                boundary_examples=list(item.get("boundary_examples", [])),
            )
            for item in data["intents"]
        ]
        return cls(router_version=data["router_version"], intents=intents)


def load_thresholds(path: str | Path) -> tuple[str, RouterThresholds, ScoreWeights]:
    data = _load_yaml(path)
    thresholds = RouterThresholds(**data["thresholds"])
    weights = ScoreWeights(**data["score_weights"])
    return data["router_version"], thresholds, weights


def _load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping: {path}")
    return data
