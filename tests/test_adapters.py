import asyncio

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.types import Command

from adapters.cli.commands import inspect_tool, list_tool_data
from adapters.http.app import create_app as create_chat_app
from adapters.langgraph.graph import build_graph
from adapters.mcp.discovery import discover_tools
from tools.contracts import ClarificationRequest, ToolMeta, ToolResult
from victus_platform.llm.contracts import LLMRequest, LLMResponse
from victus_platform.llm.litellm_client import LiteLLMClient


def test_langgraph_executes_runtime_and_blocks_unsafe_turns() -> None:
    allowed = asyncio.run(
        build_graph().ainvoke(
            {
                "request": {
                    "request_id": "r1",
                    "user_id": "u1",
                    "conversation_id": "c1",
                    "raw_text": "hoy comi arroz",
                }
            }
        )
    )
    assert allowed["tool_context"]["last_tool_result"]["data"]["capture_action"] == "log_meal"
    assert allowed["audit"]["node_path"][-1] == "finalize_turn"

    blocked = asyncio.run(
        build_graph(safety_client=BlockedSafetyClient()).ainvoke(
            {
                "request": {
                    "request_id": "r2",
                    "user_id": "u1",
                    "conversation_id": "c2",
                    "raw_text": "I am going to hurt myself",
                }
            }
        )
    )
    assert blocked["safety"]["status"] == "blocked"
    assert blocked["tool_context"]["allowed_tools"] == []
    assert "last_tool_result" not in blocked["tool_context"]


def test_langgraph_model_selection_enforces_identity_and_exact_text() -> None:
    client = SequenceClient(
        [
            LLMResponse(
                text="",
                tool_calls=[
                    {
                        "id": "call-1",
                        "name": "event_capture",
                        "arguments": {"user_id": "u1", "normalized_text": "changed"},
                    }
                ],
            ),
            LLMResponse(text="Registrado.", tool_calls=[]),
        ]
    )
    runtime = RecordingRuntime()
    result = asyncio.run(
        build_graph(llm_client=client, tool_runtime=runtime).ainvoke(
            {
                "request": {
                    "request_id": "r1",
                    "user_id": "u1",
                    "conversation_id": "c1",
                    "raw_text": "Hoy comí arroz",
                }
            }
        )
    )
    assert runtime.invocations[0].arguments["normalized_text"] == "Hoy comí arroz"
    assert result["tool_context"]["last_tool_result"]["status"] == "success"
    assert result["response"]["user_message"] == "Registrado."

    changed_identity = asyncio.run(
        build_graph(
            llm_client=SequenceClient(
                [
                    LLMResponse(
                        text="",
                        tool_calls=[
                            {
                                "name": "event_capture",
                                "arguments": {"user_id": "other", "normalized_text": "x"},
                            }
                        ],
                    )
                ]
            )
        ).ainvoke(
            {
                "request": {
                    "request_id": "r2",
                    "user_id": "u1",
                    "conversation_id": "c2",
                    "raw_text": "texto",
                }
            }
        )
    )
    assert changed_identity["response"]["mode"] == "error"
    assert "identity" in changed_identity["response"]["internal_notes"][0]


def test_langgraph_confirmation_resumes_once_and_memory_is_user_scoped() -> None:
    saver = InMemorySaver()
    store = InMemoryStore()
    runtime = RecordingRuntime()
    client = SequenceClient(
        [
            LLMResponse(
                text="",
                tool_calls=[
                    {
                        "id": "call-1",
                        "name": "planning",
                        "arguments": {"user_id": "u1", "action": "adjust_goal", "goal_id": "g1", "patch": {}},
                    }
                ],
            ),
            LLMResponse(text="Meta ajustada.", tool_calls=[]),
        ]
    )
    graph = build_graph(llm_client=client, tool_runtime=runtime, checkpointer=saver, store=store)
    config = {"configurable": {"thread_id": "c-confirm", "user_id": "u1"}}
    paused = asyncio.run(
        graph.ainvoke(
            {
                "request": {
                    "request_id": "r1",
                    "user_id": "u1",
                    "conversation_id": "c-confirm",
                    "raw_text": "ajusta mi meta",
                }
            },
            config=config,
        )
    )
    assert paused["__interrupt__"][0].value["kind"] == "confirmation"
    resumed = asyncio.run(graph.ainvoke(Command(resume={"accepted": True}), config=config))
    assert resumed["response"]["user_message"] == "Meta ajustada."
    assert len(runtime.invocations) == 1

    declined_runtime = RecordingRuntime()
    declined_graph = build_graph(
        llm_client=SequenceClient(
            [
                LLMResponse(
                    text="",
                    tool_calls=[
                        {
                            "name": "planning",
                            "arguments": {"user_id": "u1", "action": "end_session", "session_id": "s1"},
                        }
                    ],
                )
            ]
        ),
        tool_runtime=declined_runtime,
        checkpointer=InMemorySaver(),
    )
    declined_config = {"configurable": {"thread_id": "declined", "user_id": "u1"}}
    asyncio.run(
        declined_graph.ainvoke(
            {
                "request": {
                    "request_id": "declined",
                    "user_id": "u1",
                    "conversation_id": "declined",
                    "raw_text": "termina la sesión",
                }
            },
            config=declined_config,
        )
    )
    declined = asyncio.run(
        declined_graph.ainvoke(Command(resume={"accepted": False}), config=declined_config)
    )
    assert declined["response"]["user_message"] == "Acción cancelada."
    assert declined_runtime.invocations == []

    memory_graph = build_graph(checkpointer=InMemorySaver(), store=store)
    asyncio.run(
        memory_graph.ainvoke(
            {
                "request": {
                    "request_id": "remember",
                    "user_id": "u1",
                    "conversation_id": "memory-1",
                    "raw_text": "recuerda que prefiero respuestas breves",
                }
            },
            config={"configurable": {"thread_id": "memory-1", "user_id": "u1"}},
        )
    )
    same_user = asyncio.run(
        memory_graph.ainvoke(
            {
                "request": {
                    "request_id": "recall",
                    "user_id": "u1",
                    "conversation_id": "memory-2",
                    "raw_text": "hola",
                }
            },
            config={"configurable": {"thread_id": "memory-2", "user_id": "u1"}},
        )
    )
    other_user = asyncio.run(
        memory_graph.ainvoke(
            {
                "request": {
                    "request_id": "other",
                    "user_id": "u2",
                    "conversation_id": "memory-3",
                    "raw_text": "hola",
                }
            },
            config={"configurable": {"thread_id": "memory-3", "user_id": "u2"}},
        )
    )
    assert same_user["memory"]["recalled"][0]["content"] == "prefiero respuestas breves"
    assert other_user["memory"]["recalled"] == []


