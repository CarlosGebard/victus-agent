from __future__ import annotations

from pathlib import Path

from application.routing.embeddings import Embedder
from application.routing.models import RouteDecision
from application.routing.normalizer import normalize_text
from application.routing.policy import RoutingPolicy
from application.routing.prototype_store import PrototypeStore, ScoreWeights
from application.routing.safety_gate import SafetyGate
from application.routing.scorer import IntentScorer


class IntentRouter:
    def __init__(
        self,
        embedder: Embedder,
        prototype_store: PrototypeStore,
        policy: RoutingPolicy,
        safety_gate: SafetyGate,
        weights: ScoreWeights,
        log_path: str | Path = "data/runtime/router/decisions.jsonl",
    ) -> None:
        self.embedder = embedder
        self.prototype_store = prototype_store
        self.policy = policy
        self.safety_gate = safety_gate
        self.scorer = IntentScorer(embedder, prototype_store, weights)
        self.log_path = Path(log_path)

    def route(self, input_text: str) -> RouteDecision:
        normalized_text = normalize_text(input_text)
        safety = self.safety_gate.check(normalized_text)

        scores = []
        if safety.severity not in {"high", "urgent"}:
            scores = self.scorer.score(normalized_text)

        decision = self.policy.decide(
            input_text=input_text,
            normalized_text=normalized_text,
            scores=scores,
            safety=safety,
        )

        if safety.severity == "medium":
            decision.requires_safety_overlay = True
            decision.safety_reason = safety.reason

        self._append_log(decision)
        return decision

    def _append_log(self, decision: RouteDecision) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(decision.model_dump_json() + "\n")
