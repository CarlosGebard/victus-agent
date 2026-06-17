from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
import yaml

from infrastructure.db.schema import (
    agent_turns,
    agent_user_identities,
    conversation_state_summaries,
    metadata,
    node_runs,
    pending_interaction_state,
    user_profile_projection,
    user_events,
)


def test_metadata_contains_phase_2_core_tables() -> None:
    assert "agent_user_identities" in metadata.tables
    assert "agent_turns" in metadata.tables
    assert "node_runs" in metadata.tables
    assert "user_events" in metadata.tables
    assert "conversation_state_summaries" in metadata.tables
    assert "pending_interaction_state" in metadata.tables
    assert "accounts" not in metadata.tables


def test_user_events_compiles_for_postgres() -> None:
    ddl = str(CreateTable(user_events).compile(dialect=postgresql.dialect()))

    assert "CREATE TABLE user_events" in ddl
    assert "JSONB" in ddl
    assert "event_seq BIGINT" in ddl
    assert "turn_id UUID" in ddl
    assert "event_type TEXT NOT NULL" in ddl
    assert "event_type" not in str(user_events.c.event_type.type).lower().replace("text", "")


def test_operational_trace_tables_compile_for_postgres() -> None:
    turn_ddl = str(CreateTable(agent_turns).compile(dialect=postgresql.dialect()))
    node_run_ddl = str(CreateTable(node_runs).compile(dialect=postgresql.dialect()))

    assert "CREATE TABLE agent_turns" in turn_ddl
    assert "ck_agent_turns_final_status" in turn_ddl
    assert "CREATE TABLE node_runs" in node_run_ddl
    assert "ck_node_runs_status" in node_run_ddl


def test_agent_user_identities_compile_for_postgres() -> None:
    ddl = str(CreateTable(agent_user_identities).compile(dialect=postgresql.dialect()))

    assert "CREATE TABLE agent_user_identities" in ddl
    assert "agent_user_id TEXT NOT NULL" in ddl
    assert "external_system TEXT NOT NULL" in ddl
    assert "ux_agent_user_identities_external_identity" in ddl
    assert "preferred_name" not in ddl


def test_profile_projection_keeps_profile_data_in_jsonb() -> None:
    ddl = str(CreateTable(user_profile_projection).compile(dialect=postgresql.dialect()))

    assert "profile JSONB" in ddl
    assert "preferred_name" not in ddl


def test_session_context_tables_compile_for_postgres() -> None:
    summary_ddl = str(CreateTable(conversation_state_summaries).compile(dialect=postgresql.dialect()))
    pending_ddl = str(CreateTable(pending_interaction_state).compile(dialect=postgresql.dialect()))

    assert "CREATE TABLE conversation_state_summaries" in summary_ddl
    assert "should_inject_next_turn BOOLEAN" in summary_ddl
    assert "CREATE TABLE pending_interaction_state" in pending_ddl
    assert "ck_pending_interaction_state_kind" in pending_ddl


def test_event_registry_defines_unique_text_event_types() -> None:
    with open("docs/contracts/events/event-registry.yml", encoding="utf-8") as file:
        registry = yaml.safe_load(file)

    events = registry["events"]
    event_types = [event["event_type"] for event in events]

    assert "meal.logged" in event_types
    assert "restriction.added" in event_types
    assert len(event_types) == len(set(event_types))
    assert all(isinstance(event_type, str) for event_type in event_types)
