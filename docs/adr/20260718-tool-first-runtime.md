---
id: ADR-20260718-TOOL-FIRST-RUNTIME
title: Tool-First Runtime And Capability Layout
status: accepted
date: 2026-07-18
owners:
  - victus-agent-runtime
---

# Context

Layer-first packages split each capability across domain, application, LangGraph, MCP, and CLI.
Repeated manifests, event mappings, validators, and action directories created multiple sources of
truth and made a complete use case difficult to inspect.

# Decision

- Organize product behavior under vertical `src/tools/<capability>/` packages.
- Register public metadata, schemas, exposure, and implementation once in `tools/catalog.py`.
- Execute every adapter invocation through `ToolRuntime`.
- Keep shared events/projections in `domain`, technical implementations in `victus_platform`, and
  dependency assembly in `bootstrap`.
- Treat clarification and confirmation as interaction continuation mechanisms.
- Preserve existing public tool names while migrating internal contracts.

The platform package is named `victus_platform` to avoid collision with Python's standard-library
`platform` module.

# Alternatives

- Keep layered packages and add more registries: rejected because duplication remains.
- Make MCP the canonical boundary: rejected because tools must run without MCP.
- Rewrite all behavior behind new APIs: rejected in favor of behavioral migration and contract
  tests.

# Consequences

- Tools are independently testable and do not import adapters.
- LangGraph, MCP, CLI, and tests share one execution and persistence path.
- Adding a tool requires one capability package and one catalog entry.
- Python import paths changed; CLI and MCP command names remain stable.
