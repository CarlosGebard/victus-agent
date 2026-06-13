---
id: VICTUS-AGENT-OPERATIONS
title: Victus Agent Operations
status: draft
updated_at: 2026-06-12
owners:
  - victus-agent-runtime
related_services:
  - PostgreSQL
  - pgvector
  - LangGraph
  - LLM provider
  - embedding provider
  - observability backend
related_docs:
  - README.md
  - docs/000-SYSTEM-CONTEXT.md
  - 100-ARCHITECTURE.md
  - 300-CONTRACTS.md
---

# Victus Agent Operations

## 1. Operational Overview

`victus-agent` is operated as an account-aware agent runtime.

A normal runtime execution receives an authenticated message, resolves `account_id` and `user_id`, performs safety precheck, routes intent with embeddings, executes a graph branch, calls typed tools, appends domain events, updates projections, and returns a traceable response.

Operational safety depends on five guarantees:

- requests always have validated account context
- write operations always use idempotency keys
- events are immutable
- projections are rebuildable
- router embeddings can be reseeded from route definitions

## 2. Runtime Environments

### Local Development

Local development should run PostgreSQL with pgvector and a development LLM/embedding provider.

Required local capabilities:

- run migrations
- seed route definitions and route examples
- run the agent API
- execute smoke tests
- inspect events and projections

### Staging

Staging should use production-like auth, database migrations, observability, and provider configuration.

Staging is used to validate:

- account context mapping
- route confidence thresholds
- tool idempotency
- event/projector consistency
- safety blocking behavior
- traces without leaking secrets

### Production

Production must use managed secrets, controlled migrations, backup policies, structured logs, and trace sampling.

Production must not store provider access tokens directly in raw PostgreSQL columns. Store secret references such as `token_ref` and keep token material in a secret store or encrypted vault.

## 3. Expected Developer Commands

Codex should implement these commands as the stable local interface.

```bash
make install              # install dependencies
make db-up                # start local postgres/pgvector if using compose
make db-migrate           # apply migrations
make db-reset             # reset local database only
make seed-router          # seed active route definitions and route example embeddings
make dev                  # start local API/agent runtime
make test                 # run unit and integration tests
make lint                 # run formatting and static checks
make smoke-router         # verify embedding router behavior
make smoke-event-store    # verify append-only events and idempotency
make smoke-agent-turn     # verify one end-to-end agent turn
```

If a command cannot be implemented immediately, it should fail with a clear message instead of silently doing nothing.

The current implemented local validation interface is:

```bash
uv run --extra test victus test
uv run --extra test victus test tests/routing
uv run --extra test victus compile
uv run --extra test victus check
uv run victus db-upgrade
uv run victus db-current
uv run victus smoke-event-store
uv run victus smoke-projections
uv run victus smoke-projectors
uv run victus projections-rebuild local-smoke-user
```

Local PostgreSQL can be started with:

```bash
docker compose up -d postgres
```

## 4. Configuration

### Required Environment Variables

```bash
APP_ENV=local|staging|production
DATABASE_URL=postgresql://...
VICTUS_AUTH_PROVIDER=local|auth0|supabase|clerk|custom
VICTUS_AUTH_ISSUER=...
VICTUS_AUTH_JWKS_URL=...
ROUTER_EMBEDDING_PROVIDER=local|openai|voyage|cohere|custom
ROUTER_EMBEDDING_MODEL=...
ROUTER_EMBEDDING_DIM=1024
ROUTER_VECTOR_STORE=postgres_pgvector
ROUTER_TOP_K=5
ROUTER_CONFIDENCE_THRESHOLD=0.72
ROUTER_MARGIN_THRESHOLD=0.08
SAFETY_MODE=standard|strict
LLM_PROVIDER=...
LLM_MODEL=...
LITELLM_PROXY_API_BASE=https://...
LITELLM_PROXY_API_KEY=...
```

### Optional Environment Variables

```bash
LANGGRAPH_CHECKPOINT_DATABASE_URL=postgresql://...
OBSERVABILITY_PROVIDER=none|langfuse|otel
LANGFUSE_HOST=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
EVIDENCE_RAG_URL=...
FOOD_DATA_PROVIDER=stub|external
SECRET_STORE_URL=...
LITELLM_KEY=...
```

### Configuration Rules

- `DATABASE_URL` is required in every non-test runtime.
- `ROUTER_EMBEDDING_DIM` must match the stored vector column dimension.
- Changing the router embedding model requires reseeding route embeddings and may require a database migration.
- Auth configuration must be validated at startup outside local mode.
- Production must not run with `FOOD_DATA_PROVIDER=stub` unless explicitly allowed by a feature flag.
- LiteLLM proxy credentials must come from environment variables and must not be committed, printed, or stored in runtime traces.

