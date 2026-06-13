---
id: VICTUS-CONTRACT-PROJECTIONS-V1
contract_id: victus.contract.projections.v1
title: Projections V1
status: draft
version: v1
owner: victus-agent-runtime
domain: projections
contract_type: read_model_schema
stability: experimental
updated_at: 2026-06-12
---
# Projections V1

## 1. Purpose

Defines the read models required by the V1 agent runtime.

Projections are mutable and rebuildable. They exist to make planning and routing fast. They are not historical truth.

## 2. UserProfileProjection

```ts
type UserProfileProjection = {
  user_id: string
  profile: {
    display_name?: string
    locale?: string
    timezone?: string
    age_range?: string
    sex_label?: string
    activity_context?: string
  }
  restrictions: RestrictionView[]
  preferences: PreferenceView[]
  active_goal_id?: string
  last_event_seq: number
  updated_at: string
}
```

Builds from:

- `restriction.added`
- `restriction.updated`
- `preference.updated`
- `goal.set`
- `goal.adjusted`

## 3. ConstraintProjection

```ts
type ConstraintProjection = {
  user_id: string
  hard_constraints: Array<{
    constraint_id: string
    kind: "allergy" | "medical" | "religious" | "safety" | "system"
    label: string
    severity: "low" | "medium" | "high" | "unknown"
    rule: Record<string, unknown>
  }>
  soft_constraints: Array<{
    constraint_id: string
    kind: "preference" | "budget" | "schedule" | "adherence" | "cooking"
    label: string
    strength: number
    rule: Record<string, unknown>
  }>
  safety_flags: Array<{
    flag_id: string
    risk_category: string
    status: "warning" | "blocked" | "needs_clarification"
    reasons: string[]
  }>
  derived_from_event_seq: number
  updated_at: string
}
```

Builds from:

- restrictions
- preferences
- symptom safety events
- safety guard events
- goal safety checks

## 4. NutritionStatusProjection

```ts
type NutritionStatusProjection = {
  user_id: string
  recent_meals: Array<{
    meal_id: string
    meal_type: string
    consumed_at: string
    items: Array<{ item_id: string; food_label: string; quantity?: unknown }>
    status: "active" | "deleted"
  }>
  biometrics: {
    latest_weight?: { value: number; unit: string; measured_at: string }
    latest_height?: { value: number; unit: string; measured_at: string }
    sleep?: unknown
    steps?: unknown
  }
  symptoms: Array<{
    symptom_id: string
    label: string
    severity?: string
    occurred_at: string
  }>
  computed_metrics: {
    meal_count_7d?: number
    adherence_rate_7d?: number
    adherence_rate_30d?: number
    weekend_drop_delta?: number
    late_meal_frequency?: number
    consistency_score?: number
    trigger_pattern_score?: number
  }
  last_event_seq: number
  updated_at: string
}
```

Builds from:

- `meal.logged`
- `meal.edited`
- `meal.deleted`
- `biometrics.logged`
- `symptom.logged`
- future weekly summary events

## 5. PlanningHistoryProjection

```ts
type PlanningHistoryProjection = {
  user_id: string
  active_session_id?: string
  active_plan_artifact_id?: string
  active_goal_id?: string
  revision_summary: Array<{
    revision_id: string
    session_id: string
    created_at: string
    summary?: string
  }>
  feedback_summary: Array<{
    feedback_id: string
    target_type: string
    target_id?: string
    sentiment?: string
    resolved?: boolean
  }>
  last_event_seq: number
  updated_at: string
}
```

Builds from:

- `goal.set`
- `goal.adjusted`
- `plan.session_started`
- `plan.revision_created`
- `plan.artifact_saved`
- `plan.session_ended`
- `planning.artifact_accepted`
- `planning.artifact_rejected`
- `feedback.recorded`
- `feedback.resolved`

## 6. Projector Rules

- Projectors must be idempotent.
- Projectors must process events in `event_seq` order.
- Projectors must record their offset in `projector_offsets`.
- Projectors must be replayable from zero.
- Projection state may be denormalized for speed.
- Projection state must never be edited directly by the LLM.
