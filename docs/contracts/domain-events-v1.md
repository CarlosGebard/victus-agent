---
id: VICTUS-CONTRACT-DOMAIN-EVENTS-V1
contract_id: victus.contract.events.domain_events.v1
title: Domain Events V1
status: draft
version: v1
owner: victus-agent-runtime
domain: events
contract_type: schema
stability: experimental
updated_at: 2026-06-12
---
# Domain Events V1

## 1. Purpose

Defines the initial domain event payloads required for the Victus Agent V1.

These events are intentionally minimal. They are sufficient for a first event store, projector layer, and LangGraph runtime.

## 2. Nutrition Events

### meal.logged

```ts
type MealLoggedPayload = {
  meal_id: string
  meal_type: "breakfast" | "lunch" | "dinner" | "snack" | "unknown"
  consumed_at: string
  source: "manual" | "voice" | "import"
  items: Array<{
    item_id: string
    food_label: string
    quantity?: {
      value: number
      unit: "g" | "ml" | "unit" | "serving" | "cup" | "tbsp" | "tsp" | "unknown"
    }
    notes?: string
  }>
  notes?: string
}
```

### meal.edited

```ts
type MealEditedPayload = {
  meal_id: string
  reason?: string
  patch: {
    meal_type?: string
    consumed_at?: string
    items_added?: unknown[]
    items_updated?: unknown[]
    items_removed?: string[]
    notes?: string
  }
}
```

### meal.deleted

```ts
type MealDeletedPayload = {
  meal_id: string
  reason?: string
  user_confirmed: true
}
```

## 3. Biometrics and Symptoms

### biometrics.logged

```ts
type BiometricsLoggedPayload = {
  measurement_id: string
  measured_at: string
  measurements: Array<{
    type: "weight" | "height" | "sleep" | "steps" | "body_fat" | "waist" | "other"
    value: number
    unit: string
  }>
  source: "manual" | "wearable" | "import"
}
```

### lifestyle_metric.logged

```ts
type LifestyleMetricLoggedPayload = {
  metric_id: string
  occurred_at: string
  metric: "sleep_duration" | "water_intake" | "steps" | "stress" | "energy" | "hunger"
  value?: number | string
  unit?: string
  raw_value_text?: string
  source: "manual" | "wearable" | "import"
}
```

### symptom.logged

```ts
type SymptomLoggedPayload = {
  symptom_id: string
  occurred_at: string
  label: string
  severity?: "low" | "medium" | "high" | "unknown"
  duration?: string
  notes?: string
  safety_checked: boolean
}
```

## 4. Profile and Constraint Events

### restriction.added

```ts
type RestrictionAddedPayload = {
  restriction_id: string
  restriction_kind: "medical" | "religious" | "allergy" | "intolerance" | "advisory" | "unknown"
  condition_label?: string
  restricted_substance_label: string
  severity: "low" | "medium" | "high" | "unknown"
  scope: "absolute" | "dietary" | "advisory" | "unknown"
  evidence_level: "declared" | "clinical" | "unknown"
}
```

### restriction.updated

```ts
type RestrictionUpdatedPayload = {
  restriction_id: string
  patch: Record<string, unknown>
  reason?: string
}
```

### preference.updated

```ts
type PreferenceUpdatedPayload = {
  preference_id: string
  category: "food" | "cuisine" | "budget" | "time" | "schedule" | "cooking" | "other"
  item_label: string
  preference: "like" | "neutral" | "dislike"
  strength: number
  reason?: string
}
```

## 5. Goal and Planning Events

### goal.set

```ts
type GoalSetPayload = {
  goal_id: string
  primary_goal: "cut" | "maintain" | "bulk" | "performance" | "health" | "unknown"
  horizon_weeks?: number
  energy_target?: {
    type: "delta_daily" | "target_daily" | "unknown"
    kcal_per_day?: number
  }
  macro_targets?: Record<string, unknown>
  user_confirmed?: boolean
}
```

### goal.adjusted

```ts
type GoalAdjustedPayload = {
  goal_id: string
  patch: Record<string, unknown>
  reason?: string
  user_confirmed?: boolean
}
```

### plan.session_started

```ts
type PlanSessionStartedPayload = {
  session_id: string
  reason: string
  goal_id?: string
  active_plan_id?: string
}
```

### plan.revision_created

```ts
type PlanRevisionCreatedPayload = {
  revision_id: string
  session_id: string
  parent_revision_id?: string
  objectives: Array<{ type: string; direction: string; priority: number }>
  summary?: string
}
```

### plan.artifact_saved

```ts
type PlanArtifactSavedPayload = {
  artifact_id: string
  session_id: string
  revision_id: string
  artifact_type: "diet_recommendation" | "meal_adjustment" | "weekly_review" | "general_guidance"
  artifact: Record<string, unknown>
  validation: {
    schema_valid: boolean
    policy_valid: boolean
    safety_status: "ok" | "warning" | "blocked"
    warnings: string[]
  }
}
```

### plan.session_ended

```ts
type PlanSessionEndedPayload = {
  session_id: string
  status: "completed" | "abandoned" | "canceled" | "error"
  reason?: string
}
```

## 6. Feedback, Clarification, Safety, and Evidence

### feedback.recorded

```ts
type FeedbackRecordedPayload = {
  feedback_id: string
  target_type: "plan" | "meal" | "recommendation" | "answer" | "other"
  target_id?: string
  sentiment?: "positive" | "neutral" | "negative" | "mixed"
  text: string
}
```

### feedback.resolved

```ts
type FeedbackResolvedPayload = {
  feedback_id: string
  resolution: "accepted" | "rejected" | "incorporated" | "needs_more_info"
  linked_revision_id?: string
}
```

### clarification.requested

```ts
type ClarificationRequestedPayload = {
  clarification_id: string
  blocked_node?: string
  blocked_action?: string
  missing_fields: string[]
  question: string
  expected_answer_type: string
}
```

### clarification.resolved

```ts
type ClarificationResolvedPayload = {
  clarification_id: string
  answer: string
  resume_node?: string
  resume_action?: string
}
```

### safety.guard_triggered

```ts
type SafetyGuardTriggeredPayload = {
  risk_category: string
  safety_status: "warning" | "blocked" | "needs_clarification"
  reasons: string[]
  checked_action?: Record<string, unknown>
}
```

### safety.action_blocked

```ts
type SafetyActionBlockedPayload = {
  risk_category: string
  reasons: string[]
  blocked_action: Record<string, unknown>
}
```

### claim.generated

```ts
type ClaimGeneratedPayload = {
  claim_id: string
  text: string
  claim_type: "plan_rationale" | "evidence_answer" | "safety_explanation" | "general"
  grounded: boolean
}
```

### evidence.cited

```ts
type EvidenceCitedPayload = {
  citation_id: string
  claim_id?: string
  evidence_id: string
  source_type: "paper" | "guideline" | "curated_note" | "external"
  citation_text?: string
  relevance_score?: number
}
```
