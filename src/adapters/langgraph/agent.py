from __future__ import annotations

import json
from typing import Any

from langgraph.types import interrupt
from langchain_core.messages import RemoveMessage

from adapters.langgraph.context import _merge
from adapters.langgraph.contracts import ProposedAction
from adapters.langgraph.state import GRAPH_VERSION, VictusGraphState
from tools.catalog import get_tool, list_tools
from tools.contracts import ToolContext, ToolIdentity, ToolInvocation
from tools.runtime import ToolRuntime
from victus_platform.llm.contracts import LLMClient, LLMRequest

MAX_TOOL_LOOPS = 4
EXACT_TEXT_TOOLS = frozenset({"event_capture", "profile_update"})


def function_tools(allowed_tools: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": definition.name,
                "description": definition.description,
                "parameters": definition.input_schema,
            },
        }
        for definition in list_tools(exposure="langgraph")
        if definition.name in allowed_tools
    ]


def ingest_turn(state: VictusGraphState) -> VictusGraphState:
    request = state.get("request", {})
    user_id = str(request.get("user_id") or "")
    conversation_id = str(request.get("conversation_id") or "")
    if not user_id or not conversation_id:
        raise ValueError("authenticated user_id and conversation_id are required")
    version = state.get("graph_version")
    if version and version != GRAPH_VERSION:
        raise ValueError("checkpoint graph version is incompatible")
    return _merge(
        state,
        messages=[
            {
                "role": "user",
                "content": str(request.get("original_text") or request.get("raw_text") or ""),
            }
        ],
        response={},
        tool_context={"loop_count": 0, "tool_results": []},
        graph_version=GRAPH_VERSION,
        node_name="ingest_turn",
    )


def agent_decision(*, llm_client: LLMClient | None, model: str):
    async def node(state: VictusGraphState) -> VictusGraphState:
        tool_context = dict(state.get("tool_context", {}))
        loop_count = int(tool_context.get("loop_count", 0))
        if loop_count >= MAX_TOOL_LOOPS:
            return _error_response(state, "tool loop limit reached", "loop_limit")

        allowed = list(tool_context.get("allowed_tools", []))
        request = state.get("request", {})
        if tool_context.get("last_tool_result") and llm_client is None:
            result = tool_context["last_tool_result"]
            events = result.get("events_emitted", [])
            message = "Acción completada."
            if events:
                message = f"Acción completada y registrada ({len(events)} evento(s))."
            return _merge(
                state,
                response={"mode": "final", "user_message": message, "internal_notes": []},
                node_name="agent_decision",
            )
        if llm_client is None:
            calls = [{"name": "event_capture", "arguments": {}}]
            text = ""
        else:
            response = await llm_client.acomplete(
                LLMRequest(
                    operation="agent.decision",
                    model=model,
                    messages=[
                        {"role": "system", "content": _decision_prompt(state)},
                        *[_message_dict(item) for item in state.get("messages", [])[-12:]],
                    ],
                    temperature=0,
                    max_tokens=500,
                    tools=function_tools(allowed),
                    tool_choice="auto",
                    metadata={
                        "conversation_id": request.get("conversation_id"),
                        "request_id": request.get("request_id"),
                    },
                )
            )
            calls = response.tool_calls
            text = response.text

        if not calls:
            return _merge(
                state,
                response={"mode": "final", "user_message": text or "Entendido.", "internal_notes": []},
                tool_context={**tool_context, "proposed_action": {}},
                node_name="agent_decision",
            )
        if len(calls) != 1:
            return _error_response(
                state,
                "only one tool call is accepted per decision",
                "multiple_tool_calls",
            )

        call = calls[0]
        name = str(call.get("name") or "")
        if name not in allowed:
            return _error_response(
                state,
                "model selected a tool outside the allowed catalog",
                "tool_not_allowed",
            )
        arguments = call.get("arguments")
        if not isinstance(arguments, dict) or "_invalid_json" in arguments:
            return _error_response(state, "model returned invalid tool arguments", "invalid_arguments")
        supplied_user_id = arguments.get("user_id")
        user_id = str(request.get("user_id"))
        if supplied_user_id is not None and supplied_user_id != user_id:
            return _error_response(
                state,
                "model attempted to change authenticated identity",
                "identity_mismatch",
            )
        arguments = dict(arguments)
        if "user_id" in get_tool(name).input_schema.get("properties", {}):
            arguments["user_id"] = user_id
        if name in EXACT_TEXT_TOOLS:
            arguments["normalized_text"] = str(request.get("original_text") or "")
        proposal = ProposedAction(
            tool_name=name,
            arguments=arguments,
            call_id=call.get("id"),
            requires_confirmation=_requires_confirmation(name, arguments),
        )
        return _merge(
            state,
            tool_context={
                **tool_context,
                "proposed_action": proposal.model_dump(mode="json"),
                "loop_count": loop_count + 1,
            },
            node_name="agent_decision",
        )

    return node


