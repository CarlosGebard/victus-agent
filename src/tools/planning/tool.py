from __future__ import annotations

from tools.contracts import ToolContext, ToolExecution, ToolResult, ToolServices
from tools.planning.actions import build_planning_event
from tools.planning.contract import PlanningInput
from tools.planning.policy import decide_with_policy


def execute(
    input_data: PlanningInput, context: ToolContext, services: ToolServices
) -> ToolExecution:
    decision = decide_with_policy(input_data)
    event = build_planning_event(decision=decision, input=input_data)
    return ToolExecution(
        result=ToolResult(
            status="success",
            data=decision.model_dump(mode="json"),        ),
        events=(event,) if event is not None else (),
    )
