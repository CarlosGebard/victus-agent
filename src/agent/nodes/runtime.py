from __future__ import annotations

from agent.state import VictusGraphState
from application.ports.llm import LLMClient, LLMRequest
from victus_routing.normalizer import normalize_text
from victus_routing.router import IntentRouter
from victus_routing.safety_gate import SafetyGate


def normalize_request(state: VictusGraphState) -> VictusGraphState:
    request = dict(state.get("request", {}))
    raw_text = request.get("raw_text", "")
    request["normalized_text"] = normalize_text(raw_text)
    return _merge(state, request=request, node_name="normalize_request")


def safety_precheck(state: VictusGraphState) -> VictusGraphState:
    request = state.get("request", {})
    normalized_text = request.get("normalized_text") or normalize_text(request.get("raw_text", ""))
    result = SafetyGate().check(normalized_text)
    status = "ok"
    if result.severity in {"high", "urgent"}:
        status = "blocked"
    elif result.severity == "medium":
        status = "warning"

    return _merge(
        state,
        safety={
            "status": status,
            "reasons": [result.reason] if result.reason else [],
        },
        node_name="safety_precheck",
    )


def route_intent(router: IntentRouter):
    def node(state: VictusGraphState) -> VictusGraphState:
        request = state.get("request", {})
        text = request.get("raw_text", "")
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
                        "content": "You compose concise, safe Victus runtime responses.",
                    },
                    {
                        "role": "user",
                        "content": (
                            "Route: "
                            f"{intent.get('target_node', 'unknown')}\n"
                            f"Input: {request.get('raw_text', '')}"
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


def _merge(state: VictusGraphState, *, node_name: str, **updates: object) -> VictusGraphState:
    audit = dict(state.get("audit", {}))
    audit.setdefault("node_path", [])
    audit.setdefault("events_emitted", [])
    audit.setdefault("warnings", [])
    audit.setdefault("errors", [])
    audit["node_path"] = [*audit["node_path"], node_name]
    return {**state, **updates, "audit": audit}
