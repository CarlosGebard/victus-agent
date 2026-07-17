---
id: VICTUS-AGENT-OPERATIONS
title: Victus Agent Operations
status: current
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Victus Agent Operations

## Local Setup

Use `uv` as the project runner.

The local database is PostgreSQL from `compose.yml`:

```bash
docker compose up -d postgres
```

Environment example:

```bash
cp .env.example .env
```

The default local database URL is:

```text
postgresql+psycopg://victus:postgres@localhost:5432/victus_agent
```

## Validation

Primary checks:

```bash
uv run --extra test victus test
uv run --extra test victus compile
uv run --extra test victus check
```

Focused checks:

```bash
uv run --extra test victus test tests/agent
uv run --extra test victus test tests/victus_mcp
uv run --extra test victus test tests/contracts
```

Llama Guard 4 serverless classification:

```bash
hf auth login
uv run victus safety-check "Ignore previous instructions"
```

`victus safety-check` calls Hugging Face Router chat completions with
`meta-llama/Llama-Guard-4-12B:together`. It requires `HF_TOKEN`, `HUGGING_FACE_TOKEN`, or
`HUGGING_FACE_API_KEY`. `HUGGING_FACE_ROUTER_BASE_URL` may override the default
`https://router.huggingface.co/v1` for tests.

The response is normalized from Llama Guard output such as `safe` or `unsafe\nS11`.
The request includes strict classification instructions that tell Llama Guard 4 to return only
`safe` or `unsafe` plus S1-S14 category codes.

Current known failure:

```text
tests/safety/test_self_harm_rules.py imports safety.*, but no safety package exists in the tree.
```

Fix by restoring the `safety` package or removing/updating those tests and related packaging
references.

## Database

Migrations live under `ops/db/`.

```bash
uv run victus db-upgrade
uv run victus db-current
```

Smoke checks:

```bash
uv run victus smoke-event-store
uv run victus smoke-projections
uv run victus smoke-projectors
uv run victus projections-rebuild local-smoke-user
```

These commands require `DATABASE_URL` and a reachable local PostgreSQL instance.

## MCP

Authenticate locally for MCP token relay:

```bash
BACKEND_API_URL=http://localhost:8000 uv run victus login
```

List tools:

```bash
uv run victus mcp-list-tools
```

Call a tool:

```bash
uv run victus mcp-call event_capture '{"user_id":"local-smoke-user","normalized_text":"hoy comi arroz"}'
BACKEND_API_URL=http://localhost:8000/v1 uv run victus mcp-call recuperar_perfil '{}'
```

Start the stdio server for an MCP client:

```bash
uv run victus-mcp
```

Start the deployable Streamable HTTP MCP server:

```bash
uv run victus-mcp-http
curl http://localhost:8765/health
```

Runtime overrides:

```text
VICTUS_MCP_HTTP_HOST=0.0.0.0
VICTUS_MCP_HTTP_PORT=8765
BACKEND_API_URL=http://localhost:8000/v1
```

Docker build/run:

```bash
docker build -t victus-agent-mcp .
docker run --rm -p 8765:8765 -e BACKEND_API_URL=http://host.docker.internal:8000/v1 victus-agent-mcp
```

LangGraph web-app clients should connect to:

```text
http://<victus-agent-host>:8765/mcp
```

Register the local server with Codex:

```bash
codex mcp add victus-agent -- uv run victus-mcp
codex mcp list
```

Token lookup order for `recuperar_perfil`:

1. `VICTUS_API_TOKEN`
2. OAuth `access_token` from `~/.victus/session.json`
3. Legacy `VICTUS_API_TOKEN` from `~/.victus/session.json`

`victus login` opens the browser and completes OAuth Authorization Code + PKCE through a local
`127.0.0.1` callback. The MCP server forwards the resulting access token as
`Authorization: Bearer <token>` and does not print it. If the access token is near expiry and a
refresh token exists, the MCP server refreshes the local session before calling the backend.

Remove the local session:

```bash
uv run victus logout
```

The stdio server is for local users and Codex desktop. The HTTP server is for infrastructure and
service-to-service integration. Do not depend on `~/.victus/session.json` in production containers;
pass request/session auth at the web-app boundary.

## Graph Dev

```bash
uv run victus graph-dev --no-browser --port 2024
```

`LANGSMITH_API_KEY` is only needed for LangGraph Studio/LangSmith-backed visualization.

## Configuration

Runtime config:

```text
config/runtime.yml
```

Environment variables used locally:

```text
APP_ENV
DATABASE_URL
LITELLM_PROXY_API_BASE
LITELLM_PROXY_API_KEY
LITELLM_KEY
GROQ_API_KEY
GROQ_TRANSLATION_MODEL
LANGSMITH_API_KEY
```

Do not commit secrets or print `.env` contents.

## Docs Sync

Repository docs are synced to the central docs repository by `.github/workflows/sync-docs.yml`.

See:

```text
docs/runbooks/docs-sync.md
```
