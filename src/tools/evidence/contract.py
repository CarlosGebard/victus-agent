from __future__ import annotations

from typing import Literal

from domain.events.base import ContractModel

EvidenceAnswerAction = Literal["generate_claim", "cite"]


class EvidenceAnswerInput(ContractModel):
    user_id: str
    action: EvidenceAnswerAction
    claim_id: str | None = None
    text: str | None = None
    claim_type: Literal["plan_rationale", "evidence_answer", "safety_explanation", "general"] | None = None
    grounded: bool | None = None
    citation_id: str | None = None
    evidence_id: str | None = None
    source_type: Literal["paper", "guideline", "curated_note", "external"] | None = None
    citation_text: str | None = None
    relevance_score: float | None = None


EvidenceAnswerDecision = EvidenceAnswerInput
