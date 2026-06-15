from __future__ import annotations

from typing import Protocol

from agent.nodes.runtime import _merge
from agent.state import VictusGraphState
from domain.session_context.models import BootstrapContext


class SessionContextReader(Protocol):
    def get_latest_summary(self, conversation_id: str): ...

    def get_pending_interaction(self, conversation_id: str): ...


def context_bootstrap(repository: SessionContextReader | None = None):
    def node(state: VictusGraphState) -> VictusGraphState:
        request = dict(state.get("request", {}))
        raw_text = request.get("raw_text", "")
        conversation_id = request.get("conversation_id")
        summary = None
        pending = None

        if repository and conversation_id:
            summary = repository.get_latest_summary(conversation_id)
            pending = repository.get_pending_interaction(conversation_id)

        routing_query = _build_routing_query(raw_text, pending)
        request["routing_query"] = routing_query
        bootstrap = BootstrapContext(
            conversation_id=conversation_id,
            summary=summary,
            pending_interaction=pending,
            routing_query=routing_query,
        )
        session_context = dict(state.get("session_context", {}))
        if conversation_id:
            session_context["conversation_id"] = conversation_id
        if summary:
            session_context["summary"] = summary
        if pending:
            session_context["pending_interaction"] = pending
        session_context["bootstrap"] = bootstrap

        return _merge(
            state,
            request=request,
            session_context=session_context,
            node_name="context_bootstrap",
        )

    return node


def _build_routing_query(raw_text: str, pending: object | None) -> str:
    if not pending:
        return raw_text
    assistant_prompt = getattr(pending, "assistant_prompt", "")
    expected = getattr(pending, "expected_user_response", "")
    resume_graph = getattr(pending, "resume_graph", None)
    resume_node = getattr(pending, "resume_node", None)
    resume_target = ".".join(part for part in [resume_graph, resume_node] if part)
    return (
        "Pending interaction context:\n"
        f"Assistant prompt: {assistant_prompt}\n"
        f"Expected user response: {expected}\n"
        f"Resume target: {resume_target or 'unspecified'}\n"
        f"Current user message: {raw_text}"
    )
