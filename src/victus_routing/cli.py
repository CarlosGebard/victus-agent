from __future__ import annotations

import argparse
import json
from pathlib import Path

from victus_routing.models import IntentScore, RouteDecision
from victus_routing.embeddings import DeterministicHashEmbedder, SentenceTransformersEmbedder
from victus_routing.policy import RoutingPolicy
from victus_routing.prototype_store import PrototypeStore, load_thresholds
from victus_routing.router import IntentRouter
from victus_routing.safety_gate import SafetyGate

DEFAULT_PROTOTYPES = Path("config/router/intent_prototypes.v1.yml")
DEFAULT_THRESHOLDS = Path("config/router/router_thresholds.v1.yml")


def main() -> None:
    parser = argparse.ArgumentParser(description="Route a user utterance with the Victus router.")
    parser.add_argument("input_text")
    parser.add_argument("--embedder", choices=["hash", "sentence-transformers"], default="hash")
    parser.add_argument("--show-scores", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print the strict RouteDecision JSON.")
    args = parser.parse_args()

    embedder = (
        DeterministicHashEmbedder()
        if args.embedder == "hash"
        else SentenceTransformersEmbedder(model_name="BAAI/bge-m3")
    )
    prototype_store = PrototypeStore.from_yaml(DEFAULT_PROTOTYPES)
    router_version, thresholds, weights = load_thresholds(DEFAULT_THRESHOLDS)
    policy = RoutingPolicy(router_version=router_version, thresholds=thresholds)
    router = IntentRouter(
        embedder=embedder,
        prototype_store=prototype_store,
        policy=policy,
        safety_gate=SafetyGate(),
        weights=weights,
    )
    decision = router.route(args.input_text)

    if not args.json:
        print(format_domain_percentages(decision, show_scores=args.show_scores))
        return

    payload = decision.model_dump()
    if not args.show_scores:
        payload["scores"] = []
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def format_domain_percentages(decision: RouteDecision, *, show_scores: bool = False) -> str:
    lines = [
        f"Input: {decision.input_text}",
        f"Normalized: {decision.normalized_text}",
        f"Decision: {decision.decision}",
        f"Route: {decision.route}",
    ]
    if decision.requires_safety_overlay and decision.safety_reason:
        lines.append(f"Safety: {decision.safety_reason}")

    if not decision.scores:
        lines.append("Domain probabilities:")
        lines.append("  SafetyTriageRoute: 100.00%")
        return "\n".join(lines)

    lines.append("Domain probabilities:")
    for score, percentage in domain_percentages(decision.scores):
        suffix = ""
        if show_scores:
            suffix = f" (score={score.score:.4f})"
        lines.append(f"  {score.route} / {score.intent_type}: {percentage:.2f}%{suffix}")

    return "\n".join(lines)


def domain_percentages(scores: list[IntentScore]) -> list[tuple[IntentScore, float]]:
    positive_scores = [max(score.score, 0.0) for score in scores]
    total = sum(positive_scores)
    if total == 0:
        if not scores:
            return []
        uniform = 100.0 / len(scores)
        return [(score, uniform) for score in scores]
    return [(score, value * 100.0 / total) for score, value in zip(scores, positive_scores)]


if __name__ == "__main__":
    main()
