---
id: VICTUS-CONTRACT-TOOL-RESULT-ENVELOPE-V1
contract_id: victus.contract.agent.tool_result_envelope.v1
title: Tool Result Envelope V1
status: draft
version: v1
owner: victus-agent-runtime
domain: agent
contract_type: schema
stability: experimental
updated_at: 2026-06-12
---
# Tool Result Envelope V1

## 1. Purpose

Defines the common return format for every backend tool handler exposed to the Victus agent runtime.

Individual tools may define their own `data` payload, but they must all return this envelope shape.

## 2. Type

```ts
type ToolStatus =
  | "success"
  | "needs_clarification"
  | "blocked"
  | "rejected"
  | "error"

type SafetyStatus = "ok" | "warning" | "blocked" | "needs_clarification"

type ToolEventRef = {
  event_id: string
  event_type: string
  seq: number
}

type ToolResult<TData = unknown> = {
  status: ToolStatus
  data: TData | null
  events_emitted: ToolEventRef[]
  warnings: string[]
  clarification: ClarificationRequest | null
  safety: {
    status: SafetyStatus
    reasons: string[]
  }
  meta: {
    confidence?: number
    schema_version: 1
    handler_version?: string
    trace_id?: string
  }
}

type ClarificationRequest = {
  missing_fields: string[]
  question: string
  expected_answer_type:
    | "quantity"
    | "time"
    | "meal_reference"
    | "preference_strength"
    | "restriction_type"
    | "goal_target"
    | "yes_no"
    | "free_text"
  resume_node?: string
  resume_action?: string
}
```

## 3. Rules

- `success` means the handler completed the requested action.
- `needs_clarification` means no unsafe write was performed and the graph should route to clarification.
- `blocked` means the request was rejected by safety or policy.
- `rejected` means validation failed for non-safety reasons.
- `error` means an unexpected runtime failure occurred.
- `events_emitted` must be empty for pure compute tools unless they explicitly persist output.
- Tool handlers must not return unvalidated LLM text as persisted state.

## 4. V1 Implementation Note

Existing tool docs currently show status as a string like `"success | needs_clarification | blocked | rejected | error"`. In code, implement this as an enum, not a free-form string.
