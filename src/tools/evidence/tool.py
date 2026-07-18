from __future__ import annotations

from tools.contracts import ToolContext, ToolExecution, ToolMeta, ToolResult, ToolServices
from tools.evidence.actions import build_evidence_answer_event
from tools.evidence.contract import EvidenceAnswerInput
from tools.evidence.policy import decide_with_policy


def execute(
    input_data: EvidenceAnswerInput, context: ToolContext, services: ToolServices
) -> ToolExecution:
    decision = decide_with_policy(input_data)
    event = build_evidence_answer_event(decision=decision, input=input_data)
    return ToolExecution(
        result=ToolResult(
            status="success",
            data=decision.model_dump(mode="json"),
            meta=ToolMeta(handler_version="evidence_answer.v1", trace_id=context.trace_id),
        ),
        events=(event,) if event is not None else (),
    )
