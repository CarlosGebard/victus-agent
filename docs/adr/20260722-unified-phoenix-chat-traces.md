---
id: VICTUS-ADR-20260722-UNIFIED-PHOENIX-CHAT-TRACES
title: Unified Phoenix Chat Traces
status: accepted
updated_at: 2026-07-22
owners:
  - victus-agent-runtime
---

# Context

The gateway and agent emitted independent Phoenix traces even though the gateway forwarded a W3C
`traceparent`. Automatic LangGraph instrumentation also displayed serialized tool results as raw
messages, making normal incident review difficult.

# Decision

Both services use project `victus-local`. The agent extracts the incoming W3C context at `POST
/chat` and creates `agent.http.chat` as a child of the gateway request. Automatic LLM inputs,
messages, and outputs remain visible in local Phoenix. Agent nodes publish concise, non-secret
`victus.*` attributes for the decision, tool outcome, and clarification state.

# Tradeoffs

Phoenix exposes prompt, message, and tool-result payloads needed to debug model decisions, at the
cost of showing local conversational data and serialized tool results. This configuration is local
only; production must make an explicit privacy decision before enabling it.

# Consequences

Operators inspect one trace per web chat turn and filter by `service.name` or `victus.*` attributes.
The gateway remains responsible for browser-facing request and stream spans; the agent owns graph
and tool summaries.
