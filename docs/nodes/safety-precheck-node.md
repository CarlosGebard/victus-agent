---
## id: VICTUS-NODE-SAFETY-PRECHECK  
contract_id: victus.node.safety_precheck  
title: Safety Precheck Node  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: orchestration  
contract_type: orchestration_node  
stability: experimental  
updated_at: 2026-06-12
---
# Safety Precheck Node

## 1. Purpose

Detects whether a user request contains medical, nutritional, behavioral, or safety risk before normal execution.

This node protects the system from unsafe plan changes, dangerous recommendations, and risky symptom handling.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.node.safety_precheck`
    
- One safety precheck may be produced per user request.
    
- Safety identity must not be derived from the final answer or downstream tool result.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Input

```ts
type SafetyPrecheckInput = {
  user_id: string
  original_text: string
  working_text: string
  selected_intent?: string
  user_context_digest?: string
  active_constraints?: object
}
```

## 4. Output

```ts
type SafetyPrecheckOutput = {
  decision: "allow" | "route_to_safety_triage" | "emergency_escalation"
  severity: "none" | "low" | "medium" | "high" | "critical"
  categories: Array<"self_harm" | "none">
  matched_rules: string[]
  reason_codes: string[]
  blocked_tools: string[]
  allowed_next_route: "IntentRouter" | "SafetyTriageRoute" | "EmergencySupportResponse"
  audit_required: boolean
}
```

## 5. Responsibilities

### Required Responsibilities

- Detect V1 self-harm requests before tool execution using declarative rules.
    
- Block unsafe actions when policy requires it.
    
- Route uncertain safety cases to clarification.
    
- Preserve matched rule IDs and reason codes for traceability.
    
- Trigger safety-related events only through internal handlers.
    

### Forbidden Responsibilities

- Must not generate medical diagnosis.
    
- Must not directly create or revise plans.
    
- Must not directly modify goals.
    
- Must not directly log symptoms unless delegated to the correct command.
    
- Must not expose dangerous reasoning to the user.
    

## 6. Validation Rules

- `safety_status` must be one allowed value.
    
- `blocked` must include a reason.
    
- `needs_clarification` must include the missing safety information.
    
- Safety-sensitive plan changes must not continue without validation.
    

## 7. Lifecycle

### Created

Created after intent routing or before intent routing when obvious risk exists.

### Updated

Safety precheck outputs are immutable.

### Superseded

A new safety precheck may supersede the previous one after clarification.

## 8. Relationships

### Upstream Contracts

- `IntentRouterNode`
    
- `ConstraintProjection`
    
- `UserProfile`
    
- `NutritionStatus`
    

### Downstream Contracts

- `SafetyTriageNode`
    
- `ClarificationNode`
    
- Selected semantic node when safety status is `ok`
    

### Related Events

- `safety.guard_triggered`
    
- `safety.action_blocked`
    
- `symptom.logged`
    

## 9. Operational Notes

This node should prefer deterministic rules over LLM judgment.

The LLM should not receive broad write tools until safety precheck has passed.

## 10. Versioning

### Patch

Clarifies wording or risk descriptions.

### Minor

Adds a new risk category.

### Major

Changes blocking behavior, safety status meaning, or downstream routing policy.
