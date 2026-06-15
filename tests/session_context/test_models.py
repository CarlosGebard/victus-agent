from pydantic import ValidationError

from domain.session_context.models import ConversationStateSummary, PendingInteractionState


def test_conversation_summary_is_strict_compact_contract() -> None:
    summary = ConversationStateSummary(
        conversation_id="conversation-1",
        user_id="user-1",
        user_current_goal="adjust plan",
        current_topic="PlanRevisionGraph",
        updated_at="2026-06-14T00:00:00+00:00",
    )

    assert summary.summary_version == "session-context-v1"
    assert summary.should_inject_next_turn is True


def test_pending_interaction_rejects_unknown_fields() -> None:
    try:
        PendingInteractionState(
            conversation_id="conversation-1",
            user_id="user-1",
            pending_kind="confirmation",
            assistant_prompt="Do it?",
            expected_user_response="yes_no",
            created_at="2026-06-14T00:00:00+00:00",
            updated_at="2026-06-14T00:00:00+00:00",
            full_chat_history=[],
        )
    except ValidationError as error:
        assert "full_chat_history" in str(error)
    else:
        raise AssertionError("extra fields must be rejected")
