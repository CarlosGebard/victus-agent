# victus-agent

Runtime repository for the Victus agent prototype.

The current codebase implements a tool-first LangGraph agent runtime, not the full nutrition product:

- model-driven selection and bounded execution of the canonical typed tools
- checkpointed multi-turn state, clarification/confirmation interrupts, and bounded user memory
- an authenticated asynchronous `POST /chat` boundary
- an opt-in authenticated `POST /chat/debug` observability boundary for backend clients
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
docs/                 conceptual guides and domain-owned contracts
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
docker compose logs -f agent mcp
docker compose down
```

Compose starts PostgreSQL, the LangGraph agent on `8766`, and MCP on `8765`. Agent and MCP apply
pending application migrations during startup under one database lock; the agent also prepares its
LangGraph storage. Configure the external backend and LiteLLM proxy URLs in `.env` first.

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
uv run victus mcp-call event_capture '{"items":[{"name":"arroz","quantity":100,"unit":"g"}]}'
uv run victus-mcp
uv run victus-mcp-http
uv run victus-chat-http
```

Graph visualization:

```bash
uv run victus graph-dev --no-browser --port 2024
```

## Documentation

`docs/Overview.md` explains the system's purpose, scope, architecture, runtime flow, data model,
boundaries, and current limitations without implementation detail.

`docs/Tools.md` describes each implemented tool, records its source path, and defines the shared
`ToolResult` envelope.

`docs/Projections.md` describes the implemented projections, their source paths, schemas, and how
the agent uses them.

`docs/Events.md` describes active events, their emitting tools, common envelope, and how they connect
tools, persistence, projections, and the agent.

Specialized agent, database, safety, event-registry, and imported contracts remain under
`docs/contracts/`.
