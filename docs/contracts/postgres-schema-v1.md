---
id: VICTUS-CONTRACT-POSTGRES-SCHEMA-V1
contract_id: victus.contract.database.postgres_schema.v1
title: PostgreSQL Schema V1
status: draft
version: v1
owner: victus-agent-runtime
domain: database
contract_type: database_schema
stability: experimental
updated_at: 2026-06-12
---
# PostgreSQL Schema V1

## 1. Purpose

Defines the initial database schema required to implement the Victus Agent V1.

PostgreSQL is the canonical store for domain events, projection tables, planning artifacts, and runtime bookkeeping.

## 2. Required Extensions

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

## 3. User Events 

```sql
CREATE TABLE IF NOT EXISTS user_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_seq BIGSERIAL UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    source TEXT NOT NULL CHECK (source IN ('user', 'system', 'import', 'migration', 'test')),
    actor JSONB NOT NULL DEFAULT '{}'::jsonb,
    correlation_id UUID NULL,
    causation_id UUID NULL,
    idempotency_key TEXT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    payload JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_user_events_idempotency
ON user_events (user_id, idempotency_key)
WHERE idempotency_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_user_events_user_seq
ON user_events (user_id, event_seq);

CREATE INDEX IF NOT EXISTS ix_user_events_type
ON user_events (event_type);

CREATE INDEX IF NOT EXISTS ix_user_events_aggregate
ON user_events (aggregate_type, aggregate_id);

CREATE INDEX IF NOT EXISTS ix_user_events_payload_gin
ON user_events USING gin (payload);
```

## 4. Projector Offsets

```sql
CREATE TABLE IF NOT EXISTS projector_offsets (
    projector_name TEXT PRIMARY KEY,
    last_event_seq BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 5. Projection Tables

```sql
CREATE TABLE IF NOT EXISTS user_profile_projection (
    user_id TEXT PRIMARY KEY,
    profile JSONB NOT NULL DEFAULT '{}'::jsonb,
    restrictions JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferences JSONB NOT NULL DEFAULT '[]'::jsonb,
    active_goal_id TEXT NULL,
    last_event_seq BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS constraint_projection (
    user_id TEXT PRIMARY KEY,
    hard_constraints JSONB NOT NULL DEFAULT '[]'::jsonb,
    soft_constraints JSONB NOT NULL DEFAULT '[]'::jsonb,
    safety_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
    derived_from_event_seq BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS nutrition_status_projection (
    user_id TEXT PRIMARY KEY,
    recent_meals JSONB NOT NULL DEFAULT '[]'::jsonb,
    biometrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    symptoms JSONB NOT NULL DEFAULT '[]'::jsonb,
    computed_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_event_seq BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS planning_history_projection (
    user_id TEXT PRIMARY KEY,
    active_session_id TEXT NULL,
    active_plan_artifact_id TEXT NULL,
    active_goal_id TEXT NULL,
    revision_summary JSONB NOT NULL DEFAULT '[]'::jsonb,
    feedback_summary JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_event_seq BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## 6. Planning Tables

Planning tables are allowed because plan artifacts are large and frequently queried. They must still be backed by events.

```sql
CREATE TABLE IF NOT EXISTS planning_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'completed', 'abandoned', 'canceled', 'error')),
    reason TEXT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS plan_revisions (
    revision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES planning_sessions(session_id),
    user_id TEXT NOT NULL,
    parent_revision_id UUID NULL,
    objectives JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS plan_artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES planning_sessions(session_id),
    revision_id UUID NOT NULL REFERENCES plan_revisions(revision_id),
    user_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    artifact JSONB NOT NULL,
    validation JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'accepted', 'rejected', 'superseded')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_plan_artifacts_user_created
ON plan_artifacts (user_id, created_at DESC);
```

## 7. Clarification State

```sql
CREATE TABLE IF NOT EXISTS clarification_state (
    clarification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('open', 'resolved', 'canceled', 'superseded')),
    blocked_node TEXT NULL,
    blocked_action TEXT NULL,
    missing_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    question TEXT NOT NULL,
    expected_answer_type TEXT NOT NULL,
    answer TEXT NULL,
    resume_node TEXT NULL,
    resume_action TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS ix_clarification_state_user_status
ON clarification_state (user_id, status);
```

## 8. Session Context Tables

```sql
CREATE TABLE IF NOT EXISTS conversation_state_summaries (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    summary_version TEXT NOT NULL,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    should_inject_next_turn BOOLEAN NOT NULL DEFAULT true,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_conversation_state_summaries_user_updated
ON conversation_state_summaries (user_id, updated_at);

CREATE TABLE IF NOT EXISTS pending_interaction_state (
    conversation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    pending_kind TEXT NOT NULL CHECK (pending_kind IN ('question', 'confirmation', 'choice', 'proposal')),
    assistant_prompt TEXT NOT NULL,
    expected_user_response TEXT NOT NULL,
    resume_graph TEXT NULL,
    resume_node TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_pending_interaction_state_user_updated
ON pending_interaction_state (user_id, updated_at);
```

These tables are runtime continuity state. They are not event history and must not replace `user_events` or projections.

## 8. Evidence References

```sql
CREATE TABLE IF NOT EXISTS evidence_citations (
    citation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    citation_text TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
```

## 9. Runtime Notes

- Use JSONB for V1 flexibility, but keep event names, identifiers, and ordering relational.
- Do not use projection tables as source of truth.
- Do not physically delete events.
- Run projectors after every successful write or through a replay worker.
- Add stricter typed tables later only after the event model stabilizes.
