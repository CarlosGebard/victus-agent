---
id: VICTUS-NODE-SUMMARY-AFTER-RESPONSE
contract_id: victus.node.summary_after_response
title: Summary After Response Node
status: draft
version: v1
owner: victus-agent-runtime
domain: orchestration
contract_type: orchestration_node
stability: experimental
updated_at: 2026-06-14
---
# Summary After Response Node

## 1. Purpose

Updates compact session context after the assistant response has been composed.

This node preserves only the information needed to continue the next turn: current goal, topic, recent routing decision, active task, pending interaction, and small relevant context snippets.

## 2. Inputs

```ts
type SummaryAfterResponseInput = {
  request: RequestState
  session_context?: SessionContextState
  intent?: IntentState
  response?: ResponseState
  audit?: AuditState
}
```

## 3. Outputs

```ts
type SummaryAfterResponseOutput = {
  session_context: {
    updated_summary: ConversationStateSummary
    pending_interaction?: PendingInteractionState
  }
}
```

If a session context repository is configured, the node persists:

- `ConversationStateSummary`
- `PendingInteractionState` when the response is a clarification
- clears pending interaction when the final response no longer waits for the user

## 4. Responsibilities

- Run after response composition.
- Persist structured JSON session memory.
- Capture explicit pending interactions when the assistant asks for user input.
- Keep large outputs and domain state out of the summary.
- Preserve enough context for short next-turn replies.

## 5. Forbidden Responsibilities

- Must not store full chat history.
- Must not duplicate projection state.
- Must not persist large tool outputs or artifacts.
- Must not create domain events.
- Must not replace event or projection truth.

## 6. Runtime Position

```text
compose response
  -> summary after response
  -> end
```

## 7. LLM Summarization Contract

The intended V1 design allows this node to call an LLM through the application `LLMClient` port after the final assistant response in order to produce a compact structured `ConversationStateSummary`.

That LLM call must:

- receive only bounded inputs: previous summary, latest user message, assistant response, route decision, graph result, tool summaries, and pending interaction state
- return JSON matching the session context schema
- avoid full chat history by default
- avoid inventing facts
- avoid duplicating domain state that belongs in events, projections, or artifacts

## 8. Implementation Status

Current implementation lives in `src/agent/nodes/summary.py`.

It is deterministic today and does not yet call an LLM. The LLM summarizer is the next extension point, not current behavior.
