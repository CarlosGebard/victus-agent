---
id: ADR-20260721-RUNTIME-OWNED-DEVELOPMENT-SCHEMA-SETUP
title: Runtime-Owned Development Schema Setup
status: accepted
updated_at: 2026-07-21
owners:
  - victus-agent-runtime
related_docs:
  - ../runbooks/langgraph-chat.md
tags:
  - database
  - development
  - compose
---

# Context

The local Compose stack exposed separate Alembic and LangGraph setup jobs alongside the persistent
database, agent, and MCP processes. Those one-shot containers made the development topology harder
to read even though schema preparation is required before either runtime accepts traffic.

# Decision

In local Compose, `agent` and `mcp` prepare required application schema during startup under one
PostgreSQL advisory lock. The agent also prepares LangGraph checkpoint and Store tables. Compose
exposes the persistent database, LangGraph agent, and MCP as distinct services without migration
jobs.

# Tradeoffs

- Local startup remains a single `docker compose up` operation and concurrent migration attempts
  are serialized.
- Runtime containers retain schema-change permissions in development.
- Production deployments should move schema preparation to a controlled deployment job with
  separate credentials before restricting application roles.

# Alternatives considered

- Separate Compose jobs were operationally safe but obscured the intended local service topology.
- A host script made startup ordering an operator responsibility.
- Recreating PostgreSQL from a base schema would discard development conversations and checkpoints.

# Consequences

Startup fails before serving traffic when schema preparation fails. New application services that
use the shared schema must use the same setup lock or rely on a production migration workflow.

# Related documents

- [LangGraph chat runbook](../runbooks/langgraph-chat.md)
- [Compose stack](../../compose.yml)
