---
id: VICTUS-AGENT-OPERATIONS
title: Victus Agent Operations
status: current
updated_at: 2026-07-18
owners:
  - victus-agent-runtime
---

# Victus Agent Operations

## Local Setup

Create the environment file once and configure the external backend and LiteLLM proxy:

```bash
cp .env.example .env
```

Start the dependency-ordered local stack:

```bash
docker compose up -d --build
docker compose ps
```

Compose starts PostgreSQL, runs domain migrations and LangGraph storage setup to completion, then
starts chat on port `8766` and MCP on port `8765`. Stop the stack without deleting data with:

```bash
docker compose down
```

The default local database URL is:

```text
postgresql+psycopg://victus:postgres@localhost:5432/victus_agent
```

## Validation

The repository intentionally maintains a minimal critical suite. Add or expand tests only when a
runtime/security boundary, stable contract, regression, or persistence risk cannot be verified by
an existing test. Combine related behavior instead of growing one test per case.

Primary checks:

```bash
uv run --extra test victus test
uv run --extra test victus compile
uv run --extra test victus check
```

The full suite is already focused; narrower checks are optional:

```bash
uv run --extra test victus test tests/test_core_tools.py
uv run --extra test victus test tests/test_adapters.py
uv run --extra test victus test tests/test_domain_platform.py
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

## Database

Migrations live under `ops/db/`.

```bash
uv run victus db-upgrade
uv run victus db-current
uv run victus langgraph-storage-setup
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

For end-to-end tool validation through stdio or HTTP MCP, see
`docs/runbooks/mcp-tool-testing.md`.

Authenticate locally for MCP token relay:

```bash
BACKEND_API_URL=http://localhost:8000 uv run victus login
```

List tools:

```bash
uv run victus tools-list
uv run victus tool-inspect event_capture
uv run victus mcp-list-tools
```

Call a tool:

```bash
uv run victus mcp-call event_capture '{"user_id":"local-smoke-user","normalized_text":"hoy comi arroz"}'
uv run victus tool-run event_capture '{"user_id":"local-smoke-user","normalized_text":"hoy comi arroz"}'
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

## Chat API

Outside Compose, the authenticated JSON chat service can still run directly:

```bash
uv run victus-chat-http
curl http://localhost:8766/health
```

Compose handles `langgraph-storage-setup` automatically. Direct deployments must run it before
starting chat. See `docs/runbooks/langgraph-chat.md` for request, resume, recovery, and
troubleshooting procedures.

## Configuration

Runtime config:

```text
config/runtime.yml
```

Environment variables used locally:

```text
APP_ENV
BACKEND_API_URL
DATABASE_URL
LITELLM_PROXY_API_BASE
LITELLM_PROXY_API_KEY
LITELLM_KEY
INTENT_EVAL_MODEL
GROQ_API_KEY
GROQ_TRANSLATION_MODEL
LANGSMITH_API_KEY
LANGSMITH_PROJECT
LANGSMITH_TRACING
POSTGRES_PORT
VICTUS_DOCKER_BACKEND_API_URL
VICTUS_DOCKER_LITELLM_PROXY_API_BASE
VICTUS_MCP_HTTP_PORT
VICTUS_API_TOKEN
VICTUS_CHAT_HTTP_HOST
VICTUS_CHAT_HTTP_PORT
```

Do not commit secrets or print `.env` contents.

## Docs Sync

Repository docs are synced to the central docs repository by `.github/workflows/sync-docs.yml`.

See:

```text
docs/runbooks/docs-sync.md
```
