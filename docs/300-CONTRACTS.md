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

It is the implementation authority for schemas, event semantics, route labels, tool envelopes, account identity, PostgreSQL tables, projection behavior, and runtime state.

## 2. Contract Principles

- The event store is the canonical user history.
- Projections are derived read models.
- LangGraph state is orchestration state only.
- Account identity and user profile identity are separate concepts.
- Tool handlers validate and execute; the LLM proposes but does not persist directly.
- Router embeddings assist classification but do not bypass safety or ambiguity rules.
- All write operations require idempotency keys.
- Corrections are represented by new events, not mutation of old events.

## 3. Identity Contracts

### 3.1 Account

Represents an authenticated application account.

Canonical identifier: `account_id`.

Identity must be resolved from trusted authentication claims, not from free-text user input.

```sql
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_provider TEXT NOT NULL,
    auth_subject TEXT NOT NULL,
    email TEXT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled', 'deleted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (auth_provider, auth_subject)
);
```

### 3.2 User

Represents the nutrition/lifestyle subject Victus reasons about.

Canonical identifier: `user_id`.

V1 may use one user per account, but the schema must not collapse `account_id` and `user_id` into one concept.

```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_account_id UUID NOT NULL REFERENCES accounts(account_id),
    display_name TEXT NULL,
    locale TEXT NULL,
    timezone TEXT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled', 'deleted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 3.3 Account User Membership

Defines which accounts can access which user profiles.

```sql
CREATE TABLE account_user_memberships (
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    role TEXT NOT NULL CHECK (role IN ('owner', 'coach', 'viewer')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (account_id, user_id)
);
```

### 3.4 Connected Account

Represents an external provider connection.

Token material must not be stored directly. Store `token_ref` only.

```sql
CREATE TABLE connected_accounts (
    connection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    provider TEXT NOT NULL,
    external_subject TEXT NOT NULL,
    scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
    token_ref TEXT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'revoked', 'expired', 'error')),
    connected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at TIMESTAMPTZ NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (provider, external_subject)
);
```

## 4. Auth Context Contract

`AuthContext` is created once per authenticated request.

```ts
type AuthContext = {
  account_id: string
  user_id: string
  auth_provider: string
  auth_subject: string
  roles: Array<'owner' | 'coach' | 'viewer'>
  locale?: string
  timezone?: string
}
```

Validation rules:

- `account_id` must reference an active account.
- `user_id` must be accessible by `account_id` through `account_user_memberships`.
- write actions require role `owner` or a future explicit write permission.
- local development may use a fixed test account only when `APP_ENV=local`.

## 5. Request Context Contract

```ts
type RequestContext = {
  request_id: string
  trace_id: string
  account_id: string
  user_id: string
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
- `account_id` and `user_id` must come from `AuthContext`.

## 6. PostgreSQL Required Extensions

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
```

`pgcrypto` is required for `gen_random_uuid()`.

`vector` is required for embedding-assisted routing.

## 7. Event Store Contract

### 7.1 Purpose

`user_events` stores immutable facts about user-affecting actions.

Events represent history, not current state.

### 7.2 Schema

```sql
CREATE TABLE user_events (
    seq BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    event_type TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    actor_type TEXT NOT NULL CHECK (actor_type IN ('user', 'system', 'agent', 'tool')),
    actor_id TEXT NULL,
    correlation_id TEXT NOT NULL,
    causation_id TEXT NULL,
    idempotency_key TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    payload JSONB NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (event_id),
    UNIQUE (user_id, idempotency_key)
);

CREATE INDEX idx_user_events_user_seq ON user_events(user_id, seq);
CREATE INDEX idx_user_events_type ON user_events(event_type);
CREATE INDEX idx_user_events_correlation ON user_events(correlation_id);
```

### 7.3 Event Envelope

```ts
type UserEventEnvelope<TPayload = unknown> = {
  event_id: string
  seq: number
  account_id: string
  user_id: string
  event_type: string
  aggregate_type: string
  aggregate_id: string
  actor_type: 'user' | 'system' | 'agent' | 'tool'
  actor_id?: string
  correlation_id: string
  causation_id?: string
  idempotency_key: string
  occurred_at: string
  recorded_at: string
  payload: TPayload
  metadata: Record<string, unknown>
}
```

### 7.4 Event Rules

- Events are append-only.
- Old events must not be updated to correct user history.
- Duplicate idempotency keys for the same user must return the original event result.
- Every write tool must emit zero or more events explicitly.
- Events must include account and user identity.
- Events must not contain raw provider tokens.

## 8. Domain Event Types V1

Allowed V1 event types:

```text
meal.logged
meal.edited
meal.deleted
biometrics.logged
symptom.logged
restriction.added
restriction.updated
preference.updated
goal.set
goal.adjusted
plan.session_started
plan.revision_created
plan.artifact_saved
plan.session_ended
feedback.recorded
feedback.resolved
clarification.requested
clarification.resolved
safety.guard_triggered
safety.action_blocked
claim.generated
evidence.cited
```

### 8.1 Example Payload Shapes

```ts
type MealLoggedPayload = {
  meal_id: string
  meal_type?: 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'unknown'
  consumed_at?: string
  description: string
  items?: Array<{ name: string; quantity?: string; notes?: string }>
  estimated_nutrition?: Record<string, number | string>
  source: 'user_text' | 'manual_form' | 'import'
}

type RestrictionAddedPayload = {
  restriction_id: string
  category: 'allergy' | 'intolerance' | 'preference' | 'medical' | 'ethical' | 'religious' | 'other'
  label: string
  severity?: 'hard' | 'soft' | 'unknown'
  notes?: string
}

type GoalSetPayload = {
  goal_id: string
  goal_type: 'fat_loss' | 'muscle_gain' | 'maintenance' | 'performance' | 'health' | 'custom'
  target?: Record<string, unknown>
  horizon?: string
  status: 'active' | 'paused' | 'completed'
}

type PlanArtifactSavedPayload = {
  session_id: string
  revision_id: string
  artifact_id: string
  artifact_type: 'diet_plan' | 'meal_plan' | 'review' | 'recommendation'
  status: 'candidate' | 'accepted' | 'superseded' | 'rejected'
}
```

Payloads may evolve, but new required fields require a major contract change.

## 9. Projector Offset Contract

```sql
CREATE TABLE projector_offsets (
    projector_name TEXT PRIMARY KEY,
    last_seq BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Rules:

- Each projector owns one offset row.
- Offsets track the highest processed `user_events.seq`.
- Projectors must be idempotent.

## 10. Projection Contracts

### 10.1 User Profile Projection

```sql
CREATE TABLE user_profile_projection (
    user_id UUID PRIMARY KEY REFERENCES users(user_id),
    display_name TEXT NULL,
    locale TEXT NULL,
    timezone TEXT NULL,
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    active_goal JSONB NULL,
    updated_from_seq BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Purpose: fast read model for stable user context.

Forbidden responsibility: storing event history.

### 10.2 Constraint Projection

```sql
CREATE TABLE constraint_projection (
    user_id UUID PRIMARY KEY REFERENCES users(user_id),
    restrictions JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferences JSONB NOT NULL DEFAULT '[]'::jsonb,
    hard_constraints JSONB NOT NULL DEFAULT '[]'::jsonb,
    soft_constraints JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_from_seq BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Purpose: fast read model for planning constraints.

### 10.3 Nutrition Status Projection

```sql
CREATE TABLE nutrition_status_projection (
    user_id UUID PRIMARY KEY REFERENCES users(user_id),
    recent_meals JSONB NOT NULL DEFAULT '[]'::jsonb,
    biometrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    symptoms JSONB NOT NULL DEFAULT '[]'::jsonb,
    adherence_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_from_seq BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Purpose: current nutrition/lifestyle status for planning, review, and safety context.

`adherence_metrics` may later include `adherence_rate_7d`, `adherence_rate_30d`, `weekend_drop_delta`, `late_meal_frequency`, `consistency_score`, and `trigger_pattern_score`.

### 10.4 Planning History Projection

```sql
CREATE TABLE planning_history_projection (
    user_id UUID PRIMARY KEY REFERENCES users(user_id),
    active_session_id UUID NULL,
    active_revision_id UUID NULL,
    active_artifact_id UUID NULL,
    recent_feedback JSONB NOT NULL DEFAULT '[]'::jsonb,
    planning_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_from_seq BIGINT NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Purpose: fast read model for current planning state.

## 11. Planning Storage Contracts

```sql
CREATE TABLE planning_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    status TEXT NOT NULL CHECK (status IN ('open', 'completed', 'superseded', 'abandoned')),
    goal_id TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE plan_revisions (
    revision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES planning_sessions(session_id),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    revision_number INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('candidate', 'accepted', 'superseded', 'rejected')),
    parent_revision_id UUID NULL REFERENCES plan_revisions(revision_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (session_id, revision_number)
);

CREATE TABLE plan_artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_id UUID NOT NULL REFERENCES plan_revisions(revision_id),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    artifact_type TEXT NOT NULL CHECK (artifact_type IN ('diet_plan', 'meal_plan', 'review', 'recommendation')),
    content JSONB NOT NULL,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL CHECK (status IN ('candidate', 'accepted', 'superseded', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
```

Rules:

- Plan artifacts are versioned through revisions.
- Accepted revisions should supersede previous active revisions explicitly.
- Large artifacts may later move to object storage, but `artifact_id` remains canonical.

## 12. Clarification State Contract

```sql
CREATE TABLE clarification_state (
    clarification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    request_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'resolved', 'expired', 'superseded')),
    missing_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    question TEXT NOT NULL,
    expected_answer_type TEXT NULL,
    resume_route TEXT NULL,
    resume_node TEXT NULL,
    context JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL
);
```

Rules:

- pending clarification should pause write execution
- resolved clarification may resume a route
- clarification state is not a substitute for event history

## 13. Evidence Reference Contract

```sql
CREATE TABLE evidence_references (
    evidence_ref_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    artifact_id UUID NULL REFERENCES plan_artifacts(artifact_id),
    claim_id TEXT NULL,
    source_type TEXT NOT NULL CHECK (source_type IN ('paper', 'guideline', 'internal_evidence', 'manual_note', 'unknown')),
    source_id TEXT NULL,
    citation JSONB NOT NULL DEFAULT '{}'::jsonb,
    support_summary TEXT NULL,
    confidence TEXT NULL CHECK (confidence IS NULL OR confidence IN ('low', 'medium', 'high')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Rules:

- evidence references support claims or artifacts
- evidence references do not define user state
- evidence retrieval results are not automatically persisted unless attached by a tool

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

```sql
CREATE TABLE route_decisions (
    route_decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    selected_route_label TEXT NOT NULL,
    target_graph TEXT NOT NULL,
    confidence NUMERIC(5,4) NOT NULL,
    routing_method TEXT NOT NULL CHECK (routing_method IN ('rule', 'embedding', 'hybrid', 'llm_fallback', 'clarification', 'safety_override')),
    top_candidates JSONB NOT NULL DEFAULT '[]'::jsonb,
    ambiguity_reasons JSONB NOT NULL DEFAULT '[]'::jsonb,
    safety_status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_route_decisions_user_created ON route_decisions(user_id, created_at DESC);
```

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
  account_id: string
  user_id: string
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

```sql
CREATE TABLE tool_executions (
    tool_execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    tool_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'needs_clarification', 'blocked', 'rejected', 'error')),
    idempotency_key TEXT NULL,
    input_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    event_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    error_code TEXT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX idx_tool_executions_request ON tool_executions(request_id);
CREATE INDEX idx_tool_executions_user_created ON tool_executions(user_id, started_at DESC);
```

## 18. Agent Run Contract

```sql
CREATE TABLE agent_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id TEXT NOT NULL UNIQUE,
    trace_id TEXT NOT NULL,
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'needs_clarification', 'blocked', 'error')),
    raw_text TEXT NOT NULL,
    normalized_text TEXT NULL,
    selected_route_label TEXT NULL,
    response_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL,
    error_code TEXT NULL
);
```

Purpose: operational traceability for one agent turn.

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
  account_id: string
  user_id: string
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