def test_langgraph_clarification_survives_checkpoint_resume() -> None:
    runtime = SequenceRuntime(
        [
            ToolResult(
                status="needs_clarification",
                clarification=ClarificationRequest(
                    missing_fields=["time"],
                    question="¿A qué hora?",
                    expected_answer_type="time",
                ),
            ),
            ToolResult(status="success", meta=ToolMeta(trace_id="trace-2")),
        ]
    )
    client = SequenceClient(
        [
            LLMResponse(text="", tool_calls=[{"name": "event_capture", "arguments": {"user_id": "u1"}}]),
            LLMResponse(text="", tool_calls=[{"name": "event_capture", "arguments": {"user_id": "u1"}}]),
            LLMResponse(text="Registrado con la hora.", tool_calls=[]),
        ]
    )
    graph = build_graph(llm_client=client, tool_runtime=runtime, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "clarify", "user_id": "u1"}}
    paused = asyncio.run(
        graph.ainvoke(
            {
                "request": {
                    "request_id": "clarify-1",
                    "user_id": "u1",
                    "conversation_id": "clarify",
                    "raw_text": "comí arroz",
                }
            },
            config=config,
        )
    )
    assert paused["__interrupt__"][0].value["question"] == "¿A qué hora?"
    resumed = asyncio.run(graph.ainvoke(Command(resume={"answer": "a las 13:00"}), config=config))
    assert resumed["response"]["user_message"] == "Registrado con la hora."
    assert runtime.invocations[-1].arguments["normalized_text"] == "a las 13:00"


def test_chat_api_authenticates_and_enforces_thread_ownership() -> None:
    from starlette.testclient import TestClient

    graph = build_graph(checkpointer=InMemorySaver(), store=InMemoryStore())
    with TestClient(create_chat_app(graph=graph, identity_resolver=TokenIdentityResolver())) as client:
        first = client.post(
            "/chat",
            headers={"Authorization": "Bearer user-one"},
            json={"conversation_id": "owned", "request_id": "r1", "message": "hoy comi arroz"},
        )
        forbidden = client.post(
            "/chat",
            headers={"Authorization": "Bearer user-two"},
            json={"conversation_id": "owned", "request_id": "r2", "message": "hola"},
        )
    assert first.status_code == 200
    assert first.json()["status"] == "completed"
    assert forbidden.status_code == 403


def test_mcp_discovers_catalog_and_serves_http_health() -> None:
    from starlette.testclient import TestClient

    from adapters.mcp.transport import MCP_PATH, create_app

    assert [tool.name for tool in discover_tools()][0] == "event_capture"
    with TestClient(create_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["transport"] == "streamable_http"
    assert MCP_PATH == "/mcp"


def test_cli_reads_catalog_without_alternate_execution_metadata() -> None:
    assert list_tool_data()[0]["name"] == "event_capture"
    inspected = inspect_tool("event_capture")
    assert inspected["input_schema"]["title"] == "EventCaptureInput"


def test_litellm_proxy_alias_maps_to_openai_compatible_provider(monkeypatch) -> None:
    monkeypatch.setenv("LITELLM_PROXY_API_BASE", "http://litellm:4000/v1")
    kwargs = LiteLLMClient()._kwargs(
        LLMRequest(
            operation="test.proxy_alias",
            model="litellm_proxy/gemini-flash-lite",
            messages=[{"role": "user", "content": "hola"}],
        )
    )
    assert kwargs["model"] == "openai/gemini-flash-lite"
    assert kwargs["api_base"] == "http://litellm:4000/v1"


class BlockedSafetyClient:
    def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text="unsafe\nS11")

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        raise AssertionError("unexpected async safety call")


class SequenceClient:
    def __init__(self, responses: list[LLMResponse]) -> None:
        self.responses = responses

    def complete(self, request: LLMRequest) -> LLMResponse:
        raise AssertionError("unexpected sync model call")

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        return self.responses.pop(0)


class RecordingRuntime:
    def __init__(self) -> None:
        self.invocations = []

    async def invoke_async(self, invocation):
        self.invocations.append(invocation)
        return ToolResult(status="success", meta=ToolMeta(trace_id="trace-1"))


class SequenceRuntime(RecordingRuntime):
    def __init__(self, results: list[ToolResult]) -> None:
        super().__init__()
        self.results = results

    async def invoke_async(self, invocation):
        self.invocations.append(invocation)
        return self.results.pop(0)


class TokenIdentityResolver:
    async def resolve(self, token: str) -> str | None:
        return {"user-one": "u1", "user-two": "u2"}.get(token)
