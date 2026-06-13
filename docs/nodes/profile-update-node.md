---

## id: VICTUS-NODE-PROFILE-UPDATE  
contract_id: victus.node.profile_update  
title: Profile Update Node  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: orchestration  
contract_type: orchestration_node  
stability: experimental  
updated_at: 2026-06-12
---
# Profile Update Node

## 1. Purpose

Handles user requests that update stable or slow-changing user information.

This node manages restrictions, preferences, dislikes, likes, budget preferences, time preferences, and similar profile-level constraints. It does not log meals, create plans, revise plans, or answer scientific evidence questions.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.node.profile_update`
    
- One execution belongs to one user request or one decomposed sub-request.
    
- Node identity must not be confused with `restriction_id`, `preference_id`, or `goal_id`.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Input

```ts
type ProfileUpdateInput = {
  user_id: string
  normalized_text: string
  user_context_digest?: string
  constraint_digest?: string
}
```

## 4. Output

```ts
type ProfileUpdateOutput = {
  profile_action:
    | "add_restriction"
    | "update_restriction"
    | "update_preference"
    | "needs_clarification"
    | "reroute"

  requires_confirmation: boolean
  requires_safety_validation: boolean
  reason: string
}
```

## 5. Responsibilities

### Required Responsibilities

- Detect whether the user is declaring a restriction, updating a restriction, or changing a preference.
    
- Preserve the difference between medical restriction, allergy, intolerance, religious restriction, and preference.
    
- Request clarification when the profile update is ambiguous.
    
- Require safety validation for high-severity restrictions.
    
- Emit profile events only through validated command handlers.
    

### Forbidden Responsibilities

- Must not log meals.
    
- Must not create or revise plans.
    
- Must not change active goals.
    
- Must not downgrade safety-relevant restrictions without confirmation.
    
- Must not treat preferences as medical restrictions.
    
- Must not infer clinical status from casual language.
    

## 6. Validation Rules

- `profile_action` must be one allowed value.
    
- Restrictions must include a restricted substance or condition.
    
- Preferences must include category, item, direction, and strength when available.
    
- High-severity restrictions must require safety validation.
    
- Reducing restriction severity must require confirmation.
    
- Ambiguous restriction type must request clarification.
    

## 7. Lifecycle

### Created

Created when the router selects profile update intent.

### Updated

Node decisions are immutable.

### Superseded

May be superseded by clarification, safety triage, or mixed-intent decomposition.

## 8. Relationships

### Upstream Contracts

- `IntentRouterNode`
    
- `SafetyPreCheckNode`
    
- `UserProfile`
    
- `ConstraintProjection`
    

### Downstream Contracts

- `ClarificationNode`
    
- `SafetyTriageNode`
    
- `ResponseComposerNode`
    

### Visible Tools

- `profile.add_restriction`
    
- `profile.update_restriction`
    
- `profile.update_preference`
    
- `clarification.request`
    

### Related Events

- `restriction.added`
    
- `restriction.updated`
    
- `preference.updated`
    

## 9. Operational Notes

This node updates durable user context.

It should be conservative when the user uses medical, allergy, intolerance, or diagnosis-like language.

## 10. Versioning

### Patch

Clarifies profile update behavior.

### Minor

Adds a new profile action or preference category.

### Major

Changes the boundary between preferences, restrictions, and safety constraints.