## 5. Database Operations

### Apply Migrations

```bash
make db-migrate
```

The migration set must create:

- account identity tables
- user membership tables
- connected account references
- event store
- projector offsets
- projections
- planning tables
- clarification state
- evidence references
- router definitions and embeddings
- tool execution and route decision logs

### Rebuild Projections

```bash
make projections-rebuild USER_ID=<uuid>
make projections-rebuild-all
```

Projection rebuild reads from `user_events` and writes derived projection tables. It must not mutate event history.

### Check Projector Lag

```bash
make projections-status
```

The status command should compare each projector offset against the latest event sequence.

## 6. Router Operations

### Seed Route Definitions

```bash
make seed-router
```

This command should:

1. load route definitions from config or seed files
2. upsert route definitions
3. embed active route examples
4. store embeddings in `intent_route_examples`
5. mark the route version active

### Validate Router Behavior

```bash
make smoke-router
```

The smoke test should cover Spanish and English examples for:

- logging a meal
- updating profile restrictions
- creating a new plan
- revising an existing plan
- asking an evidence question
- describing a risky symptom
- sending a mixed or ambiguous request

The test should assert route label, minimum confidence, method used, and ambiguity behavior.

## 7. Execution Workflows

### Local Startup

```bash
cp .env.example .env
make install
make db-up
make db-migrate
make seed-router
make dev
```

### One Agent Turn

Operationally, one turn should produce:

- request id
- account id
- user id
- safety result
- router decision
- selected branch
- tool execution records if tools were used
- event references if events were appended
- projection updates if events affected projections
- response payload
- trace id

### Planning Save Flow

```text
new plan request
  -> safety precheck
  -> intent router: new_plan
  -> planning graph
  -> diet.generate_recommendation returns candidate artifact
  -> planning.manage_session saves session/revision/artifact
  -> plan events appended
  -> planning projection updated
```

### Event Logging Flow

```text
log request
  -> safety precheck
  -> intent router: log_update_data
  -> event capture graph
  -> typed tool validates command
  -> event appended with idempotency key
  -> affected projectors update projections
```

## 8. Observability

The runtime should log or trace:

- `request_id`
- `trace_id`
- `account_id`
- `user_id`
- selected route
- top route candidates
- router confidence
- safety status
- tool name
- tool status
- event references
- projector lag
- response status
- error type if failed

Do not log:

- raw access tokens
- refresh tokens
- secret values
- provider credentials
- private medical details outside structured, access-controlled event payloads

## 9. Failure and Recovery

### Duplicate Tool Execution

All write tools must use idempotency keys. If the same key is received again, the tool must return the original event references instead of creating duplicate events.

### Projector Failure

If projector execution fails after events are appended, the event store remains correct. Operators should fix the projector issue and run projection catch-up or rebuild.

### Router Embedding Failure

If route embeddings are unavailable, the router may fall back to deterministic rules or LLM classification. The response should record `routing_method=fallback` and include a warning in operational logs.

### Ambiguous Route

If the top route confidence is below threshold or the margin is too small, route to `MixedIntentResolver` or `ClarificationRoute`. Do not guess and execute write tools.

### Unsafe Request

If safety status is `blocked`, the runtime must not call planning or write tools except safety/clarification logging if allowed.

### Database Failure

If events cannot be appended, do not pretend the action succeeded. Return an error or recovery-safe response.

## 10. Troubleshooting

| Symptom | Likely Cause | Action |
|---|---|---|
| Router always returns ambiguous | route examples missing or embeddings not seeded | run `make seed-router` and `make smoke-router` |
| Wrong route for Spanish input | weak multilingual examples or wrong embedding model | add examples and reseed embeddings |
| Duplicate meals after retries | idempotency key missing or ignored | inspect `user_events.idempotency_key` constraint |
| Projection stale | projector failed or offset behind | run `make projections-status` then catch up/rebuild |
| Auth context missing | invalid provider config or local auth disabled | inspect auth middleware and `accounts` lookup |
| Plan saved but not visible | planning event appended but projection failed | rebuild planning projection |
| Safety warning not shown | response composer ignored safety state | test blocked/warning responses |

## 11. Operational Boundaries

Operations documentation owns runtime workflows, execution commands, configuration, observability, failure recovery, and smoke validation.

Operations documentation does not define schemas, event payloads, architecture boundaries, or historical decisions. Those belong in `300-CONTRACTS.md` and `100-ARCHITECTURE.md`.
