---
id: VICTUS-AGENT-SYSTEM-CONTEXT
title: Victus Agent System Context
status: draft
updated_at: 2026-06-12
owners:
  - victus-agent-runtime
---

# Victus Agent System Context

## 1. Purpose

`victus-agent` exists to implement the runtime spine of the Victus Lifestyle Agent.

The repository turns nutrition and lifestyle user messages into safe, typed, traceable actions: log nutrition events, update profile context, manage goals, create or revise diet plans, answer evidence questions, and ask clarifying questions when the request is incomplete.

The repository is designed for production-oriented development. It must support account-aware execution, deterministic persistence, recoverable projections, typed tools, safety routing, observability, and embedding-assisted intent routing.

## 2. System Goals

The system is guided by these goals:

- preserve user history as immutable domain events
- derive fast user context through projections
- keep account identity separate from nutrition profile identity
- use LangGraph for orchestration, not as the canonical database
- use embeddings to route multilingual user requests before expensive reasoning
- expose tools through typed contracts and common result envelopes
- block unsafe requests before mutation or recommendation
- make every important action auditable through request, route, event, and tool execution records
- keep V1 small enough to implement and test quickly

### Non-Goals

V1 does not own the full food knowledge base, workout programming, final evidence RAG quality, wearable synchronization, full clinical decision support, billing, or mobile UI.

## 3. Repository Scope

This repository owns the agent runtime layer.

It owns:

- authenticated request handling at the application boundary
- account and user context resolution
- LangGraph graph definition and node orchestration
- safety precheck and safety triage routing
- embedding-assisted intent routing
- typed tool registry and backend tool handlers
- immutable event append behavior
- PostgreSQL projection rebuild behavior
- planning session, revision, and artifact persistence
- clarification state management
- evidence adapter interfaces for search and support attachment
- runtime logs, traces, and smoke validation

It intentionally does not own:

- infrastructure provisioning; that belongs in `victus-infra`
- full scientific evidence processing; that belongs in the evidence/paper processing system
- external identity provider internals
- provider token custody beyond storing safe references
- final consumer UI
- medical diagnosis

## 4. Documentation Map

```text
README.md                    -> human onboarding and repository entrypoint
docs/000-SYSTEM-CONTEXT.md   -> purpose, boundaries, terminology, design principles
docs/100-ARCHITECTURE.md     -> system shape, components, flows, dependencies
docs/200-OPERATIONS.md       -> runtime workflows, configuration, observability, recovery
docs/300-CONTRACTS.md        -> schemas, events, route contracts, database tables, tool rules
```

Codex should treat `300-CONTRACTS.md` as the strongest source of implementation truth.

## 5. Core Concepts

| Concept | Meaning |
|---|---|
| Account | Authenticated login identity. One account may later access one or more user profiles. |
| User | Nutrition/lifestyle subject that Victus reasons about. V1 may be 1:1 with an account, but the concepts must remain separate. |
| Auth Context | Request-time identity object derived from the authentication provider. |
| Request Context | Per-turn runtime context containing request id, account id, user id, locale, timezone, trace id, and raw input. |
| Event Store | Append-only PostgreSQL table containing immutable domain events. |
| Domain Event | Historical fact that something happened, such as `meal.logged`, `goal.set`, or `plan.artifact_saved`. |
| Projection | Current read model derived from events. Projections are rebuildable and must not be manually mutated by agent nodes. |
| LangGraph State | Temporary orchestration state for one agent run. It is not canonical user history. |
| Tool Handler | Backend function with typed input, validation, safety class, event emission rules, and common result envelope. |
| Intent Router | Hybrid router that combines rules, embeddings, thresholds, and optional LLM fallback to select the next graph. |
| Router Embedding Index | Versioned set of route examples embedded into a vector store for semantic intent matching. |
| Safety Guard | Policy layer that blocks or redirects risky medical, unsafe, or unsupported requests. |
| Planning Artifact | Versioned plan output generated from current projections, constraints, goal context, and optional evidence support. |
| Evidence Adapter | Interface to search or attach evidence. It supports explanations; it does not override safety or constraints. |

## 6. Expected Repository Structure

```text
src/                  -> application code, graph nodes, tool handlers, projectors
src/agent/            -> LangGraph graph, state models, routing orchestration
src/auth/             -> account context resolver and auth middleware integration
src/router/           -> intent route definitions, embedding search, thresholds
src/tools/            -> typed backend tool handlers
src/events/           -> event store append/read and event contracts
src/projectors/       -> projection rebuild and incremental projectors
src/db/               -> migrations, database access, SQL models
src/safety/           -> safety policy and triage logic
src/evidence/         -> evidence RAG adapter interface
config/               -> route config, safety config, environment defaults
scripts/              -> seed, migration, smoke, and operational commands
tests/                -> unit, integration, contract, and smoke tests
```

This is the expected shape. Codex may adjust implementation details, but it must preserve the ownership boundaries.

## 7. Design Principles

The system should remain contract-first, account-aware, event-driven, projection-oriented, safety-first, multilingual, observable, idempotent, and easy to rebuild.

Important rules:

- Never let the LLM write directly to projection tables.
- Never store provider access tokens in plain PostgreSQL fields.
- Never derive account identity from free-text user input.
- Never treat router embeddings as final truth when confidence is low.
- Never route unsafe requests directly into planning or event mutation.
- Prefer append-only correction events over destructive mutation.
- Prefer typed tool handlers over raw model-generated side effects.
- Prefer small, testable runtime slices over a large unvalidated agent.

## 8. V1 Implementation North Star

A successful V1 is not a perfect nutrition coach.

A successful V1 is a reliable agent skeleton that can receive an authenticated message, resolve the correct user profile, classify the intent with an embedding-assisted router, run the correct graph branch, execute validated tools, persist immutable events, update projections, and return a traceable response.
