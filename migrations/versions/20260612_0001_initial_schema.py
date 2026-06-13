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

    op.create_table(
        "accounts",
        sa.Column("account_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("auth_provider", sa.Text(), nullable=False),
        sa.Column("auth_subject", sa.Text(), nullable=False),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_accounts_status"),
        sa.UniqueConstraint("auth_provider", "auth_subject", name="ux_accounts_auth_identity"),
    )
    op.execute("ALTER TABLE accounts ALTER COLUMN account_id SET DEFAULT gen_random_uuid()")

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("primary_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("locale", sa.Text(), nullable=True),
        sa.Column("timezone", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('active', 'disabled', 'deleted')", name="ck_users_status"),
        sa.ForeignKeyConstraint(["primary_account_id"], ["accounts.account_id"]),
    )
    op.execute("ALTER TABLE users ALTER COLUMN user_id SET DEFAULT gen_random_uuid()")

    op.create_table(
        "account_user_memberships",
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("role IN ('owner', 'coach', 'viewer')", name="ck_account_user_memberships_role"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.account_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("account_id", "user_id"),
    )

    op.create_table(
        "connected_accounts",
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("external_subject", sa.Text(), nullable=False),
        sa.Column("scopes", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("token_ref", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("status IN ('active', 'revoked', 'expired', 'error')", name="ck_connected_accounts_status"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.account_id"]),
        sa.UniqueConstraint("provider", "external_subject", name="ux_connected_accounts_provider_subject"),
    )
    op.execute("ALTER TABLE connected_accounts ALTER COLUMN connection_id SET DEFAULT gen_random_uuid()")

    op.create_table(
        "user_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("event_seq", sa.BigInteger(), sa.Identity(), unique=True, nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
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
        sa.CheckConstraint("source IN ('user', 'system', 'import', 'migration', 'test')", name="ck_user_events_source"),
    )
    op.execute("ALTER TABLE user_events ALTER COLUMN event_id SET DEFAULT gen_random_uuid()")
    op.create_index("ix_user_events_user_seq", "user_events", ["user_id", "event_seq"])
    op.create_index("ix_user_events_type", "user_events", ["event_type"])
    op.create_index("ix_user_events_aggregate", "user_events", ["aggregate_type", "aggregate_id"])
    op.create_index("ix_user_events_payload_gin", "user_events", ["payload"], postgresql_using="gin")
    op.create_index(
        "ux_user_events_idempotency",
        "user_events",
        ["user_id", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    op.create_table(
        "projector_offsets",
        sa.Column("projector_name", sa.Text(), primary_key=True),
        sa.Column("last_event_seq", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    _create_projection_tables()
    _create_planning_tables()
    _create_clarification_and_evidence_tables()


def downgrade() -> None:
    op.drop_table("evidence_citations")
    op.drop_index("ix_clarification_state_user_status", table_name="clarification_state")
    op.drop_table("clarification_state")
    op.drop_index("ix_plan_artifacts_user_created", table_name="plan_artifacts")
    op.drop_table("plan_artifacts")
    op.drop_table("plan_revisions")
    op.drop_table("planning_sessions")
    op.drop_table("planning_history_projection")
    op.drop_table("nutrition_status_projection")
    op.drop_table("constraint_projection")
    op.drop_table("user_profile_projection")
    op.drop_table("projector_offsets")
    op.drop_index("ux_user_events_idempotency", table_name="user_events")
    op.drop_index("ix_user_events_payload_gin", table_name="user_events")
    op.drop_index("ix_user_events_aggregate", table_name="user_events")
    op.drop_index("ix_user_events_type", table_name="user_events")
    op.drop_index("ix_user_events_user_seq", table_name="user_events")
    op.drop_table("user_events")
    op.drop_table("connected_accounts")
    op.drop_table("account_user_memberships")
    op.drop_table("users")
    op.drop_table("accounts")


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


def _create_planning_tables() -> None:
    op.create_table(
        "planning_sessions",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("status IN ('active', 'completed', 'abandoned', 'canceled', 'error')", name="ck_planning_sessions_status"),
    )
    op.execute("ALTER TABLE planning_sessions ALTER COLUMN session_id SET DEFAULT gen_random_uuid()")
    op.create_table(
        "plan_revisions",
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("parent_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("objectives", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.ForeignKeyConstraint(["session_id"], ["planning_sessions.session_id"]),
    )
    op.execute("ALTER TABLE plan_revisions ALTER COLUMN revision_id SET DEFAULT gen_random_uuid()")
    op.create_table(
        "plan_artifacts",
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("revision_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("artifact_type", sa.Text(), nullable=False),
        sa.Column("artifact", postgresql.JSONB(), nullable=False),
        sa.Column("validation", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.Text(), nullable=False, server_default="draft"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("status IN ('draft', 'accepted', 'rejected', 'superseded')", name="ck_plan_artifacts_status"),
        sa.ForeignKeyConstraint(["session_id"], ["planning_sessions.session_id"]),
        sa.ForeignKeyConstraint(["revision_id"], ["plan_revisions.revision_id"]),
    )
    op.execute("ALTER TABLE plan_artifacts ALTER COLUMN artifact_id SET DEFAULT gen_random_uuid()")
    op.create_index("ix_plan_artifacts_user_created", "plan_artifacts", ["user_id", sa.text("created_at DESC")])


def _create_clarification_and_evidence_tables() -> None:
    op.create_table(
        "clarification_state",
        sa.Column("clarification_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("blocked_node", sa.Text(), nullable=True),
        sa.Column("blocked_action", sa.Text(), nullable=True),
        sa.Column("missing_fields", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("expected_answer_type", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("resume_node", sa.Text(), nullable=True),
        sa.Column("resume_action", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.CheckConstraint("status IN ('open', 'resolved', 'canceled', 'superseded')", name="ck_clarification_state_status"),
    )
    op.execute("ALTER TABLE clarification_state ALTER COLUMN clarification_id SET DEFAULT gen_random_uuid()")
    op.create_index("ix_clarification_state_user_status", "clarification_state", ["user_id", "status"])
    op.create_table(
        "evidence_citations",
        sa.Column("citation_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("evidence_id", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("citation_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.execute("ALTER TABLE evidence_citations ALTER COLUMN citation_id SET DEFAULT gen_random_uuid()")
