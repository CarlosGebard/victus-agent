from contextlib import nullcontext

from domain.events.envelope import UserEventEnvelope
from tools.catalog import get_tool, list_tools
from tools.contracts import ToolContext, ToolIdentity, ToolInvocation, ToolServices
from tools.profile.contract import ProfileGatewayResponse
from tools.runtime import ToolRuntime
from ops.scripts.mcp_intent_eval import function_tools, score_case


def test_catalog_and_capabilities_share_one_runtime() -> None:
    definitions = list_tools(exposure="mcp")
    names = [definition.name for definition in definitions]
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
    assert all("Use " in definition.description for definition in definitions)
    assert all("Do not use" in definition.description for definition in definitions)
    assert "concrete event" in get_tool("event_capture").description
    assert "durable profile information" in get_tool("profile_update").description
    assert "Continuation mechanism" in get_tool("clarification").description
    assert "read-only" in get_tool("recuperar_perfil").description

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


def test_authenticated_tool_without_user_id_schema_uses_context_identity() -> None:
    import asyncio

    runtime = ToolRuntime(
        services=ToolServices({"profile_gateway": FakeProfileGateway()}),
    )
    result = asyncio.run(
        runtime.invoke_async(
            ToolInvocation(
                name="recuperar_perfil",
                arguments={},
                context=ToolContext(
                    source="langgraph",
                    identity=ToolIdentity(subject="u1", authenticated=True),
                ),
            )
        )
    )
    assert result.status == "success"


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


def test_intent_eval_uses_catalog_and_checks_exact_input() -> None:
    tools = function_tools()
    assert [item["function"]["name"] for item in tools] == [
        definition.name for definition in list_tools(exposure="mcp")
    ]
    case = {
        "id": "meal",
        "input": "Hoy comi arroz",
        "expected_tool": "event_capture",
        "exact_input_argument": "normalized_text",
    }
    passed = score_case(
        case,
        [
            {
                "name": "event_capture",
                "arguments": {
                    "user_id": "mcp-smoke-user",
                    "normalized_text": "Hoy comi arroz",
                },
            }
        ],
        user_id="mcp-smoke-user",
    )
    changed = score_case(
        case,
        [
            {
                "name": "event_capture",
                "arguments": {
                    "user_id": "mcp-smoke-user",
                    "normalized_text": "El usuario comio arroz",
                },
            }
        ],
        user_id="mcp-smoke-user",
    )
    assert passed["passed"] is True
    assert changed["passed"] is False


class FakeEventStore:
    appended: UserEventEnvelope | None = None

    def append(self, event: UserEventEnvelope) -> UserEventEnvelope:
        self.appended = event.model_copy(update={"event_seq": 1})
        return self.appended


class FakeProfileGateway:
    async def fetch(self) -> ProfileGatewayResponse:
        return ProfileGatewayResponse(status_code=200, payload={"id": "u1"})
