---

## id: VICTUS-NODE-CLARIFICATION  
contract_id: victus.node.clarification  
title: Clarification Node  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: orchestration  
contract_type: orchestration_node  
stability: experimental  
updated_at: 2026-06-12
---
# Clarification Node

## 1. Purpose

Handles requests that cannot be safely or correctly executed because required information is missing, ambiguous, or contradictory.

This node asks the user for the minimum information needed to continue. It does not execute domain actions by itself.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.node.clarification`
    
- One clarification belongs to one unresolved user request or sub-request.
    
- A clarification must reference the blocked action when available.
    
- Node identity must not be confused with the final resolved action.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Input

```ts
type ClarificationInput = {
  user_id: string
  normalized_text: string
  blocked_node?: string
  blocked_action?: string
  missing_fields: string[]
  ambiguity_reason: string
}
```

## 4. Output

```ts
type ClarificationOutput = {
  clarification_question: string
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

## 5. Responsibilities

### Required Responsibilities

- Ask only for information required to continue.
    
- Preserve the blocked node and blocked action.
    
- Avoid asking broad or unnecessary questions.
    
- Resume the original route after clarification is resolved.
    
- Prefer confirmation when the model inferred something uncertain.
    

### Forbidden Responsibilities

- Must not execute the blocked action.
    
- Must not change state.
    
- Must not ask for unrelated profile information.
    
- Must not force clarification when safe partial execution is possible.
    
- Must not expose internal routing details to the user.
    

## 6. Validation Rules

- `missing_fields` must not be empty.
    
- `clarification_question` must be specific.
    
- `expected_answer_type` must be one allowed value.
    
- `resume_node` must be an allowed semantic node when provided.
    
- Clarification must not request more information than needed for the blocked action.
    

## 7. Lifecycle

### Created

Created when a node cannot continue due to missing, ambiguous, or unsafe information.

### Updated

Clarification state may be updated when the user answers partially.

### Resolved

Resolved when the user provides enough information to resume execution.

### Superseded

May be superseded if the user changes intent.

## 8. Relationships

### Upstream Contracts

- `IntentRouterNode`
    
- `EventCaptureNode`
    
- `ProfileUpdateNode`
    
- `PlanIntentNode`
    
- `EvidenceAnswerNode`
    
- `MixedIntentNode`
    
- `SafetyPreCheckNode`
    

### Downstream Contracts

- Original blocked node
    
- `ResponseComposerNode`
    

### Visible Tools

- None by default.
    

### Internal Tools

- `clarification.request`
    
- `clarification.resolve`
    

### Related Events

- `clarification.requested`
    
- `clarification.resolved`
    

## 9. Operational Notes

This node should minimize friction.

A good clarification asks one precise question and keeps enough state to continue without restarting the flow.

## 10. Versioning

### Patch

Clarifies wording or expected answer types.

### Minor

Adds a new expected answer type.

### Major

Changes clarification lifecycle or resume semantics.