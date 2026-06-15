---
id: VICTUS-CONTRACT-SESSION-CONTEXT-V1
contract_id: victus.contract.agent.session_context.v1
title: Session Context V1
status: draft
version: v1
owner: victus-agent-runtime
domain: agent
contract_type: runtime_schema
stability: experimental
updated_at: 2026-06-14
---
# Session Context V1

## 1. Purpose

Session context preserves task continuity without relying on full conversation history.

It is compact conversational memory only. It is not domain truth.

## 2. ConversationStateSummary

```ts
type ConversationStateSummary = {
  conversation_id: string
  user_id: string
  summary_version: "session-context-v1"
  user_current_goal: string
  current_topic: string
  stable_decisions: string[]
  recent_decisions: string[]
  active_task?: {
    task_name: string
    task_status: "open" | "waiting_user" | "completed" | "blocked"
    next_expected_step?: string
  }
  pending_interaction?: PendingInteractionState
  relevant_context: string[]
  last_tool_summary?: string
  unresolved_questions: string[]
  should_inject_next_turn: boolean
  updated_at: string
}
```

## 3. PendingInteractionState

```ts
type PendingInteractionState = {
  conversation_id: string
  user_id: string
  pending_kind: "question" | "confirmation" | "choice" | "proposal"
  assistant_prompt: string
  expected_user_response: string
  resume_graph?: string
  resume_node?: string
  created_at: string
  updated_at: string
}
```

## 4. Rules

- The bootstrap node must prefer pending interaction state for short or referential user replies.
- The router should receive a standalone routing query assembled from current text plus relevant session context.
- The summary-after-response node must write structured JSON only.
- The current summary updater is deterministic; an LLM-backed updater may be added through `LLMClient` as long as it returns this schema.
- Full chat history is a fallback, not the default.
- Events and projections remain the canonical source for user facts and domain state.
