from __future__ import annotations

from typing import Literal

from domain.events.base import ContractModel


class ClaimGeneratedPayload(ContractModel):
    claim_id: str
    text: str
    claim_type: Literal["plan_rationale", "evidence_answer", "safety_explanation", "general"]
    grounded: bool


class EvidenceCitedPayload(ContractModel):
    citation_id: str
    claim_id: str | None = None
    evidence_id: str
    source_type: Literal["paper", "guideline", "curated_note", "external"]
    citation_text: str | None = None
    relevance_score: float | None = None
