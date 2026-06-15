---
id: VICTUS-CONTRACT-LANGGRAPH-STATE-V1
contract_id: victus.contract.agent.langgraph_state.v1
title: LangGraph State V1
status: draft
version: v1
owner: victus-agent-runtime
domain: agent
contract_type: runtime_schema
stability: experimental
updated_at: 2026-06-12
---
# LangGraph State V1

## 1. Purpose

Defines the minimum shared state passed between Victus LangGraph nodes.

This state is orchestration state. It is not the canonical user history.

## 2. Type

```ts
type VictusGraphStateV1 = {
  request: {
    request_id: string
    user_id: string
    original_text: string
    working_text: string
    received_at: string
    locale?: string
    timezone?: string
    conversation_id?: string
  }

  session_context: {
    conversation_id?: string
    summary?: ConversationStateSummary
    pending_interaction?: PendingInteractionState
    bootstrap?: {
      conversation_id?: string
      summary?: ConversationStateSummary
      pending_interaction?: PendingInteractionState
      recent_user_messages: string[]
      last_tool_summary?: string
      routing_query: string
    }
    updated_summary?: ConversationStateSummary
  }

  safety: {
    status: "unknown" | "ok" | "warning" | "blocked" | "needs_clarification"
    reasons: string[]
    decision?: "allow" | "route_to_safety_triage" | "emergency_escalation"
    severity?: "none" | "low" | "medium" | "high" | "critical"
    categories?: string[]
    matched_rules?: string[]
    reason_codes?: string[]
    blocked_tools?: string[]
    allowed_next_route?: "IntentRouter" | "SafetyTriageRoute" | "EmergencySupportResponse"
    audit_required?: boolean
  }

  intent: {
    primary_intent?:
      | "event_capture"
      | "profile_update"
      | "plan_intent"
      | "evidence_answer"
      | "clarification"
      | "safety"
      | "mixed"
      | "unknown"
    confidence?: number
    rationale?: string
    target_node?: string
    subintents?: string[]
  }

  projections: {
    user_profile?: UserProfileProjection
    constraint?: ConstraintProjection
    nutrition_status?: NutritionStatusProjection
    planning_history?: PlanningHistoryProjection
    loaded_at?: string
    max_event_seq?: number
  }

  tool_context: {
    allowed_tools: string[]
    proposed_action?: Record<string, unknown>
    last_tool_result?: ToolResult
    tool_results: ToolResult[]
  }

  planning: {
    session_id?: string
    revision_id?: string
    artifact_id?: string
    candidate_artifact?: Record<string, unknown>
    validation_report?: Record<string, unknown>
  }

  evidence: {
    query?: string
    retrieved_evidence?: unknown[]
    cited_evidence?: unknown[]
    generated_claims?: unknown[]
  }

  clarification: {
    clarification_id?: string
    missing_fields: string[]
    question?: string
    expected_answer_type?: string
    resume_node?: string
    resume_action?: string
  }

  response: {
    mode?: "final" | "clarification" | "blocked" | "error"
    user_message?: string
    internal_notes?: string[]
  }

  audit: {
    trace_id?: string
    node_path: string[]
    events_emitted: Array<{ event_id: string; event_type: string; seq: number }>
    warnings: string[]
    errors: string[]
    transforms?: Array<{
      step: string
      input: string
      output: string
    }>
  }
}
```

## 3. Node Ownership

- `SafetyPrecheckNode` writes `safety`.
- `ContextBootstrapNode` writes `session_context.bootstrap` and updates `request.working_text` only when pending context or translation changes the active view.
- `IntentRouterNode` writes `intent`.
- Domain nodes write `tool_context`, `planning`, `evidence`, or `clarification`.
- `ResponseComposer` writes `response`.
- `SummaryAfterResponseNode` writes `session_context.updated_summary`.
- Event-writing handlers append to `audit.events_emitted`.

## 4. Rules

- Nodes may read projections but must not mutate projection tables directly.
- Nodes may propose tool calls but backend handlers perform validation and persistence.
- The graph must preserve `request_id`, `user_id`, and `trace_id` through all nodes.
- If safety status is `blocked`, no state-writing tool may execute.
- If a node returns `needs_clarification`, route to `ClarificationNode`.
- If a tool emits events, projectors must update before final response when the response depends on current state.
- The graph must not load full conversation history by default when session context exists.
