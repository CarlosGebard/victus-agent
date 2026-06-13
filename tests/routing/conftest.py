from __future__ import annotations

from pathlib import Path

import pytest

from victus_routing.embeddings import Embedder
from victus_routing.policy import RoutingPolicy
from victus_routing.prototype_store import PrototypeStore, RouterThresholds, load_thresholds
from victus_routing.router import IntentRouter
from victus_routing.safety_gate import SafetyGate


class LexicalTestEmbedder:
    """Controlled semantic-ish embedder for stable router orchestration tests."""

    labels = ["log", "new", "revise", "weekly", "evidence", "risk"]

    def embed(self, text: str) -> list[float]:
        normalized = text.lower()
        vector = [0.0] * len(self.labels)
        label = self._label(normalized)
        if label is not None:
            vector[self.labels.index(label)] = 1.0
        return vector

    def _label(self, text: str) -> str | None:
        if any(term in text for term in ["risk, urgent symptoms", "chest hurts", "short of breath", "diabetes", "hypertension", "presion alta", "medication", "extreme caffeine"]):
            return "risk"
        if any(term in text for term in ["asks for scientific evidence", "evidence", "studies", "paper", "science", "scientific", "evidencia", "consensus"]):
            return "evidence"
        if any(term in text for term in ["review weekly progress", "review my week", "this week", "weekly", "weekly summary", "revisemos mi semana", "analyze my week"]):
            return "weekly"
        if any(term in text for term in ["modify, adjust", "change", "adjust", "modify", "remove", "adapt", "cambia", "menos tiempo", "improve my plan", "sin lactosa", "mas proteina"]):
            return "revise"
        if any(term in text for term in ["create a new", "make me", "create", "new plan", "meal plan", "diet plan", "start a plan", "hazme un plan", "menu semanal", "bajar grasa", "lose fat"]):
            return "new"
        if any(term in text for term in ["log, save", "today", "save", "update my weight", "registered", "slept", "comi", "almuerzo", "ate", "peso"]):
            return "log"
        return None


@pytest.fixture
def lexical_embedder() -> Embedder:
    return LexicalTestEmbedder()


@pytest.fixture
def router(tmp_path: Path, lexical_embedder: Embedder) -> IntentRouter:
    store = PrototypeStore.from_yaml("config/router/intent_prototypes.v1.yml")
    version, _, weights = load_thresholds("config/router/router_thresholds.v1.yml")
    thresholds = RouterThresholds(
        accept_score=0.50,
        accept_margin=0.0,
        multi_score=1.10,
        multi_second_score=1.10,
        clarify_below=0.10,
    )
    return IntentRouter(
        embedder=lexical_embedder,
        prototype_store=store,
        policy=RoutingPolicy(version, thresholds),
        safety_gate=SafetyGate(),
        weights=weights,
        log_path=tmp_path / "decisions.jsonl",
    )
