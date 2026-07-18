---
id: VICTUS-CONTRACT-CHAT-V1
contract_id: victus.contract.agent.chat.v1
title: Authenticated Chat V1
status: current
version: v1
owner: victus-agent-runtime
domain: agent
contract_type: api
stability: experimental
updated_at: 2026-07-18
---
# Purpose

`POST /chat` is the authenticated, asynchronous, non-streaming application boundary for one Victus
LangGraph turn. It does not replace MCP or make checkpoints a domain source of truth.

# Identity

- The bearer token is validated through the Victus backend and yields the canonical `user_id`.
- `conversation_id` maps exactly to LangGraph `thread_id`.
- Existing threads may be invoked or resumed only by their stored authenticated owner.
- Model arguments never establish or change identity.

# Request

```ts
type ChatRequest = {
  conversation_id: string
  request_id: string
  message?: string
  resume?: { value: unknown }
  locale?: string
  timezone?: string
}
```

Exactly one of `message` or `resume` is required. Resume is valid only while the owned thread has a
pending interrupt and uses the same checkpoint execution position.

# Response

```ts
type ChatResponse = {
  conversation_id: string
  status: "completed" | "needs_user_response" | "blocked" | "error"
  message: string
  interrupt?: { id: string; kind: string; question: string; details: object }
  tool?: object
  events: object[]
  trace_id?: string
}
```

An acknowledged mutation must include the actual `ToolResult`; persisted mutations expose matching
event references. Declined confirmation, safety blocks, invalid identity, and rejected resume do not
execute the proposed mutation.

# Memory

Checkpoint state contains bounded messages, proposal/result state, loop count, response, compact
summary, and graph version. Store namespaces are `("users", user_id, "agent_memory", kind)` and
contain only explicit, bounded non-domain conversational or procedural memory. Events and
projections remain authoritative for meals, biometrics, symptoms, restrictions, goals, and plans.

# Compatibility

Graph version `1` rejects incompatible checkpoint resumes. Additive response fields are minor
changes; identity, ownership, status meaning, or request-shape breaks require a new major version.
