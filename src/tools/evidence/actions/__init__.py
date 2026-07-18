from __future__ import annotations

from domain.events.envelope import UserEventEnvelope
from tools.evidence.actions.cite import build_cite_event
from tools.evidence.actions.generate_claim import build_generate_claim_event
from tools.evidence.contract import EvidenceAnswerDecision, EvidenceAnswerInput


def build_evidence_answer_event(
    *,
    decision: EvidenceAnswerDecision,
    input: EvidenceAnswerInput,
) -> UserEventEnvelope:
    if decision.action == "generate_claim":
        return build_generate_claim_event(decision=decision, input=input)
    return build_cite_event(decision=decision, input=input)
