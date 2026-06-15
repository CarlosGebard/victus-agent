from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from agent.nodes.runtime import _merge
from agent.state import VictusGraphState
from domain.session_context.models import ActiveTask, ConversationStateSummary, PendingInteractionState


class SessionContextWriter(Protocol):
    def save_summary(self, summary: ConversationStateSummary) -> None: ...

    def save_pending_interaction(self, pending: PendingInteractionState) -> None: ...

    def clear_pending_interaction(self, conversation_id: str) -> None: ...


def summarize_after_response(repository: SessionContextWriter | None = None):
    def node(state: VictusGraphState) -> VictusGraphState:
        request = state.get("request", {})
        conversation_id = request.get("conversation_id")
        user_id = request.get("user_id")
        if not conversation_id or not user_id:
            return _merge(state, node_name="summarize_after_response")

        previous = state.get("session_context", {}).get("summary")
        response = state.get("response", {})
        intent = state.get("intent", {})
        now = datetime.now(UTC).isoformat()
        pending = _pending_from_response(
            conversation_id=conversation_id,
            user_id=user_id,
            response=response,
            intent=intent,
            now=now,
        )
        summary = _updated_summary(
            previous=previous,
            conversation_id=conversation_id,
            user_id=user_id,
            raw_text=request.get("original_text", ""),
            response_text=response.get("user_message", ""),
            intent=intent,
            pending=pending,
            now=now,
        )

        if repository:
            repository.save_summary(summary)
            if pending:
                repository.save_pending_interaction(pending)
            else:
                repository.clear_pending_interaction(conversation_id)

        session_context = dict(state.get("session_context", {}))
        session_context["updated_summary"] = summary
        if pending:
            session_context["pending_interaction"] = pending

        return _merge(
            state,
            session_context=session_context,
            node_name="summarize_after_response",
        )

    return node


def _pending_from_response(
    *,
    conversation_id: str,
    user_id: str,
    response: dict[str, object],
    intent: dict[str, object],
    now: str,
) -> PendingInteractionState | None:
    if response.get("mode") != "clarification":
        return None
    prompt = str(response.get("user_message", ""))
    return PendingInteractionState(
        conversation_id=conversation_id,
        user_id=user_id,
        pending_kind="question",
        assistant_prompt=prompt,
        expected_user_response="free_text",
        resume_graph=str(intent.get("target_node") or "ClarificationRoute"),
        resume_node=None,
        created_at=now,
        updated_at=now,
    )


def _updated_summary(
    *,
    previous: ConversationStateSummary | None,
    conversation_id: str,
    user_id: str,
    raw_text: str,
    response_text: str,
    intent: dict[str, object],
    pending: PendingInteractionState | None,
    now: str,
) -> ConversationStateSummary:
    target_node = str(intent.get("target_node") or "unknown")
    task_status = "waiting_user" if pending else "completed"
    active_task = ActiveTask(
        task_name=target_node,
        task_status=task_status,
        next_expected_step=pending.expected_user_response if pending else None,
    )
    relevant_context = list(previous.relevant_context if previous else [])
    if raw_text:
        relevant_context = [*relevant_context[-2:], f"Latest user message: {raw_text}"]
    if response_text:
        relevant_context = [*relevant_context[-2:], f"Latest assistant response: {response_text}"]

    return ConversationStateSummary(
        conversation_id=conversation_id,
        user_id=user_id,
        summary_version=previous.summary_version if previous else "session-context-v1",
        user_current_goal=previous.user_current_goal if previous else raw_text,
        current_topic=target_node,
        stable_decisions=list(previous.stable_decisions if previous else []),
        recent_decisions=[f"Routed to {target_node}"],
        active_task=active_task,
        pending_interaction=pending,
        relevant_context=relevant_context,
        last_tool_summary=previous.last_tool_summary if previous else None,
        unresolved_questions=[pending.assistant_prompt] if pending else [],
        should_inject_next_turn=True,
        updated_at=now,
    )
