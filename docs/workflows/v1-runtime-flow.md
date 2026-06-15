---
id: VICTUS-WORKFLOW-V1-RUNTIME-FLOW
title: V1 Runtime Flow
status: draft
version: v1
owner: victus-agent-runtime
updated_at: 2026-06-12
---
# V1 Runtime Flow

```text
receive user input
  -> normalize request
  -> context bootstrap
  -> safety precheck
  -> build standalone routing query
  -> if blocked: safety response
  -> route intent
  -> load node-specific projections
  -> expose node-specific tools
  -> call backend tool handler
  -> append events if needed
  -> run projectors affected by emitted events
  -> compose response
  -> update conversation state summary
  -> return route, response, event refs, warnings
```

## Rule

Every state mutation must pass through this chain:

```text
tool input validation
  -> safety/policy validation when needed
  -> event append
  -> projector update
  -> response composition
```

No node should mutate projections directly.

## Summary After Response

After the assistant response is composed, the runtime updates `ConversationStateSummary`.

The current implementation uses a deterministic updater. The V1 target allows an LLM-backed summarizer through `LLMClient`, but that call must produce bounded structured JSON and must not receive full chat history by default.

## Session Context Rule

The runtime must not load full conversation history by default.

Use this order when building turn context:

```text
PendingInteractionState
  -> ConversationStateSummary
  -> recent user messages
  -> last tool summary
  -> projections
  -> full history only as fallback
```
