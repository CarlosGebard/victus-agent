import pytest
from pydantic import ValidationError

from events.models import ToolEventRef
from tools.models import ClarificationRequest, ToolResult


def test_tool_result_defaults_to_safe_success_envelope() -> None:
    result = ToolResult(status="success", data={"ok": True})

    assert result.events_emitted == []
    assert result.warnings == []
    assert result.safety.status == "ok"
    assert result.meta.schema_version == 1


def test_tool_result_accepts_event_refs_and_clarification() -> None:
    result = ToolResult(
        status="needs_clarification",
        events_emitted=[ToolEventRef(event_id="event-1", event_type="clarification.requested", seq=3)],
        clarification=ClarificationRequest(
            missing_fields=["consumed_at"],
            question="When did you eat this?",
            expected_answer_type="time",
            resume_node="EventCaptureNode",
        ),
        safety={"status": "needs_clarification", "reasons": []},
    )

    assert result.clarification is not None
    assert result.clarification.expected_answer_type == "time"


def test_tool_result_rejects_unknown_status() -> None:
    with pytest.raises(ValidationError):
        ToolResult(status="done")
