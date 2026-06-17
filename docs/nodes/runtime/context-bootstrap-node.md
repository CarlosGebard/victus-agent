---
id: VICTUS-NODE-CONTEXT-BOOTSTRAP
contract_id: victus.node.context_bootstrap
title: Context Bootstrap Node
status: draft
version: v1
owner: victus-agent-runtime
domain: orchestration
contract_type: orchestration_node
stability: experimental
updated_at: 2026-06-14
---
# Context Bootstrap Node

## 1. Purpose

Builds the minimal per-turn context needed before safety and routing.

This node prevents Victus from relying on full conversation history as the default context source. It loads compact session state, prioritizes pending user-response dependencies, and writes a standalone `routing_query` for downstream routing.

## 2. Inputs

```ts
type ContextBootstrapInput = {
  request: {
    original_text: string
    working_text: string
    user_id?: string
    conversation_id?: string
  }
}
```

Optional repository reads:

- latest `ConversationStateSummary`
- active `PendingInteractionState`

## 3. Outputs

```ts
type ContextBootstrapOutput = {
  request: {
    working_text: string
  }
  session_context: {
    conversation_id?: string
    summary?: ConversationStateSummary
    pending_interaction?: PendingInteractionState
    bootstrap: BootstrapContext
  }
}
```

## 4. Responsibilities

- Load explicit session context when `conversation_id` is present.
- Prefer `PendingInteractionState` for short, referential, or confirmation-like messages.
- Build a routing query that can stand alone for the intent router.
- Keep context small and auditable.

## 5. Forbidden Responsibilities

- Must not load full chat history by default.
- Must not mutate domain events or projections.
- Must not execute tools.
- Must not summarize the conversation.
- Must not treat conversation memory as domain truth.

## 6. Runtime Position

```text
normalize request
  -> context bootstrap
  -> safety precheck
  -> route intent
```

## 7. Implementation Status

Current implementation lives in `src/agent/nodes/context.py`.

It currently builds routing context deterministically. Future semantic canonicalization may use an LLM through the application `LLMClient` port, but broad chat history must still remain a fallback only.
