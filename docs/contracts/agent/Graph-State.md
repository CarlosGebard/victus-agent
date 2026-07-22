---
id: VICTUS-CONTRACT-LANGGRAPH-STATE-V1
contract_id: victus.contract.agent.langgraph_state.v1
title: LangGraph State V1
status: current
version: v1
owner: victus-agent-runtime
domain: agent
contract_type: runtime_schema
stability: experimental
updated_at: 2026-07-21
---

# LangGraph State V1

## Purpose

Defines the shared orchestration state passed between agent graph nodes. It may preserve bounded
conversation continuity, but it is not canonical user history or domain state.

Source: `src/adapters/langgraph/engine/state.py`

## Schema

All top-level sections are optional because nodes build the state incrementally.

```ts
type VictusGraphState = {
  messages?: unknown[]
  request?: {
    request_id?: string
    user_id?: string
    original_text?: string
    working_text?: string
    received_at?: string
    locale?: string
    timezone?: string
    conversation_id?: string
  }
  safety?: {
    status?: "unknown" | "ok" | "warning" | "blocked" | "needs_clarification"
    reasons?: string[]
    decision?: string
    severity?: string
    categories?: string[]
    matched_rules?: string[]
    reason_codes?: string[]
    blocked_tools?: string[]
    allowed_next_route?: string
    audit_required?: boolean
  }
  intent?: {
    primary_intent?: string
    confidence?: number
    rationale?: string
    target_node?: string
    subintents?: string[]
  }
  projections?: {
    user_profile?: UserProfileProjection
    constraint?: ConstraintProjection
    nutrition_status?: NutritionStatusProjection
    planning_history?: PlanningHistoryProjection
    loaded_at?: string
    max_event_seq?: number
  }
  tool_context?: {
    allowed_tools?: string[]
    proposed_action?: Record<string, unknown>
    last_tool_result?: Record<string, unknown>
    tool_results?: Array<Record<string, unknown>>
    loop_count?: number
    confirmation?: Record<string, unknown>
  }
  planning?: {
    session_id?: string
    revision_id?: string
    artifact_id?: string
    candidate_artifact?: Record<string, unknown>
    validation_report?: Record<string, unknown>
  }
  evidence?: {
    query?: string
    retrieved_evidence?: unknown[]
    cited_evidence?: unknown[]
    generated_claims?: unknown[]
  }
  clarification?: {
    clarification_id?: string
    missing_fields?: string[]
    question?: string
    expected_answer_type?: string
    resume_node?: string
    resume_action?: string
  }
  response?: {
    mode?: "final" | "clarification" | "blocked" | "error"
    user_message?: string
    internal_notes?: string[]
  }
  memory?: {
    recalled?: Array<Record<string, unknown>>
    compact_summary?: string
  }
  graph_version?: string
  audit?: {
    node_path: string[]
    events_emitted: Array<{ event_id: string; event_type: string; seq: number }>
    warnings: string[]
    errors: string[]
    transforms: Array<Record<string, string>>
  }
}
```

## Rules

- `messages` uses LangGraph message reduction and remains bounded by finalization policy.
- Authenticated identity originates in `request.user_id`; model output must not change it.
- Nodes may read projections but must not write projection storage directly.
- Tool proposals are validated and executed through `ToolRuntime`.
- Safety blocks prevent state-changing tool execution.
- Checkpoint resumes require graph version `1` and the same owned conversation.
- Events and projections remain authoritative for durable user facts.
