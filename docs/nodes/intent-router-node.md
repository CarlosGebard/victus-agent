---
## id: VICTUS-NODE-INTENT-ROUTER  
contract_id: victus.node.intent_router  
title: Intent Router Node  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: orchestration  
contract_type: orchestration_node  
stability: experimental  
updated_at: 2026-06-12
---
# Intent Router Node

## 1. Purpose

Routes a normalized user request to the correct semantic node.

This node decides the user’s main operational intent. It does not execute tools, persist events, generate plans, answer evidence questions, or modify user state.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.node.intent_router`
    
- One router decision is produced per user request.
    
- Router identity must not be derived from the selected downstream node.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Input

```ts
type IntentRouterInput = {
  user_id: string
  conversation_id: string
  normalized_text: string
  session_state?: object
  active_plan_exists?: boolean
  active_clarification_exists?: boolean
}
```

## 4. Output

```ts
type IntentRouterOutput = {
  selected_node:
    | "safety_precheck"
    | "plan_intent"
    | "event_capture"
    | "evidence_answer"
    | "weekly_review"
    | "profile_update"
    | "mixed_intent"
    | "clarification"

  intent_confidence: number
  reason: string
}
```

## 5. Responsibilities

### Required Responsibilities

- Classify the request into one semantic execution path.
    
- Prefer safety routing when risk is present.
    
- Prefer clarification when intent confidence is low.
    
- Route mixed requests to `MixedIntentNode`.
    
- Keep downstream tool space small.
    

### Forbidden Responsibilities

- Must not call user-facing tools.
    
- Must not write events.
    
- Must not update projections.
    
- Must not generate final responses.
    
- Must not decide final safety outcomes.
    

## 6. Validation Rules

- `selected_node` must be one allowed node value.
    
- `intent_confidence` must be between `0` and `1`.
    
- Low-confidence routing must select `clarification` or `mixed_intent`.
    
- Safety-sensitive inputs must not bypass `SafetyPreCheckNode`.
    

## 7. Lifecycle

### Created

Created for each normalized user request.

### Updated

Router decisions are immutable after produced.

### Superseded

A router decision may be superseded by a later router decision if clarification changes the user intent.

## 8. Relationships

### Upstream Contracts

- `NormalizeInputNode`
    
- Conversation state
    
- Active session state
    

### Downstream Contracts

- `SafetyPreCheckNode`
    
- `PlanIntentNode`
    
- `EventCaptureNode`
    
- `EvidenceAnswerNode`
    
- `WeeklyReviewNode`
    
- `ProfileUpdateNode`
    
- `MixedIntentNode`
    
- `ClarificationNode`
    

## 9. Operational Notes

This node should be implemented with a hybrid strategy:

1. deterministic safety and session rules
    
2. embedding router for semantic intent
    
3. LLM router only when ambiguous
    

The model should not receive the full tool catalog at this stage.

## 10. Versioning

### Patch

Clarifies routing descriptions without changing behavior.

### Minor

Adds a new allowed downstream node.

### Major

Changes routing semantics, confidence policy, or node responsibility boundaries.