from __future__ import annotations

from tools.feedback.contract import FeedbackDecision, FeedbackInput


def decide_with_policy(input: FeedbackInput) -> FeedbackDecision:
    if input.action == "record" and (not input.text or not input.target_type):
        raise FeedbackPolicyError("record requires text and target_type")
    if input.action == "resolve" and (not input.feedback_id or not input.resolution):
        raise FeedbackPolicyError("resolve requires feedback_id and resolution")
    return input


class FeedbackPolicyError(ValueError):
    pass
