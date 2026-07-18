from __future__ import annotations

from domain.events.planning import PlanRevisionCreatedPayload
from tools._event_builder import new_prefixed_id, tool_event_envelope
from tools.planning.contract import PlanningDecision, PlanningInput


def build_create_revision_event(*, decision: PlanningDecision, input: PlanningInput):
    revision_id = decision.revision_id or new_prefixed_id("plan_revision")
    payload = PlanRevisionCreatedPayload(
        revision_id=revision_id,
        session_id=decision.session_id or new_prefixed_id("plan_session"),
        parent_revision_id=decision.parent_revision_id,
        objectives=decision.objectives,
        summary=decision.summary,
    )
    return tool_event_envelope(
        user_id=input.user_id,
        tool_name="planning",
        event_type="plan.revision_created",
        aggregate_type="plan_revision",
        aggregate_id=revision_id,
        actor_id=f"planning.{decision.action}",
        payload=payload,
        idempotency_key=f"planning:create_revision:{input.user_id}:{revision_id}",
    )
