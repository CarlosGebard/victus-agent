from __future__ import annotations

from tools.contracts import ToolContext, ToolExecution, ToolResult, ToolServices
from tools.profile.actions import build_profile_update_event
from tools.profile.contract import ProfileUpdateInput
from tools.profile.policy import decide_with_policy
from tools.profile.validators import validate_profile_update_decision


def execute(
    input_data: ProfileUpdateInput, context: ToolContext, services: ToolServices
) -> ToolExecution:
    decision = validate_profile_update_decision(decide_with_policy(input_data), input_data)
    if decision.requires_safety_validation:
        status = "blocked"
    elif decision.profile_action == "needs_clarification":
        status = "needs_clarification"
    elif decision.profile_action == "reroute":
        status = "rejected"
    else:
        status = "success"
    event = build_profile_update_event(decision=decision, input=input_data)
    return ToolExecution(
        result=ToolResult(
            status=status,
            data=decision.model_dump(mode="json"),        ),
        events=(event,) if event is not None and status == "success" else (),
    )
