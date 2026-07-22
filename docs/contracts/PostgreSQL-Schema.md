---
id: VICTUS-POSTGRESQL-SCHEMA
contract_id: victus.database.postgresql_schema
title: PostgreSQL Schema
status: current
version: v1
owner: victus-agent-runtime
domain: database
contract_type: database_diagram
stability: experimental
updated_at: 2026-07-21
---

# PostgreSQL Schema

Agent-local PostgreSQL database for identity references, runtime traceability, immutable user
events, rebuildable projections, and compact conversation continuity.

This database is separate from the webapp database. It does not own platform auth or webapp user
records.

Required extension:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

## Mermaid ERD

```mermaid
erDiagram
    agent_user_identities {
        text agent_user_id PK
        text external_system
        text external_subject
        text email
        text status
        timestamptz created_at
        timestamptz updated_at
    }

    agent_turns {
        uuid turn_id PK
        text conversation_id
        text user_id
        text input_text
        text normalized_text
        text selected_node
        text final_status
        timestamptz created_at
        jsonb metadata
    }

    node_runs {
        uuid node_run_id PK
        uuid turn_id
        text user_id
        text node_name
        jsonb input
        jsonb output
        text status
        timestamptz created_at
        jsonb metadata
    }

    user_events {
        uuid event_id PK
        bigint event_seq UK
        text user_id
        uuid turn_id
        text event_type
        text aggregate_type
        text aggregate_id
        timestamptz occurred_at
        timestamptz recorded_at
        text source
        jsonb actor
        text correlation_id
        text causation_id
        text idempotency_key
        integer schema_version
        jsonb payload
        jsonb metadata
    }

    projector_offsets {
        text projector_name PK
        bigint last_event_seq
        timestamptz updated_at
    }

    user_profile_projection {
        text user_id PK
        jsonb profile
        jsonb restrictions
        jsonb preferences
        text active_goal_id
        bigint last_event_seq
        timestamptz updated_at
    }

    constraint_projection {
        text user_id PK
        jsonb hard_constraints
        jsonb soft_constraints
        jsonb safety_flags
        bigint derived_from_event_seq
        timestamptz updated_at
    }

    nutrition_status_projection {
        text user_id PK
        jsonb recent_meals
        jsonb biometrics
        jsonb symptoms
        jsonb computed_metrics
        bigint last_event_seq
        timestamptz updated_at
    }

    planning_history_projection {
        text user_id PK
        text active_session_id
        text active_plan_artifact_id
        text active_goal_id
        jsonb revision_summary
        jsonb feedback_summary
        bigint last_event_seq
        timestamptz updated_at
    }

    conversation_state_summaries {
        text conversation_id PK
        text user_id
        text summary_version
        jsonb summary
        boolean should_inject_next_turn
        timestamptz updated_at
    }

    pending_interaction_state {
        text conversation_id PK
        text user_id
        text pending_kind
        text assistant_prompt
        text expected_user_response
        text resume_graph
        text resume_node
        timestamptz created_at
        timestamptz updated_at
    }

    agent_user_identities ||--o{ agent_turns : "agent_user_id -> user_id"
    agent_user_identities ||--o{ user_events : "agent_user_id -> user_id"
    agent_turns ||--o{ node_runs : "turn_id"
    agent_turns ||--o{ user_events : "turn_id"
    user_events ||--o{ user_profile_projection : "rebuilds"
    user_events ||--o{ constraint_projection : "rebuilds"
    user_events ||--o{ nutrition_status_projection : "rebuilds"
    user_events ||--o{ planning_history_projection : "rebuilds"
    agent_user_identities ||--o{ conversation_state_summaries : "agent_user_id -> user_id"
    agent_user_identities ||--o{ pending_interaction_state : "agent_user_id -> user_id"
    conversation_state_summaries ||--o| pending_interaction_state : "conversation_id"
```

## Notes

- `user_events` is the source of truth.
- Projection tables are derived state and can be rebuilt.
- `node_runs.turn_id` and `user_events.turn_id` are logical links to `agent_turns.turn_id`; V1
  does not require hard foreign keys.
- `conversation_state_summaries` and `pending_interaction_state` store compact conversation
  continuity only.
- `event_type` remains `TEXT`; validation belongs in `docs/contracts/event-registry.yml`
  and code registries.
- Idempotent event writes are enforced by a unique index on `(user_id, idempotency_key)` when
  `idempotency_key` is not null.
- LangGraph checkpoint and Store tables are created by the LangGraph PostgreSQL setup and remain
  library-owned; this schema documents only repository-owned tables.

## Indexes

```text
agent_user_identities(email)
agent_user_identities(external_system, external_subject) unique

agent_turns(user_id, created_at)
agent_turns(conversation_id, created_at)
agent_turns(selected_node)

node_runs(turn_id)
node_runs(user_id, created_at)
node_runs(node_name)

user_events(user_id, event_seq)
user_events(user_id, occurred_at)
user_events(user_id, recorded_at)
user_events(event_type)
user_events(aggregate_type, aggregate_id)
user_events(turn_id)
user_events(payload) gin
user_events(user_id, idempotency_key) unique where idempotency_key is not null

conversation_state_summaries(user_id, updated_at)
pending_interaction_state(user_id, updated_at)
```
