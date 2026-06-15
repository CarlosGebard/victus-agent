"""add session context state

Revision ID: 20260614_0002
Revises: 20260612_0001
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260614_0002"
down_revision = "20260612_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index("ix_pending_interaction_state_user_updated", table_name="pending_interaction_state")
    op.drop_table("pending_interaction_state")
    op.drop_index(
        "ix_conversation_state_summaries_user_updated",
        table_name="conversation_state_summaries",
    )
    op.drop_table("conversation_state_summaries")
