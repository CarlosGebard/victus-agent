# victus-agent

Runtime repository for the Victus agent prototype.

The current codebase implements a tool-first LangGraph agent runtime, not the full nutrition product:

- model-driven selection and bounded execution of the canonical typed tools
- checkpointed multi-turn state, clarification/confirmation interrupts, and bounded user memory
- an authenticated asynchronous `POST /chat` boundary
- one catalog and runtime shared by every tool surface
- vertical tools for capture, profile, planning, feedback, evidence, and interaction
- LangGraph, MCP stdio/HTTP, and CLI adapters
- event, projection, session-context, and tool result models
- PostgreSQL repositories and Alembic migrations under `ops/db/`
- local CLI commands under `uv run victus ...`

The source of truth for user history is the event store. Projections are rebuildable read
models. LangGraph state is orchestration state only.

## Current Status

Status: `LangGraph V1 / testable runtime`

Implemented for deterministic unit testing with in-memory LangGraph persistence and for PostgreSQL
deployment with explicit storage setup. Provider and database acceptance still require configured
external services.

## Repository Map

```text
src/tools/            capabilities, catalog, shared contracts, runtime
src/domain/           events, projections, session context, shared invariants
src/adapters/         LangGraph, MCP, and CLI adapters
src/victus_platform/  database, repositories, LLM, safety, identity, config, telemetry
src/bootstrap/        dependency assembly
ops/db/               Alembic config and migrations
ops/scripts/          helper scripts
config/               runtime config
docs/                 compact system documentation and contracts
tests/                unit, contract, repository, CLI, graph, and MCP tests
```

## Useful Commands

```bash
uv run --extra test victus test
uv run --extra test victus test tests/agent
uv run --extra test victus compile
uv run --extra test victus check
```

Complete local stack:

```bash
cp .env.example .env  # only when .env does not exist
docker compose up -d --build
docker compose ps
docker compose logs -f chat mcp
docker compose down
```

Compose starts PostgreSQL, runs both idempotent setup jobs, and then starts chat on `8766` and MCP
on `8765`. Configure the external backend and LiteLLM proxy URLs in `.env` first.

Database and smoke commands:

```bash
uv run victus db-upgrade
uv run victus langgraph-storage-setup
uv run victus db-current
uv run victus smoke-event-store
uv run victus smoke-projections
uv run victus smoke-projectors
uv run victus projections-rebuild local-smoke-user
```

MCP commands:

```bash
uv run victus mcp-list-tools
uv run victus mcp-call event_capture '{"user_id":"local-smoke-user","normalized_text":"hoy comi arroz"}'
uv run victus-mcp
uv run victus-mcp-http
uv run victus-chat-http
```

Graph visualization:

```bash
uv run victus graph-dev --no-browser --port 2024
```

## Documentation

Read in this order:

1. [`docs/000-SYSTEM-CONTEXT.md`](docs/000-SYSTEM-CONTEXT.md)
2. [`docs/100-ARCHITECTURE.md`](docs/100-ARCHITECTURE.md)
3. [`docs/200-OPERATIONS.md`](docs/200-OPERATIONS.md)
4. [`docs/300-CONTRACTS.md`](docs/300-CONTRACTS.md)

Detailed contracts live under [`docs/contracts/`](docs/contracts/). Avoid adding new planning
docs unless the current code or a stable contract changes.

MCP tool testing: [`docs/runbooks/mcp-tool-testing.md`](docs/runbooks/mcp-tool-testing.md).
