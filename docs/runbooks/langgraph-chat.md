---
id: VICTUS-RUNBOOK-LANGGRAPH-CHAT
title: LangGraph Chat Operations
status: current
updated_at: 2026-07-18
owners:
  - victus-agent-runtime
---
# Setup

Create `.env` once, then configure `VICTUS_DOCKER_BACKEND_API_URL`,
`VICTUS_DOCKER_LITELLM_PROXY_API_BASE`, and the proxy key:

```bash
cp .env.example .env
docker compose up -d --build
docker compose ps
```

The `db-migrate` and `langgraph-setup` jobs must finish successfully before chat starts. Both setup
paths are idempotent; request-serving application startup does not run migrations.

# Run

Check both HTTP services:

```bash
curl http://localhost:8766/health
curl http://localhost:8765/health
docker compose logs -f chat mcp
```

Stop all services while retaining PostgreSQL data with `docker compose down`. Use
`docker compose down -v` only when intentionally deleting local data.

Send a new turn with a backend-issued bearer token:

```bash
curl -X POST http://localhost:8766/chat \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"conversation_id":"demo-1","request_id":"turn-1","message":"hoy comi arroz"}'
```

When status is `needs_user_response`, resume the same conversation:

```bash
curl -X POST http://localhost:8766/chat \
  -H 'Authorization: Bearer <token>' \
  -H 'Content-Type: application/json' \
  -d '{"conversation_id":"demo-1","request_id":"turn-2","resume":{"value":{"accepted":true}}}'
```

# Recovery

- A request may be retried with the same `request_id`; tool idempotency keys are stable per loop.
- Restore PostgreSQL from backup to recover checkpoints, Store memory, events, and projections.
- Rebuild domain projections with `uv run victus projections-rebuild <user_id>` after event recovery.
- Do not fabricate checkpoints from legacy `pending_interaction_state`; ask the user to repeat it.
- Legacy summary/pending tables remain read-only compatibility data until a separately audited drop.

# Troubleshooting

- `503 /health`: verify database reachability, LangGraph setup, and LiteLLM configuration.
- `401 /chat`: verify the bearer token against `BACKEND_API_URL/me`.
- `403 /chat`: the authenticated user does not own that conversation.
- `409 /chat`: there is no pending interrupt or the checkpoint graph version is incompatible.
- `503 /chat`: inspect database and LiteLLM availability; responses intentionally hide provider and
  credential details.
