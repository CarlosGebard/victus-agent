from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql

from db.schema import metadata, user_events


def test_metadata_contains_phase_2_core_tables() -> None:
    assert "accounts" in metadata.tables
    assert "user_events" in metadata.tables


def test_user_events_compiles_for_postgres() -> None:
    ddl = str(CreateTable(user_events).compile(dialect=postgresql.dialect()))

    assert "CREATE TABLE user_events" in ddl
    assert "JSONB" in ddl
    assert "event_seq BIGINT" in ddl
