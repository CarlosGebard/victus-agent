---
id: VICTUS-AGENT-CONTRACTS
title: Victus Agent Contracts
status: draft
version: v1
updated_at: 2026-06-12
owners:
  - victus-agent-runtime
---

# Victus Agent Contracts

## 1. Purpose

This document defines the stable contracts required to implement Victus Agent V1.

It is the implementation authority for schemas, event semantics, route labels, tool envelopes, agent identity, PostgreSQL tables, projection behavior, and runtime state.

## 2. Contract Principles

- The event store is the canonical user history.
- Projections are derived read models.
- Session context is compact conversational memory, not domain truth.
- LangGraph state is orchestration state only.
- The webapp owns platform users; this database stores only the agent's identity reference.
- Tool handlers validate and execute; the LLM proposes but does not persist directly.
- Router embeddings assist classification but do not bypass safety or ambiguity rules.
- All write operations require idempotency keys.
- Corrections are represented by new events, not mutation of old events.

Fundamental shared contracts imported from `CarlosGebard/victus-docs` live under `docs/contracts/fundamental/` and must be synchronized with `uv run contracts sync`; do not edit those imported files manually.

## 3. Identity Contracts

### 3.1 Agent User Identity

Represents the user as seen by the agent and the external subject it came from.

Canonical identifier: `agent_user_id`.

This table is not the platform user table. It is a minimal bridge from an external system such as
`webapp`, `cli`, `test`, or `import` into the agent runtime.

```sql
CREATE TABLE agent_user_identities (
    agent_user_id TEXT PRIMARY KEY,
    external_system TEXT NOT NULL,
    external_subject TEXT NOT NULL,
    email TEXT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled', 'deleted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ux_agent_identity_external_subject UNIQUE (external_system, external_subject)
);
```

## 4. Auth Context Contract

`AuthContext` is created once per authenticated request.

```ts
type AuthContext = {
  agent_user_id: string
  external_system: string
  external_subject: string
  locale?: string
  timezone?: string
}
```

Validation rules:

- `agent_user_id` must reference an active `agent_user_identities` row.
- `external_system` and `external_subject` must come from trusted caller context.
- write authorization is delegated to the external system until the agent owns permissions.
- local development may use a fixed test identity only when `APP_ENV=local`.

## 5. Request Context Contract

```ts
type RequestContext = {
  request_id: string
  trace_id: string
  agent_user_id: string
  raw_text: string
  normalized_text?: string
  received_at: string
  locale?: string
  timezone?: string
  conversation_id?: string
}
```

Rules:

- `request_id` must be unique per incoming user message.
- `trace_id` must connect route decisions, tool executions, events, and response composition.
- `agent_user_id` must come from `AuthContext`.

