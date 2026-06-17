---

## id: VICTUS-NODE-EVENT-CAPTURE  
contract_id: victus.node.event_capture  
title: Event Capture Node  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: orchestration  
contract_type: orchestration_node  
stability: experimental  
updated_at: 2026-06-12
---
# Event Capture Node

## 1. Purpose

Handles user requests that report, correct, or delete fast-changing personal data.

This node captures meals, biometrics, symptoms, and similar user events. It does not create plans, revise goals, or answer scientific evidence questions.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.node.event_capture`
    
- One execution belongs to one user request or one decomposed sub-request.
    
- Node identity must not be confused with `meal_id`, `biometrics_id`, or `symptom_id`.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Input

```ts
type EventCaptureInput = {
  user_id: string
  normalized_text: string
  active_clarification_exists?: boolean
  user_context_digest?: string
  nutrition_status_digest?: string
}
```

## 4. Output

```ts
type EventCaptureOutput = {
  capture_action:
    | "log_meal"
    | "edit_meal"
    | "delete_meal"
    | "log_biometrics"
    | "log_symptom"
    | "needs_clarification"
    | "reroute"

  requires_confirmation: boolean
  requires_safety_validation: boolean
  reason: string
}
```

## 5. Responsibilities

### Required Responsibilities

- Identify whether the user is reporting, editing, or deleting fast-changing data.
    
- Extract only explicitly stated values.
    
- Request clarification when required quantities, dates, or references are missing.
    
- Route symptoms or risky inputs through safety validation when needed.
    
- Emit domain events only through validated command handlers.
    

### Forbidden Responsibilities

- Must not create or revise plans.
    
- Must not change goals.
    
- Must not infer unstated meal quantities.
    
- Must not invent nutrition values from incomplete input.
    
- Must not answer evidence questions.
    
- Must not persist ambiguous corrections without confirmation.
    

## 6. Validation Rules

- `capture_action` must be one allowed value.
    
- Meal logging must include at least one food item.
    
- Meal editing or deletion must reference an existing meal or request clarification.
    
- Biometrics must use reasonable value ranges.
    
- Symptoms must include category, severity, or enough context to ask a useful clarification.
    
- High-risk symptoms must require safety validation.
    

## 7. Lifecycle

### Created

Created when the router selects fast data capture.

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
    
- `NutritionStatus`
    

### Downstream Contracts

- `ClarificationNode`
    
- `SafetyTriageNode`
    
- `ResponseComposerNode`
    

### Visible Tools

- `nutrition.log_meal`
    
- `nutrition.edit_meal`
    
- `nutrition.delete_meal`
    
- `biometrics.log`
    
- `symptom.log`
    
- `clarification.request`
    

### Related Events

- `meal.logged`
    
- `meal.edited`
    
- `meal.deleted`
    
- `biometrics.logged`
    
- `symptom.logged`
    

## 9. Operational Notes

This node should be conservative.

When the user gives partial information, the node should either save only explicit facts or ask for clarification.

## 10. Versioning

### Patch

Clarifies capture behavior.

### Minor

Adds a new capture action or visible tool.

### Major

Changes what counts as user-recorded data or changes write behavior.