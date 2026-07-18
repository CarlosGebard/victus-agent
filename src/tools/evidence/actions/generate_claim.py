from __future__ import annotations

from domain.events.evidence import ClaimGeneratedPayload
from tools._event_builder import new_prefixed_id, tool_event_envelope
from tools.evidence.contract import EvidenceAnswerDecision, EvidenceAnswerInput


def build_generate_claim_event(*, decision: EvidenceAnswerDecision, input: EvidenceAnswerInput):
    claim_id = decision.claim_id or new_prefixed_id("claim")
    payload = ClaimGeneratedPayload(
        claim_id=claim_id,
        text=decision.text or "",
        claim_type=decision.claim_type or "general",
        grounded=bool(decision.grounded),
    )
    return tool_event_envelope(
        user_id=input.user_id,
        tool_name="evidence_answer",
        event_type="claim.generated",
        aggregate_type="claim",
        aggregate_id=claim_id,
        actor_id="evidence.generate_claim",
        payload=payload,
        idempotency_key=f"evidence:claim:{input.user_id}:{claim_id}",
    )
