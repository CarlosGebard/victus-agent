# Implemented Projections

## Projection Model

A projection is a rebuildable view of a user's current state, derived from immutable domain events.
Events remain the source of truth; projections exist to provide fast, focused reads without replaying
the complete event history.

The projection registry maps each relevant event type to a projector. A projector applies the event
to the current view and produces its next state.

Canonical registry: `src/domain/projections/registry.py`

## How Projections Work in the Agent

At the beginning of a turn, the agent loads every available projection for the authenticated user.
These views become bounded context for the model when it decides whether to answer directly or use a
tool.

When a tool emits an event, the event is persisted first. Every projection interested in that event
is then updated in the same database transaction. A projection can also be rebuilt from the event
history if its stored state is missing or needs to be regenerated.

Agent loader: `src/adapters/langgraph/capabilities/projections.py`

Transactional update: `src/bootstrap/runtime.py`

Rebuild process: `src/victus_platform/repositories/rebuild.py`

Persistence: `src/victus_platform/repositories/projections.py`

## Projections

- `user_profile` — Current profile details, restrictions, preferences, and active goal.
  Model: `src/domain/projections/models/user_profile.py`
  Projector: `src/domain/projections/projectors/user_profile.py`
- `nutrition_status` — Recent meals, latest biometrics, lifestyle metrics, symptoms, and computed
  nutrition indicators.
  Model: `src/domain/projections/models/nutrition_status.py`
  Projector: `src/domain/projections/projectors/nutrition_status.py`
- `constraint` — Hard constraints, soft constraints, and active safety flags used to bound decisions.
  Model: `src/domain/projections/models/constraint.py`
  Projector: `src/domain/projections/projectors/constraint.py`
- `planning_history` — Active planning state, goals, revisions, saved artifacts, and feedback history.
  Model: `src/domain/projections/models/planning_history.py`
  Projector: `src/domain/projections/projectors/planning_history.py`

## Projection Contracts

Projection models reject unknown fields. They are mutable read views, not historical records, and
their event sequence identifies the newest event included in the view.

### User Profile

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
  restrictions: Array<{
    restriction_id: string
    kind: string
    label: string
    severity: "low" | "medium" | "high" | "unknown"
    metadata: Record<string, unknown>
  }>
  preferences: Array<{
    preference_id: string
    category: string
    item_label: string
    preference: "like" | "neutral" | "dislike"
    strength: number
  }>
  active_goal_id?: string
  last_event_seq: number
  updated_at: string
}
```

### Nutrition Status

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

### Constraint

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

### Planning History

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

Rules:

- Projections are keyed by authenticated `user_id`.
- Projectors consume events in `event_seq` order.
- Replaying the same ordered history must reproduce the same view.
- Projection persistence must not redefine event meaning.
- Missing projections may be rebuilt from immutable events.
