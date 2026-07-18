from __future__ import annotations

from domain.events.evidence import EvidenceCitedPayload
from tools._event_builder import new_prefixed_id, tool_event_envelope
from tools.evidence.contract import EvidenceAnswerDecision, EvidenceAnswerInput


def build_cite_event(*, decision: EvidenceAnswerDecision, input: EvidenceAnswerInput):
    citation_id = decision.citation_id or new_prefixed_id("citation")
    payload = EvidenceCitedPayload(
        citation_id=citation_id,
        claim_id=decision.claim_id,
        evidence_id=decision.evidence_id or "unknown",
        source_type=decision.source_type or "external",
        citation_text=decision.citation_text,
        relevance_score=decision.relevance_score,
    )
    return tool_event_envelope(
        user_id=input.user_id,
        tool_name="evidence_answer",
        event_type="evidence.cited",
        aggregate_type="evidence_citation",
        aggregate_id=citation_id,
        actor_id="evidence.cite",
        payload=payload,
        idempotency_key=f"evidence:cite:{input.user_id}:{citation_id}",
    )
