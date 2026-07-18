---
id: ADR-20260718-LANGGRAPH-MEMORY-PERSISTENCE
title: LangGraph Checkpoints And Store For Agent Memory
status: accepted
updated_at: 2026-07-18
owners:
  - victus-agent-runtime
supersedes:
  - ADR-20260614-SESSION-CONTEXT-MANAGEMENT
related_docs:
  - ../../PLANS.md
  - ../contracts/session-context-v1.md
tags:
  - langgraph
  - memory
  - postgres
---

# Context

Victus needs conversational continuity within one thread and bounded memory across separate threads.
The repository introduced custom summary and pending-interaction tables, but the active graph never
wired them. Maintaining a second conversation persistence mechanism would duplicate state already
owned by LangGraph and would not provide native pause/resume semantics.

Domain events and projections already own durable user facts and must remain authoritative.

# Decision

- Use LangGraph PostgreSQL checkpoints for short-term, thread-scoped execution and conversation state.
- Map an authenticated `conversation_id` to LangGraph `thread_id`.
- Use LangGraph PostgreSQL Store for bounded cross-thread conversational memory under namespaces rooted
  in the authenticated `user_id`.
- Use LangGraph interrupts and resume commands for clarification and confirmation control flow.
- Keep domain events and projections separate from checkpoint and Store memory.
- Deprecate the custom conversation-summary and pending-interaction repository, models, and tables;
  remove them after a data audit, migration of eligible facts, and one compatibility window.

# Tradeoffs

Positive:

- Native checkpoint, resume, replay, human-in-the-loop, and fault-recovery behavior.
- One graph execution model instead of parallel custom session orchestration.
- Explicit separation between thread state, cross-thread memory, and domain truth.
- PostgreSQL-backed behavior across local integration, staging, and production.

Negative:

- Requires the separately installed PostgreSQL LangGraph persistence package.
- Adds LangGraph-managed tables and setup lifecycle alongside Alembic-managed domain tables.
- Existing pending interactions cannot become checkpoints because they lack execution position.
- Retention, ownership, deletion, backup, and graph-version compatibility become operational duties.

# Alternatives considered

- Keep custom summary/pending tables: rejected because they duplicate checkpoint state and require
  custom pause/resume behavior.
- Use checkpoints for all memory: rejected because checkpoints are thread scoped and do not provide
  the intended cross-thread namespace model.
- Store domain facts in LangGraph Store: rejected because events and projections already own them.
- Use only in-memory saver/store: rejected outside unit tests because restart loses state.
- Add semantic/vector memory immediately: deferred pending an embedding contract, retention policy,
  and measurable retrieval baseline.

# Consequences

- Production graph compilation requires a PostgreSQL checkpointer and Store.
- Chat callers require authenticated user and owned thread identifiers.
- Graph state and memories require explicit size, retention, provenance, and version bounds.
- LangGraph persistence setup is a deployment operation, not a normal request-startup action.
- The old session-context ADR and experimental contract become migration references, not target design.
- MCP stays external; internal graph nodes execute canonical tools directly through `ToolRuntime`.

# Related documents

- [Active LangGraph Agent V1 plan](../../PLANS.md)
- [Superseded session-context decision](20260614-session-context-management.md)
- [Architecture](../100-ARCHITECTURE.md)
- [Operations](../200-OPERATIONS.md)
- [Session context V1 contract](../contracts/session-context-v1.md)
