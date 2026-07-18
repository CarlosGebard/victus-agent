from contextlib import nullcontext

from domain.events.envelope import UserEventEnvelope
from tools.catalog import get_tool, list_tools
from tools.contracts import ToolContext, ToolInvocation
from tools.runtime import ToolRuntime


def test_catalog_and_capabilities_share_one_runtime() -> None:
    names = [definition.name for definition in list_tools(exposure="mcp")]
    assert names == [
        "event_capture",
        "profile_update",
        "planning",
        "feedback",
        "evidence_answer",
        "clarification",
        "confirmation",
        "recuperar_perfil",
    ]
    assert all(get_tool(name).input_schema for name in names)

    cases = [
        ("event_capture", {"user_id": "u1", "normalized_text": "hoy comi arroz"}, "success"),
        ("profile_update", {"user_id": "u1", "normalized_text": "soy intolerante a lactosa"}, "success"),
        ("planning", {"user_id": "u1", "action": "set_goal", "primary_goal": "health"}, "success"),
        ("feedback", {"user_id": "u1", "action": "record", "target_type": "plan", "text": "bien"}, "success"),
        ("evidence_answer", {"user_id": "u1", "action": "generate_claim", "text": "claim", "grounded": True}, "success"),
        ("clarification", {"user_id": "u1", "action": "request", "missing_fields": ["time"], "question": "Cuando?"}, "needs_clarification"),
        ("confirmation", {"user_id": "u1", "action": "request", "question": "Confirmas?"}, "needs_clarification"),
    ]
    for name, arguments, status in cases:
        store = FakeEventStore()
        result = ToolRuntime(lambda: nullcontext(store)).invoke(
            ToolInvocation(
                name=name,
                arguments=arguments,
                context=ToolContext(source="test"),
            )
        )
        assert result.status == status
        assert result.events_emitted


def test_runtime_applies_trace_idempotency_and_normalizes_errors() -> None:
    store = FakeEventStore()
    runtime = ToolRuntime(lambda: nullcontext(store))
    result = runtime.invoke(
        ToolInvocation(
            name="event_capture",
            arguments={"user_id": "u1", "normalized_text": "hoy comi arroz"},
            context=ToolContext(
                source="test", trace_id="trace-1", idempotency_key="request-1"
            ),
        )
    )
    assert result.meta.trace_id == "trace-1"
    assert store.appended is not None
    assert store.appended.idempotency_key == "request-1"
    assert store.appended.metadata.trace_id == "trace-1"

    rejected = runtime.invoke(
        ToolInvocation(name="missing", arguments={}, context=ToolContext(source="test"))
    )
    assert rejected.status == "rejected"
    assert rejected.error and rejected.error.code == "invalid_invocation"


def test_event_capture_blocks_safety_risk_without_redundant_decision_fields() -> None:
    store = FakeEventStore()
    result = ToolRuntime(lambda: nullcontext(store)).invoke(
        ToolInvocation(
            name="event_capture",
            arguments={"user_id": "u1", "normalized_text": "tengo dolor en el pecho fuerte"},
            context=ToolContext(source="test"),
        )
    )
    assert result.status == "blocked"
    assert result.events_emitted == []
    assert store.appended is None
    assert not {"selected_skill", "capture_entity_type", "event_type_candidate"} & set(result.data)


class FakeEventStore:
    appended: UserEventEnvelope | None = None

    def append(self, event: UserEventEnvelope) -> UserEventEnvelope:
        self.appended = event.model_copy(update={"event_seq": 1})
        return self.appended
