from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

from infrastructure.db.schema import conversation_state_summaries, metadata, pending_interaction_state, user_events


def test_metadata_contains_phase_2_core_tables() -> None:
    assert "accounts" in metadata.tables
    assert "user_events" in metadata.tables
    assert "conversation_state_summaries" in metadata.tables
    assert "pending_interaction_state" in metadata.tables


def test_user_events_compiles_for_postgres() -> None:
    ddl = str(CreateTable(user_events).compile(dialect=postgresql.dialect()))

    assert "CREATE TABLE user_events" in ddl
    assert "JSONB" in ddl
    assert "event_seq BIGINT" in ddl


def test_session_context_tables_compile_for_postgres() -> None:
    summary_ddl = str(CreateTable(conversation_state_summaries).compile(dialect=postgresql.dialect()))
    pending_ddl = str(CreateTable(pending_interaction_state).compile(dialect=postgresql.dialect()))

    assert "CREATE TABLE conversation_state_summaries" in summary_ddl
    assert "should_inject_next_turn BOOLEAN" in summary_ddl
    assert "CREATE TABLE pending_interaction_state" in pending_ddl
    assert "ck_pending_interaction_state_kind" in pending_ddl
