from __future__ import annotations

from domain.events.planning import PlanArtifactSavedPayload
from tools._event_builder import new_prefixed_id, tool_event_envelope
from tools.planning.contract import PlanningDecision, PlanningInput


def build_save_artifact_event(*, decision: PlanningDecision, input: PlanningInput):
    artifact_id = decision.artifact_id or new_prefixed_id("plan_artifact")
    payload = PlanArtifactSavedPayload(
        artifact_id=artifact_id,
        session_id=decision.session_id or new_prefixed_id("plan_session"),
        revision_id=decision.revision_id or new_prefixed_id("plan_revision"),
        artifact_type=decision.artifact_type or "general_guidance",
        artifact=decision.artifact or {},
        validation=decision.validation,
    )
    return tool_event_envelope(
        user_id=input.user_id,
        tool_name="planning",
        event_type="plan.artifact_saved",
        aggregate_type="plan_artifact",
        aggregate_id=artifact_id,
        actor_id=f"planning.{decision.action}",
        payload=payload,
        idempotency_key=f"planning:save_artifact:{input.user_id}:{artifact_id}",
    )
