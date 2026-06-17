from __future__ import annotations

from agent.state import VictusGraphState
from agent.prompts.compose_response import (
    COMPOSE_RESPONSE_SYSTEM_PROMPT,
    compose_response_user_prompt,
)
from application.ports.llm import LLMClient, LLMRequest
from application.routing.normalizer import normalize_text
from application.routing.router import IntentRouter


def normalize_request(state: VictusGraphState) -> VictusGraphState:
    request = dict(state.get("request", {}))
    original_text = str(request.get("original_text") or request.get("raw_text", ""))
    existing_working_text = str(request.get("working_text") or "")
    normalized_text = existing_working_text or normalize_text(original_text)
    request = _clean_request(request)
    request["original_text"] = original_text
    request["working_text"] = normalized_text
    return _merge(
        state,
        request=request,
        node_name="normalize_request",
        transform={"step": "normalize", "input": original_text, "output": normalized_text},
    )


def safety_precheck(*, llm_client: LLMClient | None = None, model: str | None = None):
    def node(state: VictusGraphState) -> VictusGraphState:
        request = state.get("request", {})
        text = str(
            request.get("working_text")
            or request.get("original_text")
            or request.get("raw_text")
            or ""
        )
        if not llm_client or not model:
            return _merge(state, safety=_allowed_safety(), node_name="safety_precheck")

        result = llm_client.complete(
            LLMRequest(
                operation="agent.safety_precheck.llama_guard",
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": _llama_guard_prompt(text),
                    }
                ],
                temperature=0,
                max_tokens=32,
                metadata={"guard": "llama_guard_3_1b"},
            )
        )
        safety = _safety_from_llama_guard(result.text)
        return _merge(state, safety=safety, node_name="safety_precheck")

    return node


def _llama_guard_prompt(user_text: str) -> str:
    return (
        "Task: Check if the user message is safe or unsafe. "
        "Respond only with 'safe' or 'unsafe' followed by the violated category if any.\n\n"
        f"User message:\n{user_text}"
    )


def _safety_from_llama_guard(output: str) -> dict[str, object]:
    normalized = output.strip().lower()
    if normalized.startswith("unsafe"):
        categories = ["self_harm"] if "s11" in normalized or "self-harm" in normalized else ["unsafe"]
        return {
            "status": "blocked",
            "reasons": ["llama_guard_unsafe"],
            "decision": "route_to_safety_triage",
            "severity": "high",
            "categories": categories,
            "matched_rules": [],
            "reason_codes": ["llama_guard_unsafe"],
            "blocked_tools": ["planning", "event_capture", "profile_update"],
            "allowed_next_route": "SafetyTriageRoute",
            "audit_required": True,
        }
    return _allowed_safety()


def _allowed_safety() -> dict[str, object]:
    return {
        "status": "ok",
        "reasons": [],
        "decision": "allow",
        "severity": "none",
        "categories": ["none"],
        "matched_rules": [],
        "reason_codes": [],
        "blocked_tools": [],
        "allowed_next_route": "IntentRouter",
        "audit_required": False,
    }


def route_intent(router: IntentRouter):
    def node(state: VictusGraphState) -> VictusGraphState:
        safety = state.get("safety", {})
        allowed_next_route = safety.get("allowed_next_route")
        if allowed_next_route in {"SafetyTriageRoute", "EmergencySupportResponse"}:
            intent = {
                "primary_intent": "risk_medical_unsafe",
                "confidence": 1.0,
                "target_node": allowed_next_route,
                "subintents": list(safety.get("categories", [])),
                "rationale": safety.get("decision", "safety"),
            }
            return _merge(state, intent=intent, node_name="route_intent")

        request = state.get("request", {})
        text = str(request.get("working_text") or request.get("original_text", ""))
        decision = router.route(text)
        intent = {
            "primary_intent": decision.intent_type or decision.decision,
            "confidence": decision.confidence,
            "target_node": decision.route,
            "subintents": list(decision.secondary_intents),
            "rationale": decision.decision,
        }
        if decision.requires_clarification and decision.clarification_question:
            response = {
                "mode": "clarification",
                "user_message": decision.clarification_question,
                "internal_notes": ["router requested clarification"],
            }
            return _merge(state, intent=intent, response=response, node_name="route_intent")
        return _merge(state, intent=intent, node_name="route_intent")

    return node


def compose_response(*, llm_client: LLMClient | None = None, model: str | None = None):
    if not llm_client or not model:
        return _compose_response_sync

    async def node(state: VictusGraphState) -> VictusGraphState:
        existing_response = state.get("response", {})
        if existing_response.get("user_message"):
            return _merge(state, node_name="compose_response")

        safety = state.get("safety", {})
        intent = state.get("intent", {})
        if safety.get("status") == "blocked":
            return _merge(
                state,
                response=_blocked_response(list(safety.get("reasons", []))),
                node_name="compose_response",
            )

        request = state.get("request", {})
        llm_response = await llm_client.acomplete(
            LLMRequest(
                operation="agent.compose_response",
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": COMPOSE_RESPONSE_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": compose_response_user_prompt(
                            route=str(intent.get("target_node", "unknown")),
                            raw_text=str(request.get("original_text", "")),
                        ),
                    },
                ],
                temperature=0,
                max_tokens=300,
                metadata={"target_node": intent.get("target_node", "unknown")},
            )
        )
        response = {
            "mode": "final",
            "user_message": llm_response.text,
            "internal_notes": ["response composed with llm port"],
        }
        return _merge(state, response=response, node_name="compose_response")


    return node


def _compose_response_sync(state: VictusGraphState) -> VictusGraphState:
    existing_response = state.get("response", {})
    if existing_response.get("user_message"):
        return _merge(state, node_name="compose_response")

    safety = state.get("safety", {})
    intent = state.get("intent", {})
    if safety.get("status") == "blocked":
        return _merge(
            state,
            response=_blocked_response(list(safety.get("reasons", []))),
            node_name="compose_response",
        )

    response = {
        "mode": "final",
        "user_message": f"Route selected: {intent.get('target_node', 'unknown')}",
        "internal_notes": ["deterministic response composer"],
    }
    return _merge(state, response=response, node_name="compose_response")


def _blocked_response(reasons: list[str]) -> dict[str, object]:
    return {
        "mode": "blocked",
        "user_message": (
            "No puedo ayudar con esa accion de forma segura. Busca apoyo medico urgente "
            "si los sintomas son graves o inmediatos."
        ),
        "internal_notes": reasons,
    }


def _clean_request(request: dict[str, object]) -> dict[str, object]:
    for key in ("raw_text", "normalized_text", "english_safety_text", "routing_query"):
        request.pop(key, None)
    return request


def _merge(
    state: VictusGraphState,
    *,
    node_name: str,
    transform: dict[str, str] | None = None,
    **updates: object,
) -> VictusGraphState:
    audit = dict(state.get("audit", {}))
    audit.setdefault("node_path", [])
    audit.setdefault("events_emitted", [])
    audit.setdefault("warnings", [])
    audit.setdefault("errors", [])
    audit.setdefault("transforms", [])
    audit["node_path"] = [*audit["node_path"], node_name]
    if transform:
        audit["transforms"] = [*audit["transforms"], transform]
    return {**state, **updates, "audit": audit}
