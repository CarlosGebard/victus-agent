---
id: VICTUS-IMPLEMENTATION-BUILD-ORDER
title: Victus Agent V1 Build Order
status: draft
version: v1
owner: victus-agent-runtime
updated_at: 2026-06-12
---
# Victus Agent V1 Build Order

## Phase 1 — Contracts in Code

Status: started. Core Python contracts exist for tool results, event envelopes,
domain event payloads, projections, LLM port, and LangGraph state.

Implement Pydantic models for:

- tool result envelope
- event envelope
- domain event payloads
- projection views
- LangGraph state
- node inputs and outputs
- LLM client port and request/response envelopes

Do not implement business logic until these models validate.

## Phase 2 — Database

Status: started. Alembic configuration, initial PostgreSQL migration, SQLAlchemy
schema metadata, and a minimal event store repository exist.

Implement migrations for:

- `user_events`
- `projector_offsets`
- projection tables
- planning tables
- clarification state
- evidence citations

Add repository classes for event append, event replay, projection load, and planning artifact persistence.

## Phase 3 — Projectors

Status: started. Replayable user profile and nutrition status projectors exist
for the first V1 event types.

Implement projectors for:

- user profile
- constraints
- nutrition status
- planning history

Every projector must be replayable from zero.

## Phase 4 — Tool Handlers

Implement backend handlers for current tool docs:

- `nutrition.manage_meal`
- `biometrics.log`
- `symptom.log`
- `profile.manage_context`
- `goal.manage`
- `planning.manage_session`
- `feedback.record`
- `diet.generate_recommendation`
- `evidence.search`
- `evidence.manage_support`
- `safety.triage`
- `clarification.manage`

Handlers must return `ToolResult` and write events only through the event repository.

## Phase 5 — LLM Adapter Boundary

Implement the LiteLLM adapter behind the application LLM port.

Rules:

- graph nodes and use cases depend on `LLMClient`
- only `src/infrastructure/llm/` imports LiteLLM
- credentials are read from environment variables only
- live proxy checks are opt-in smoke tests

## Phase 6 — LangGraph Runtime

Implement nodes in this order:

1. `SafetyPrecheckNode`
2. `IntentRouterNode`
3. `EventCaptureNode`
4. `ProfileUpdateNode`
5. `PlanIntentNode`
6. `EvidenceAnswerNode`
7. `ClarificationNode`
8. `ResponseComposer`

Start with deterministic rules and small LLM usage. Do not expose the full tool catalog at the router.

## Phase 7 — End-to-End Harness

Create a CLI or minimal API endpoint that accepts:

```json
{
  "user_id": "demo-user",
  "message": "I ate chicken and rice for lunch"
}
```

It should return:

- final response text
- selected route
- emitted events
- updated projection summaries
- warnings or clarification requests

## Phase 8 — Tests

Add test coverage for:

- valid event append
- duplicate idempotency key
- meal logging projection update
- restriction update projection update
- unsafe symptom safety block
- goal setting flow
- basic plan generation flow
- clarification flow
- evidence adapter flow
