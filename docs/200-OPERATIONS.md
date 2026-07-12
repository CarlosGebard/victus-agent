---
id: VICTUS-AGENT-OPERATIONS
title: Victus Agent Operations
status: current
updated_at: 2026-07-12
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

List tools:

```bash
uv run victus mcp-list-tools
```

Call a tool:

```bash
uv run victus mcp-call event_capture '{"user_id":"local-smoke-user","normalized_text":"hoy comi arroz"}'
```

Start the stdio server for an MCP client:

```bash
uv run victus-mcp
```

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