def confirmation_interrupt(state: VictusGraphState) -> VictusGraphState:
    proposal = state.get("tool_context", {}).get("proposed_action", {})
    answer = interrupt(
        {
            "kind": "confirmation",
            "question": f"¿Confirmas ejecutar {proposal.get('tool_name', 'esta acción')}?",
            "tool_name": proposal.get("tool_name"),
        }
    )
    accepted = answer if isinstance(answer, bool) else bool((answer or {}).get("accepted"))
    tool_context = dict(state.get("tool_context", {}))
    tool_context["confirmation"] = {"accepted": accepted}
    if not accepted:
        return _merge(
            state,
            tool_context=tool_context,
            response={
                "mode": "final",
                "user_message": "Acción cancelada.",
                "internal_notes": ["confirmation_declined"],
            },
            node_name="confirmation_interrupt",
        )
    return _merge(state, tool_context=tool_context, node_name="confirmation_interrupt")


def execute_tool(runtime: ToolRuntime):
    async def node(state: VictusGraphState) -> VictusGraphState:
        request = state.get("request", {})
        tool_context = dict(state.get("tool_context", {}))
        proposal = tool_context.get("proposed_action", {})
        result = await runtime.invoke_async(
            ToolInvocation(
                name=str(proposal.get("tool_name") or ""),
                arguments=dict(proposal.get("arguments") or {}),
                context=ToolContext(
                    source="langgraph",
                    identity=ToolIdentity(
                        subject=str(request.get("user_id")),
                        authenticated=True,
                    ),
                    trace_id=str(request.get("trace_id") or "") or None,
                    idempotency_key=(
                        f"{request.get('conversation_id')}:{request.get('request_id')}:"
                        f"{tool_context.get('loop_count', 0)}:{proposal.get('tool_name')}"
                    ),
                ),
            )
        )
        dumped = {"tool_name": proposal.get("tool_name"), **result.model_dump(mode="json")}
        results = [*tool_context.get("tool_results", []), dumped]
        return _merge(
            state,
            tool_context={**tool_context, "last_tool_result": dumped, "tool_results": results},
            messages=[
                {
                    "role": "tool",
                    "content": json.dumps(dumped, ensure_ascii=False),
                    "tool_call_id": proposal.get("call_id") or "tool",
                }
            ],
            node_name="execute_tool",
        )

    return node


def clarification_interrupt(state: VictusGraphState) -> VictusGraphState:
    result = state.get("tool_context", {}).get("last_tool_result", {})
    clarification = result.get("clarification") or {}
    answer = interrupt(
        {
            "kind": "clarification",
            "question": clarification.get("question") or "Necesito más información.",
            "missing_fields": clarification.get("missing_fields", []),
            "expected_answer_type": clarification.get("expected_answer_type", "free_text"),
        }
    )
    request = dict(state.get("request", {}))
    request["original_text"] = str(answer.get("answer") if isinstance(answer, dict) else answer)
    request["working_text"] = request["original_text"]
    tool_context = dict(state.get("tool_context", {}))
    tool_context["proposed_action"] = {}
    tool_context.pop("last_tool_result", None)
    return _merge(
        state,
        request=request,
        messages=[{"role": "user", "content": request["original_text"]}],
        tool_context=tool_context,
        node_name="clarification_interrupt",
    )


