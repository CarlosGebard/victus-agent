---
id: ADR-20260614-SESSION-CONTEXT-MANAGEMENT
title: Session Context Management
status: accepted
date: 2026-06-14
owners:
  - victus-agent-runtime
---

# Context

Victus needs conversational continuity, but full chat history should not be the primary context source.

The runtime already treats domain events as canonical history and projections as current read models. Conversation memory must not duplicate those sources or become stale domain truth.

# Decision

Add explicit session context made of:

- `ConversationStateSummary`: compact structured memory for the next turn
- `PendingInteractionState`: active user-response dependency when the assistant asks a question, proposes an action, or waits for confirmation

The graph now bootstraps session context before safety/routing and updates the summary after response composition.

Preferred context order:

```text
PendingInteractionState
-> ConversationStateSummary
-> recent user messages
-> last tool summary
-> projections
-> full history only as fallback
```

# Consequences

- Short replies such as `yes`, `do it`, or `tomorrow instead` can be routed with pending context.
- Session context remains auditable JSON.
- Domain truth remains in events, projections, planning artifacts, and evidence records.
- LLM summarization can be introduced later through the existing `LLMClient` port without changing the storage contract.

# Boundary

Session context must not store:

- full chat history
- large tool outputs
- duplicated projection state
- nutrition facts that belong in events or projections
- artifact bodies
