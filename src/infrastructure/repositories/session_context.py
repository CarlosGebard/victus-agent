from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Connection, delete, select
from sqlalchemy.dialects.postgresql import insert

from infrastructure.db.schema import conversation_state_summaries, pending_interaction_state
from domain.session_context.models import ConversationStateSummary, PendingInteractionState


class SessionContextRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def get_latest_summary(self, conversation_id: str) -> ConversationStateSummary | None:
        row = self.connection.execute(
            select(conversation_state_summaries).where(
                conversation_state_summaries.c.conversation_id == conversation_id
            )
        ).mappings().first()
        return _summary_from_row(dict(row)) if row else None

    def save_summary(self, summary: ConversationStateSummary) -> None:
        values = {
            "conversation_id": summary.conversation_id,
            "user_id": summary.user_id,
            "summary_version": summary.summary_version,
            "summary": _summary_body(summary),
            "should_inject_next_turn": summary.should_inject_next_turn,
            "updated_at": _from_iso(summary.updated_at),
        }
        statement = insert(conversation_state_summaries).values(**values)
        self.connection.execute(
            statement.on_conflict_do_update(
                index_elements=[conversation_state_summaries.c.conversation_id],
                set_=values,
            )
        )

    def get_pending_interaction(self, conversation_id: str) -> PendingInteractionState | None:
        row = self.connection.execute(
            select(pending_interaction_state).where(
                pending_interaction_state.c.conversation_id == conversation_id
            )
        ).mappings().first()
        return _pending_from_row(dict(row)) if row else None

    def save_pending_interaction(self, pending: PendingInteractionState) -> None:
        values = {
            "conversation_id": pending.conversation_id,
            "user_id": pending.user_id,
            "pending_kind": pending.pending_kind,
            "assistant_prompt": pending.assistant_prompt,
            "expected_user_response": pending.expected_user_response,
            "resume_graph": pending.resume_graph,
            "resume_node": pending.resume_node,
            "created_at": _from_iso(pending.created_at),
            "updated_at": _from_iso(pending.updated_at),
        }
        statement = insert(pending_interaction_state).values(**values)
        self.connection.execute(
            statement.on_conflict_do_update(
                index_elements=[pending_interaction_state.c.conversation_id],
                set_=values,
            )
        )

    def clear_pending_interaction(self, conversation_id: str) -> None:
        self.connection.execute(
            delete(pending_interaction_state).where(
                pending_interaction_state.c.conversation_id == conversation_id
            )
        )


def _summary_body(summary: ConversationStateSummary) -> dict[str, Any]:
    payload = summary.model_dump(exclude_none=True)
    for key in ("conversation_id", "user_id", "summary_version", "should_inject_next_turn", "updated_at"):
        payload.pop(key, None)
    return payload


def _summary_from_row(row: dict[str, Any]) -> ConversationStateSummary:
    return ConversationStateSummary(
        conversation_id=row["conversation_id"],
        user_id=row["user_id"],
        summary_version=row["summary_version"],
        should_inject_next_turn=row["should_inject_next_turn"],
        updated_at=_to_iso(row["updated_at"]),
        **row["summary"],
    )


def _pending_from_row(row: dict[str, Any]) -> PendingInteractionState:
    return PendingInteractionState(
        conversation_id=row["conversation_id"],
        user_id=row["user_id"],
        pending_kind=row["pending_kind"],
        assistant_prompt=row["assistant_prompt"],
        expected_user_response=row["expected_user_response"],
        resume_graph=row["resume_graph"],
        resume_node=row["resume_node"],
        created_at=_to_iso(row["created_at"]),
        updated_at=_to_iso(row["updated_at"]),
    )


def _to_iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _from_iso(value: str) -> datetime | str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