## 6. PostgreSQL Required Extensions

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
```

`pgcrypto` is required for `gen_random_uuid()`.

`vector` is required for embedding-assisted routing.

## 7. Database Schema Contract

The authoritative V1 PostgreSQL schema is `docs/contracts/postgres-schema-v1.md`.

Key guarantees:

- `user_events` is the source of truth.
- `event_type` remains `TEXT`; allowed events are validated through `docs/contracts/events/event-registry.yml` and code registries.
- projections remain JSONB-derived state.
- `agent_turns` and `node_runs` own operational traceability.
- `conversation_state_summaries` is compact memory, not user truth.
- `pending_interaction_state` stores pending clarification/confirmation state.
- no hard foreign keys point to the webapp database.

## 8. Domain Event Types V1

Allowed event types are registered in `docs/contracts/events/event-registry.yml`.

Payloads may evolve, but new required fields require a major contract change.

## 14. Intent Router Contracts

### 14.1 Route Definition

```sql
CREATE TABLE intent_route_definitions (
    route_id TEXT PRIMARY KEY,
    route_label TEXT NOT NULL,
    target_graph TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive', 'deprecated')),
    priority INTEGER NOT NULL DEFAULT 100,
    requires_safety_ok BOOLEAN NOT NULL DEFAULT true,
    description TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v1',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Allowed route labels:

```text
log_update_data
new_plan
revise_plan
weekly_review
evidence_question
profile_update
risk_medical_unsafe
mixed_ambiguous
needs_clarification
```

### 14.2 Route Example Embedding

Default V1 embedding dimension is `1024`, suitable for a multilingual BGE-M3-style local model. If a different embedding model is selected, this contract must be migrated with the new dimension.

```sql
CREATE TABLE intent_route_examples (
    example_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    route_id TEXT NOT NULL REFERENCES intent_route_definitions(route_id),
    language TEXT NULL,
    example_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    embedding vector(1024) NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding_version TEXT NOT NULL DEFAULT 'v1',
    status TEXT NOT NULL CHECK (status IN ('active', 'inactive', 'deprecated')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_intent_route_examples_route ON intent_route_examples(route_id);
CREATE INDEX idx_intent_route_examples_embedding
ON intent_route_examples USING hnsw (embedding vector_cosine_ops);
```

### 14.3 Route Decision Log

Route decisions are captured in `agent_turns.selected_node`, `node_runs`, and metadata fields.
V1 does not create a separate `route_decisions` table.

### 14.4 Router Decision Type

```ts
type RouterDecision = {
  selected_route_label:
    | 'log_update_data'
    | 'new_plan'
    | 'revise_plan'
    | 'weekly_review'
    | 'evidence_question'
    | 'profile_update'
    | 'risk_medical_unsafe'
    | 'mixed_ambiguous'
    | 'needs_clarification'
  target_graph: string
  confidence: number
  routing_method: 'rule' | 'embedding' | 'hybrid' | 'llm_fallback' | 'clarification' | 'safety_override'
  top_candidates: Array<{ route_label: string; score: number; example_id?: string }>
  ambiguity_reasons: string[]
}
```

### 14.5 Router Validation Rules

- Safety override wins over embedding score.
- If confidence is below `ROUTER_CONFIDENCE_THRESHOLD`, do not execute write tools.
- If the margin between top two candidates is below `ROUTER_MARGIN_THRESHOLD`, route to `mixed_ambiguous` or `needs_clarification`.
- Router examples must be versioned by embedding model.
- Multilingual examples must include at least Spanish and English in V1.
- The router must log every decision.

## 15. LangGraph State Contract

```ts
type VictusGraphStateV1 = {
  request: RequestContext
  auth: AuthContext
  safety: {
    status: 'unknown' | 'ok' | 'warning' | 'blocked' | 'needs_clarification'
    risk_category?: string
    reasons: string[]
  }
  router?: RouterDecision
  projections: {
    user_profile?: Record<string, unknown>
    constraints?: Record<string, unknown>
    nutrition_status?: Record<string, unknown>
    planning_history?: Record<string, unknown>
  }
  tool_context: {
    allowed_tools: string[]
    tool_results: Array<ToolResult>
  }
  planning?: {
    session_id?: string
    revision_id?: string
    artifact_id?: string
    candidate_artifact?: Record<string, unknown>
  }
  clarification?: {
    clarification_id?: string
    missing_fields?: string[]
    question?: string
    resume_route?: string
    resume_node?: string
  }
  response?: {
    status: 'success' | 'needs_clarification' | 'blocked' | 'error'
    message: string
    warnings: string[]
    event_refs: Array<{ event_id: string; event_type: string; seq: number }>
  }
  audit: {
    trace_id: string
    route_decision_id?: string
    tool_execution_ids: string[]
  }
}
```

Rules:

- graph state may be checkpointed
- graph state is not the source of truth
- projections inside state are snapshots and may be stale after writes until refreshed

## 16. Tool Result Envelope Contract

```ts
type ToolStatus = 'success' | 'needs_clarification' | 'blocked' | 'rejected' | 'error'

type ToolResult<TData = unknown> = {
  status: ToolStatus
  tool_name: string
  request_id: string
  trace_id: string
  agent_user_id: string
  data?: TData
  events?: Array<{ event_id: string; event_type: string; seq: number }>
  warnings: string[]
  errors: Array<{ code: string; message: string; field?: string }>
  safety_status: 'ok' | 'warning' | 'blocked' | 'needs_clarification'
  idempotency_key?: string
}
```

Rules:

- every tool returns the envelope
- write tools include event references when successful
- tools must not return raw secrets
- `status=success` must not be returned if required event append failed

## 17. Tool Execution Log Contract

Tool execution traceability is captured in `node_runs` and event references in `user_events`.
V1 does not create a separate `tool_executions` table.

## 18. Agent Run Contract

`agent_turns` is the V1 agent run table.

Forbidden responsibility: replacing event history or projection state.

## 19. Tool Registry V1

| Tool | Type | Visible To Model | Writes Events | Primary Route |
|---|---:|---:|---:|---|
| `safety.triage` | safety | false | possible safety events | `risk_medical_unsafe` |
| `clarification.manage` | clarification | false | yes | `needs_clarification` |
| `nutrition.manage_meal` | command | true | yes | `log_update_data` |
| `biometrics.log` | command | true | yes | `log_update_data` |
| `symptom.log` | command | true | yes | `log_update_data` |
| `profile.manage_context` | command | true | yes | `profile_update` |
| `goal.manage` | command | true | yes | `new_plan`, `revise_plan` |
| `planning.manage_session` | command | partially | yes | `new_plan`, `revise_plan` |
| `diet.generate_recommendation` | compute | true | no by default | `new_plan`, `revise_plan` |
| `feedback.record` | command | true | yes | `revise_plan`, `weekly_review` |
| `evidence.search` | retrieval | true | no | `evidence_question`, `new_plan` |
| `evidence.manage_support` | command | partially | yes | `evidence_question`, `new_plan` |

## 20. Tool Execution Policy

Write tools must receive:

```ts
type ToolExecutionContext = {
  request_id: string
  trace_id: string
  agent_user_id: string
  actor_type: 'user' | 'agent' | 'tool' | 'system'
  idempotency_key: string
  safety_status: 'ok' | 'warning' | 'blocked' | 'needs_clarification'
  locale?: string
  timezone?: string
}
```

Rules:

- write tools must reject missing `idempotency_key`
- write tools must reject `safety_status=blocked`
- read tools may run without idempotency key
- compute tools must not persist unless paired with an explicit save command
- node-specific tool exposure must be enforced server-side

## 21. Safety Contract

Safety status values:

```text
unknown
ok
warning
blocked
needs_clarification
```

Rules:

- default status before safety evaluation is `unknown`
- `blocked` prevents planning and write tool execution
- `warning` may allow execution but must be included in the final response
- high-risk symptoms, medical danger, extreme diet requests, and unsafe self-treatment must route to safety
- safety decisions must be logged in route/tool/run records

## 22. Versioning

Patch changes:

- wording clarifications
- added non-required documentation
- typo fixes

Minor changes:

- backward-compatible optional fields
- new event types that do not change existing semantics
- new tools or routes that do not break V1 contracts

Major changes:

- changing identity semantics
- changing required fields
- changing event immutability rules
- changing route labels
- changing vector dimension without migration
- removing fields or status values
- allowing direct projection mutation from tools or graph nodes
