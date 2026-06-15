---
id: ADR-20260614-CLEAN-ARCHITECTURE-SOURCE-LAYOUT
title: Clean Architecture Source Layout
status: accepted
date: 2026-06-14
owners:
  - victus-agent-runtime
---

# Context

The repository is early and had several root-level packages mixing domain contracts, routing services, persistence adapters, and orchestration code.

That layout made it harder to see dependency direction as new modules such as session context were added.

# Decision

Organize `src` by architectural layer:

```text
src/domain/             -> domain contracts and pure models
src/application/        -> ports, config, routing, and application services
src/infrastructure/     -> database, repositories, and provider adapters
src/agent/              -> LangGraph orchestration
src/victus_cli/         -> local operational CLI
```

Routing now lives under `application.routing`.

PostgreSQL schema, engine, and repositories live under `infrastructure`.

Events, projection models, projectors, tool contracts, and session context models live under `domain`.

# Consequences

- Dependency direction is easier to audit.
- Domain code no longer owns concrete persistence adapters.
- Future modules should choose their layer by responsibility instead of creating new root-level packages.
- Import paths changed while runtime behavior stayed the same.
