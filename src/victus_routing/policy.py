from __future__ import annotations

from victus_routing.models import IntentScore, RouteDecision, SafetyGateResult
from victus_routing.prototype_store import RouterThresholds


class RoutingPolicy:
    def __init__(self, router_version: str, thresholds: RouterThresholds) -> None:
        self.router_version = router_version
        self.thresholds = thresholds

    def decide(
        self,
        *,
        input_text: str,
        normalized_text: str,
        scores: list[IntentScore],
        safety: SafetyGateResult,
    ) -> RouteDecision:
        if safety.severity in {"high", "urgent"}:
            return RouteDecision(
                router_version=self.router_version,
                input_text=input_text,
                normalized_text=normalized_text,
                decision="safety",
                route="SafetyTriageRoute",
                intent_type="risk_medical_unsafe",
                confidence=1.0,
                requires_safety_overlay=True,
                safety_reason=safety.reason,
                scores=scores,
            )

        sorted_scores = sorted(scores, key=lambda item: item.score, reverse=True)
        if not sorted_scores:
            return RouteDecision(
                router_version=self.router_version,
                input_text=input_text,
                normalized_text=normalized_text,
                decision="clarify",
                route="ClarificationRoute",
                confidence=0.0,
                margin=None,
                requires_clarification=True,
                clarification_question="What would you like help with: logging data, planning, revising a plan, reviewing progress, or asking for evidence?",
                scores=[],
            )

        top1 = sorted_scores[0]
        top2 = sorted_scores[1] if len(sorted_scores) > 1 else None
        margin = top1.score - top2.score if top2 else None

        if top1.score >= self.thresholds.accept_score and (
            margin is None or margin >= self.thresholds.accept_margin
        ):
            return RouteDecision(
                router_version=self.router_version,
                input_text=input_text,
                normalized_text=normalized_text,
                decision="route",
                route=top1.route,
                intent_type=top1.intent_type,
                confidence=top1.score,
                margin=margin,
                scores=sorted_scores,
            )

        if (
            top2
            and top1.score >= self.thresholds.multi_score
            and top2.score >= self.thresholds.multi_second_score
        ):
            return RouteDecision(
                router_version=self.router_version,
                input_text=input_text,
                normalized_text=normalized_text,
                decision="mixed",
                route="MixedIntentResolver",
                intent_type=top1.intent_type,
                secondary_intents=[top2.intent_type],
                confidence=top1.score,
                margin=margin,
                scores=sorted_scores,
            )

        if top1.score < self.thresholds.clarify_below:
            return RouteDecision(
                router_version=self.router_version,
                input_text=input_text,
                normalized_text=normalized_text,
                decision="clarify",
                route="ClarificationRoute",
                intent_type=top1.intent_type,
                confidence=top1.score,
                margin=margin,
                requires_clarification=True,
                clarification_question="Do you want to log data, create a new plan, revise an existing plan, review your week, or ask an evidence question?",
                scores=sorted_scores,
            )

        return RouteDecision(
            router_version=self.router_version,
            input_text=input_text,
            normalized_text=normalized_text,
            decision="mixed",
            route="MixedIntentResolver",
            intent_type=top1.intent_type,
            secondary_intents=[top2.intent_type] if top2 else [],
            confidence=top1.score,
            margin=margin,
            scores=sorted_scores,
        )
