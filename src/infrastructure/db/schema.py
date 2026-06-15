from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Identity,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID

metadata = MetaData()

accounts = Table(
    "accounts",
    metadata,
    Column("account_id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    Column("auth_provider", Text, nullable=False),
    Column("auth_subject", Text, nullable=False),
    Column("email", Text),
    Column("status", Text, nullable=False, server_default="active"),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_accounts_status"),
    UniqueConstraint("auth_provider", "auth_subject", name="ux_accounts_auth_identity"),
)

user_events = Table(
    "user_events",
    metadata,
    Column("event_id", UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")),
    Column("event_seq", BigInteger, Identity(), unique=True, nullable=False),
    Column("user_id", Text, nullable=False),
    Column("event_type", Text, nullable=False),
    Column("aggregate_type", Text, nullable=False),
    Column("aggregate_id", Text, nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("recorded_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("source", Text, nullable=False),
    Column("actor", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("correlation_id", Text),
    Column("causation_id", Text),
    Column("idempotency_key", Text),
    Column("schema_version", Integer, nullable=False, server_default="1"),
    Column("payload", JSONB, nullable=False),
    Column("metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    CheckConstraint(
        "source IN ('user', 'system', 'import', 'migration', 'test')",
        name="ck_user_events_source",
    ),
)

Index("ix_user_events_user_seq", user_events.c.user_id, user_events.c.event_seq)
Index("ix_user_events_type", user_events.c.event_type)
Index("ix_user_events_aggregate", user_events.c.aggregate_type, user_events.c.aggregate_id)
Index("ix_user_events_payload_gin", user_events.c.payload, postgresql_using="gin")
Index(
    "ux_user_events_idempotency",
    user_events.c.user_id,
    user_events.c.idempotency_key,
    unique=True,
    postgresql_where=user_events.c.idempotency_key.is_not(None),
)

projector_offsets = Table(
    "projector_offsets",
    metadata,
    Column("projector_name", Text, primary_key=True),
    Column("last_event_seq", BigInteger, nullable=False, server_default="0"),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)

user_profile_projection = Table(
    "user_profile_projection",
    metadata,
    Column("user_id", Text, primary_key=True),
    Column("profile", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("restrictions", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("preferences", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("active_goal_id", Text),
    Column("last_event_seq", BigInteger, nullable=False, server_default="0"),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)

constraint_projection = Table(
    "constraint_projection",
    metadata,
    Column("user_id", Text, primary_key=True),
    Column("hard_constraints", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("soft_constraints", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("safety_flags", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("derived_from_event_seq", BigInteger, nullable=False, server_default="0"),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)

nutrition_status_projection = Table(
    "nutrition_status_projection",
    metadata,
    Column("user_id", Text, primary_key=True),
    Column("recent_meals", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("biometrics", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("symptoms", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("computed_metrics", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("last_event_seq", BigInteger, nullable=False, server_default="0"),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)

planning_history_projection = Table(
    "planning_history_projection",
    metadata,
    Column("user_id", Text, primary_key=True),
    Column("active_session_id", Text),
    Column("active_plan_artifact_id", Text),
    Column("active_goal_id", Text),
    Column("revision_summary", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("feedback_summary", JSONB, nullable=False, server_default=text("'[]'::jsonb")),
    Column("last_event_seq", BigInteger, nullable=False, server_default="0"),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)

conversation_state_summaries = Table(
    "conversation_state_summaries",
    metadata,
    Column("conversation_id", Text, primary_key=True),
    Column("user_id", Text, nullable=False),
    Column("summary_version", Text, nullable=False),
    Column("summary", JSONB, nullable=False, server_default=text("'{}'::jsonb")),
    Column("should_inject_next_turn", Boolean, nullable=False, server_default=text("true")),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
)

pending_interaction_state = Table(
    "pending_interaction_state",
    metadata,
    Column("conversation_id", Text, primary_key=True),
    Column("user_id", Text, nullable=False),
    Column("pending_kind", Text, nullable=False),
    Column("assistant_prompt", Text, nullable=False),
    Column("expected_user_response", Text, nullable=False),
    Column("resume_graph", Text),
    Column("resume_node", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    Column("updated_at", DateTime(timezone=True), nullable=False, server_default=text("now()")),
    CheckConstraint(
        "pending_kind IN ('question', 'confirmation', 'choice', 'proposal')",
        name="ck_pending_interaction_state_kind",
    ),
)

Index(
    "ix_conversation_state_summaries_user_updated",
    conversation_state_summaries.c.user_id,
    conversation_state_summaries.c.updated_at,
)
Index(
    "ix_pending_interaction_state_user_updated",
    pending_interaction_state.c.user_id,
    pending_interaction_state.c.updated_at,
)
