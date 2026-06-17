---
## id: VICTUS-NODE-PLAN-INTENT  
contract_id: victus.node.plan_intent  
title: Plan Intent Node  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: orchestration  
contract_type: orchestration_node  
stability: experimental  
updated_at: 2026-06-12
---
# Plan Intent Node

## 1. Purpose

Handles user requests that involve goals, new plans, or revisions to an existing plan.

This node groups goal management and planning because both represent changes to the user’s intended direction or execution strategy.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.node.plan_intent`
    
- One plan intent execution belongs to one user request.
    
- Plan intent identity must not be confused with `goal_id`, `session_id`, `revision_id`, or `artifact_id`.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Input

```ts
type PlanIntentInput = {
  user_id: string
  normalized_text: string
  active_plan_exists: boolean
  active_goal_exists: boolean
  user_context_digest?: string
  planning_context_digest?: string
}
```

## 4. Output

```ts
type PlanIntentOutput = {
  plan_action:
    | "goal_only"
    | "new_plan"
    | "revise_plan"
    | "needs_clarification"

  requires_evidence: boolean
  requires_safety_validation: boolean
  reason: string
}
```

## 5. Responsibilities

### Required Responsibilities

- Decide whether the user wants only a goal change, a new plan, or a revision.
    
- Load only the context required for the selected plan action.
    
- Keep goal changes separate from plan artifact creation.
    
- Use the active plan when the user is modifying current recommendations.
    
- Request clarification when the user intent cannot be safely executed.
    

### Forbidden Responsibilities

- Must not treat every goal change as a full plan request.
    
- Must not create a plan artifact without a planning session.
    
- Must not revise a plan without a target revision or active plan.
    
- Must not bypass constraints or safety validation.
    
- Must not search scientific evidence unless needed for justification or uncertainty.
    

## 6. Validation Rules

- `plan_action` must be one allowed value.
    
- `new_plan` must create or use a planning session.
    
- `revise_plan` must reference an active plan, revision, or user feedback.
    
- `goal_only` may emit goal events without creating a plan artifact.
    
- Unsafe or aggressive goals must require safety validation.
    

## 7. Lifecycle

### Created

Created when the router selects planning intent.

### Updated

Node decisions are immutable.

### Superseded

A decision may be superseded after clarification or safety triage.

## 8. Relationships

### Upstream Contracts

- `IntentRouterNode`
    
- `SafetyPreCheckNode`
    
- `UserProfile`
    
- `ConstraintProjection`
    
- `NutritionStatus`
    
- `PlanningHistory`
    

### Downstream Contracts

- `GoalOnlyAction`
    
- `NewPlanAction`
    
- `RevisePlanAction`
    
- `ClarificationNode`
    
- `SafetyTriageNode`
    

### Related Events

- `goal.set`
    
- `goal.adjusted`
    
- `plan.session_started`
    
- `plan.revision_created`
    
- `plan.artifact_saved`
    
- `user.feedback`
    
- `feedback.resolved`
    
- `claim.generated`
    
- `evidence.cited`
    

## 9. Operational Notes

This node is the main planning boundary.

The model may help interpret the user request, but command handlers must validate goals, constraints, safety, and plan changes before events are emitted.

## 10. Versioning

### Patch

Clarifies plan action descriptions.

### Minor

Adds a new plan action.

### Major

Splits goal and planning into separate nodes or changes event ownership.