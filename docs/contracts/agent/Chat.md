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
updated_at: 2026-07-21
---
# Purpose

`POST /chat` is the authenticated, asynchronous, non-streaming application boundary for one Victus
LangGraph turn. It does not replace MCP or make checkpoints a domain source of truth.

Source: `src/adapters/langgraph/capabilities/contracts.py`

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
pending interrupt and uses the same checkpoint execution position. A new `message` sent while an
interrupt is pending is rejected with `409`; clients must convert the user's answer into
`resume.value` instead of starting another turn from the paused checkpoint.

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

# Debug Boundary

`POST /chat/debug` accepts the same bearer token and `ChatRequest`, executes the same graph path, and
returns the normal response fields plus:

```ts
type ChatDebugResponse = ChatResponse & {
  request_id: string
  debug: {
    graph_version?: string
    thread_id: string
    authenticated_user_id: string
    next_nodes: string[]
    execution: {
      started_at: string
      completed_at: string
      duration_ms: number
      resumed: boolean
    }
    state: object
  }
}
```

`state` is a bounded serialization of the authenticated turn's request, safety, intent,
projections, tool context, planning, evidence, clarification, response, memory, audit, and messages.
Collections, nesting, and strings are size-limited. Fields whose names indicate tokens,
authorization, cookies, credentials, passwords, secrets, or API keys are replaced with
`"[redacted]"`.

The debug boundary must preserve `/chat` authentication, thread ownership, graph-version, and resume
rules. It must not return bearer tokens, credentials, environment values, system prompts, or raw
checkpoint payloads. It is disabled unless `VICTUS_CHAT_DEBUG_ENABLED` is true. Enabling or adding
debug state fields is backward compatible; weakening redaction or ownership is forbidden.
