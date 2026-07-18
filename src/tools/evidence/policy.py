from __future__ import annotations

from tools.evidence.contract import EvidenceAnswerDecision, EvidenceAnswerInput


def decide_with_policy(input: EvidenceAnswerInput) -> EvidenceAnswerDecision:
    if input.action == "generate_claim" and (not input.text or input.grounded is None):
        raise EvidencePolicyError("generate_claim requires text and grounded")
    if input.action == "cite" and (not input.evidence_id or not input.source_type):
        raise EvidencePolicyError("cite requires evidence_id and source_type")
    return input


class EvidencePolicyError(ValueError):
    pass