def finalize_turn(state: VictusGraphState) -> VictusGraphState:
    messages = state.get("messages", [])
    removable = [
        RemoveMessage(id=message.id)
        for message in messages[:-20]
        if getattr(message, "id", None)
    ]
    memory = dict(state.get("memory", {}))
    if removable:
        summary_source = " ".join(str(getattr(item, "content", "")) for item in messages[:-20])
        previous = str(memory.get("compact_summary") or "")
        memory["compact_summary"] = f"{previous} {summary_source}".strip()[-1_000:]
    result = _merge(
        state,
        messages=removable,
        memory=memory,
        node_name="finalize_turn",
    )
    audit = dict(result.get("audit", {}))
    audit["node_path"] = audit.get("node_path", [])[-100:]
    audit["events_emitted"] = audit.get("events_emitted", [])[-100:]
    audit["warnings"] = audit.get("warnings", [])[-50:]
    audit["errors"] = audit.get("errors", [])[-50:]
    audit["transforms"] = audit.get("transforms", [])[-50:]
    result["audit"] = audit
    return result


def compose_final_response(state: VictusGraphState) -> VictusGraphState:
    if state.get("response", {}).get("user_message"):
        return _merge(state, node_name="compose_final_response")
    result = state.get("tool_context", {}).get("last_tool_result", {})
    status = result.get("status")
    if status == "success":
        events = result.get("events_emitted", [])
        message = "Acción completada."
        if events:
            message = f"Acción completada y registrada ({len(events)} evento(s))."
        mode = "final"
    elif status == "blocked":
        message, mode = "No puedo ejecutar esa acción de forma segura.", "blocked"
    else:
        error = result.get("error") or {}
        message, mode = str(error.get("message") or "No fue posible completar la acción."), "error"
    return _merge(
        state,
        response={"mode": mode, "user_message": message, "internal_notes": []},
        node_name="compose_final_response",
    )


def route_after_decision(state: VictusGraphState) -> str:
    if state.get("response", {}).get("user_message"):
        return "response"
    proposal = state.get("tool_context", {}).get("proposed_action", {})
    return "confirm" if proposal.get("requires_confirmation") else "execute"


def route_after_confirmation(state: VictusGraphState) -> str:
    return "response" if state.get("response", {}).get("user_message") else "execute"


def route_after_execution(state: VictusGraphState) -> str:
    status = state.get("tool_context", {}).get("last_tool_result", {}).get("status")
    if status == "needs_clarification":
        return "clarify"
    if status == "success":
        return "decide"
    return "response"


def _decision_prompt(state: VictusGraphState) -> str:
    context = {
        "authenticated_user_id": state.get("request", {}).get("user_id"),
        "original_text": state.get("request", {}).get("original_text"),
        "memories": state.get("memory", {}).get("recalled", []),
        "compact_summary": state.get("memory", {}).get("compact_summary", ""),
        "projections": state.get("projections", {}),
        "previous_tool_result": state.get("tool_context", {}).get("last_tool_result"),
    }
    return (
        "Eres el agente Victus. Selecciona como máximo una herramienta canónica o responde sin "
        "herramienta. Nunca cambies la identidad autenticada. Conserva el texto original exacto "
        "en normalized_text. Si ya existe un resultado exitoso, responde al usuario sin repetir la "
        f"mutación. Contexto acotado: {json.dumps(context, ensure_ascii=False, default=str)}"
    )


def _requires_confirmation(name: str, arguments: dict[str, Any]) -> bool:
    if name == "planning":
        return arguments.get("action") in {"adjust_goal", "save_artifact", "end_session"}
    text = str(arguments.get("normalized_text") or "").lower()
    return any(term in text for term in ("elimina", "borra", "quita", "remove", "delete"))


def _error_response(state: VictusGraphState, message: str, code: str) -> VictusGraphState:
    return _merge(
        state,
        response={"mode": "error", "user_message": message, "internal_notes": [code]},
        node_name="agent_decision",
    )


def _message_dict(message: Any) -> dict[str, Any]:
    if isinstance(message, dict):
        return message
    role = getattr(message, "type", "user")
    if role == "human":
        role = "user"
    elif role == "ai":
        role = "assistant"
    return {"role": role, "content": str(getattr(message, "content", ""))}
