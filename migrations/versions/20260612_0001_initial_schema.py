"""initial schema

Revision ID: 20260612_0001
Revises:
Create Date: 2026-06-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260612_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    _create_agent_user_identities()
    _create_agent_turns()
    _create_node_runs()
    _create_user_events()
    _create_projector_offsets()
    _create_projection_tables()
    _create_session_context_tables()


def downgrade() -> None:
    op.drop_index("ix_pending_interaction_state_user_updated", table_name="pending_interaction_state")
    op.drop_table("pending_interaction_state")
    op.drop_index(
        "ix_conversation_state_summaries_user_updated",
        table_name="conversation_state_summaries",
    )
    op.drop_table("conversation_state_summaries")
    op.drop_table("planning_history_projection")
    op.drop_table("nutrition_status_projection")
    op.drop_table("constraint_projection")
    op.drop_table("user_profile_projection")
    op.drop_table("projector_offsets")
    op.drop_index("ux_user_events_idempotency", table_name="user_events")
    op.drop_index("ix_user_events_payload_gin", table_name="user_events")
    op.drop_index("ix_user_events_turn", table_name="user_events")
    op.drop_index("ix_user_events_aggregate", table_name="user_events")
    op.drop_index("ix_user_events_type", table_name="user_events")
    op.drop_index("ix_user_events_user_recorded_at", table_name="user_events")
    op.drop_index("ix_user_events_user_occurred_at", table_name="user_events")
    op.drop_index("ix_user_events_user_seq", table_name="user_events")
    op.drop_table("user_events")
    op.drop_index("ix_node_runs_node_name", table_name="node_runs")
    op.drop_index("ix_node_runs_user_created", table_name="node_runs")
    op.drop_index("ix_node_runs_turn", table_name="node_runs")
    op.drop_table("node_runs")
    op.drop_index("ix_agent_turns_selected_node", table_name="agent_turns")
    op.drop_index("ix_agent_turns_conversation_created", table_name="agent_turns")
    op.drop_index("ix_agent_turns_user_created", table_name="agent_turns")
    op.drop_table("agent_turns")
    op.drop_index("ix_agent_user_identities_email", table_name="agent_user_identities")
    op.drop_table("agent_user_identities")


def _create_agent_user_identities() -> None:
    op.create_table(
        "agent_user_identities",
        sa.Column("agent_user_id", sa.Text(), primary_key=True),
        sa.Column("external_system", sa.Text(), nullable=False),
        sa.Column("external_subject", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('active', 'disabled', 'deleted')",
            name="ck_agent_user_identities_status",
        ),
        sa.UniqueConstraint(
            "external_system",
            "external_subject",
            name="ux_agent_user_identities_external_identity",
        ),
    )
    op.create_index("ix_agent_user_identities_email", "agent_user_identities", ["email"])


def _create_agent_turns() -> None:
    op.create_table(
        "agent_turns",
        sa.Column("turn_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("selected_node", sa.Text(), nullable=True),
        sa.Column("final_status", sa.Text(), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint(
            "final_status IN ('completed', 'failed', 'blocked', 'needs_user_response')",
            name="ck_agent_turns_final_status",
        ),
    )
    op.execute("ALTER TABLE agent_turns ALTER COLUMN turn_id SET DEFAULT gen_random_uuid()")
    op.create_index("ix_agent_turns_user_created", "agent_turns", ["user_id", "created_at"])
    op.create_index(
        "ix_agent_turns_conversation_created",
        "agent_turns",
        ["conversation_id", "created_at"],
    )
    op.create_index("ix_agent_turns_selected_node", "agent_turns", ["selected_node"])


def _create_node_runs() -> None:
    op.create_table(
        "node_runs",
        sa.Column("node_run_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("turn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("node_name", sa.Text(), nullable=False),
        sa.Column("input", postgresql.JSONB(), nullable=False),
        sa.Column("output", postgresql.JSONB(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint(
            "status IN ('completed', 'failed', 'skipped', 'rerouted', 'needs_clarification', "
            "'needs_confirmation', 'safety_blocked')",
            name="ck_node_runs_status",
        ),
    )
    op.execute("ALTER TABLE node_runs ALTER COLUMN node_run_id SET DEFAULT gen_random_uuid()")
    op.create_index("ix_node_runs_turn", "node_runs", ["turn_id"])
    op.create_index("ix_node_runs_user_created", "node_runs", ["user_id", "created_at"])
    op.create_index("ix_node_runs_node_name", "node_runs", ["node_name"])


def _create_user_events() -> None:
    op.create_table(
        "user_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_seq", sa.BigInteger(), sa.Identity(), unique=True, nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("turn_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("aggregate_type", sa.Text(), nullable=False),
        sa.Column("aggregate_id", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("actor", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("correlation_id", sa.Text(), nullable=True),
        sa.Column("causation_id", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint(
            "source IN ('user', 'system', 'import', 'migration', 'test')",
            name="ck_user_events_source",
        ),
    )
    op.execute("ALTER TABLE user_events ALTER COLUMN event_id SET DEFAULT gen_random_uuid()")
    op.create_index("ix_user_events_user_seq", "user_events", ["user_id", "event_seq"])
    op.create_index("ix_user_events_user_occurred_at", "user_events", ["user_id", "occurred_at"])
    op.create_index("ix_user_events_user_recorded_at", "user_events", ["user_id", "recorded_at"])
    op.create_index("ix_user_events_type", "user_events", ["event_type"])
    op.create_index("ix_user_events_aggregate", "user_events", ["aggregate_type", "aggregate_id"])
    op.create_index("ix_user_events_turn", "user_events", ["turn_id"])
    op.create_index("ix_user_events_payload_gin", "user_events", ["payload"], postgresql_using="gin")
    op.create_index(
        "ux_user_events_idempotency",
        "user_events",
        ["user_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def _create_projector_offsets() -> None:
    op.create_table(
        "projector_offsets",
        sa.Column("projector_name", sa.Text(), primary_key=True),
        sa.Column("last_event_seq", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def _create_projection_tables() -> None:
    op.create_table(
        "user_profile_projection",
        sa.Column("user_id", sa.Text(), primary_key=True),
        sa.Column("profile", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("restrictions", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("preferences", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("active_goal_id", sa.Text(), nullable=True),
        sa.Column("last_event_seq", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "constraint_projection",
        sa.Column("user_id", sa.Text(), primary_key=True),
        sa.Column("hard_constraints", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("soft_constraints", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("safety_flags", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("derived_from_event_seq", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "nutrition_status_projection",
        sa.Column("user_id", sa.Text(), primary_key=True),
        sa.Column("recent_meals", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("biometrics", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("symptoms", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("computed_metrics", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("last_event_seq", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_table(
        "planning_history_projection",
        sa.Column("user_id", sa.Text(), primary_key=True),
        sa.Column("active_session_id", sa.Text(), nullable=True),
        sa.Column("active_plan_artifact_id", sa.Text(), nullable=True),
        sa.Column("active_goal_id", sa.Text(), nullable=True),
        sa.Column("revision_summary", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("feedback_summary", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("last_event_seq", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def _create_session_context_tables() -> None:
    op.create_table(
        "conversation_state_summaries",
        sa.Column("conversation_id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("summary_version", sa.Text(), nullable=False),
        sa.Column("summary", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("should_inject_next_turn", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_conversation_state_summaries_user_updated",
        "conversation_state_summaries",
        ["user_id", "updated_at"],
    )

    op.create_table(
        "pending_interaction_state",
        sa.Column("conversation_id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("pending_kind", sa.Text(), nullable=False),
        sa.Column("assistant_prompt", sa.Text(), nullable=False),
        sa.Column("expected_user_response", sa.Text(), nullable=False),
        sa.Column("resume_graph", sa.Text(), nullable=True),
        sa.Column("resume_node", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "pending_kind IN ('question', 'confirmation', 'choice', 'proposal')",
            name="ck_pending_interaction_state_kind",
        ),
    )
    op.create_index(
        "ix_pending_interaction_state_user_updated",
        "pending_interaction_state",
        ["user_id", "updated_at"],
    )
