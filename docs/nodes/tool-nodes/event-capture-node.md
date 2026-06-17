---
id: VICTUS-NODE-EVENT-CAPTURE
contract_id: victus.node.event_capture
title: Event Capture Node
status: draft
version: v1
owner: victus-agent-runtime
domain: orchestration
contract_type: orchestration_node
stability: experimental
updated_at: 2026-06-17
---
# Event Capture Node

## 1. Purpose

`EventCaptureNode` classifies fast-changing personal data reported by the user and returns a structured `EventCaptureDecision`.

It does not write directly to PostgreSQL. Command handlers consume the decision, validate command inputs, append events to `user_events`, and projectors update derived read models such as `nutrition_status_projection`.

## 2. Scope

V1 captures:

- `meal`: food, drinks, meals, snacks, meal corrections, meal deletion.
- `biometrics`: weight, blood pressure, glucose, heart rate, body measurements.
- `lifestyle_metric`: sleep, water, steps, stress, energy, hunger.
- `symptom`: pain, nausea, dizziness, physical discomfort, physical symptoms.

## 3. Non-Goals

The node must not:

- create or revise plans
- change goals
- update durable preferences or restrictions
- answer scientific questions
- calculate calories or macros
- invent quantities, nutrients, or absolute timestamps
- persist ambiguous corrections
- diagnose symptoms
- write to the database or emit events directly

## 4. Input

```ts
type EventCaptureInput = {
  user_id: string
  normalized_text: string
  active_clarification_exists?: boolean
  user_context_digest?: string | null
  nutrition_status_digest?: string | null
}
```

## 5. Output

```ts
type EventCaptureDecision = {
  capture_action:
    | "log_meal"
    | "edit_meal"
    | "delete_meal"
    | "log_biometrics"
    | "log_lifestyle_metric"
    | "log_symptom"
    | "needs_clarification"
    | "reroute"

  capture_entity_type:
    | "meal"
    | "biometrics"
    | "lifestyle_metric"
    | "symptom"
    | "unknown"

  selected_skill:
    | "nutrition.log_meal"
    | "nutrition.edit_meal"
    | "nutrition.delete_meal"
    | "biometrics.log"
    | "lifestyle.log"
    | "symptom.log"
    | "clarification.request"
    | "none"

  event_type_candidate:
    | "meal.logged"
    | "meal.edited"
    | "meal.deleted"
    | "biometrics.logged"
    | "lifestyle_metric.logged"
    | "symptom.logged"
    | "none"

  extracted: Record<string, unknown>
  referenced_record?: string | null
  occurred_at_text?: string | null
  requires_confirmation: boolean
  requires_safety_validation: boolean
  clarification_question?: string | null
  reason: string
}
```

## 6. Extraction Rules

Meal payloads require at least one explicit item name:

```json
{
  "meal": {
    "meal_type": "breakfast | lunch | dinner | snack | unknown",
    "items": [
      {
        "name": "pollo",
        "quantity_text": "200g",
        "preparation": "grilled"
      }
    ]
  }
}
```

`quantity_text` is copied only when explicitly stated. The node must not estimate calories, macros, grams, portions, or nutrients.

Biometrics require a metric and explicit value or raw value:

```json
{
  "biometrics": {
    "metric": "weight | blood_pressure | glucose | heart_rate | body_measurement",
    "value": 78.4,
    "unit": "kg",
    "raw_value_text": "78.4 kg"
  }
}
```

Blood pressure uses systolic and diastolic values when explicitly provided:

```json
{
  "biometrics": {
    "metric": "blood_pressure",
    "systolic": 125,
    "diastolic": 80,
    "unit": "mmHg",
    "raw_value_text": "125/80"
  }
}
```

Lifestyle metrics require a metric. Numeric or qualitative values are allowed when explicitly stated:

```json
{
  "lifestyle_metric": {
    "metric": "sleep_duration | water_intake | steps | stress | energy | hunger",
    "value": 5,
    "unit": "hours",
    "raw_value_text": "5 horas"
  }
}
```

Symptoms require a category or useful raw text and must not be diagnosed:

```json
{
  "symptom": {
    "category": "headache | nausea | dizziness | pain | discomfort | other",
    "severity": "mild | medium | severe | unknown",
    "body_location": "head",
    "context": "after training",
    "raw_text": "dolor de cabeza leve después de entrenar"
  }
}
```

Relative time expressions such as `today`, `yesterday`, `this morning`, `after training`, and `before sleep` are preserved in `occurred_at_text`. Absolute timestamps are assigned outside this node.

## 7. Validation Rules

- `capture_action` must match `selected_skill`.
- `capture_action` must match `event_type_candidate`.
- `log_meal` requires `extracted.meal.items` with at least one item name.
- `edit_meal` requires `referenced_record` or `clarification_question`.
- `delete_meal` requires `referenced_record` or `clarification_question`.
- `log_biometrics` requires `extracted.biometrics.metric` and `raw_value_text` or numeric value.
- `log_lifestyle_metric` requires `extracted.lifestyle_metric.metric`.
- `log_symptom` requires `extracted.symptom.raw_text` or `extracted.symptom.category`.
- `needs_clarification` requires `clarification_question`.
- `reroute` must use `selected_skill=none` and `event_type_candidate=none`.
- Extracted payloads must not contain invented calories, macros, or nutrients.
- High-risk symptom keywords force `requires_safety_validation=true`.

## 8. Visible Skills

- `nutrition.log_meal`
- `nutrition.edit_meal`
- `nutrition.delete_meal`
- `biometrics.log`
- `lifestyle.log`
- `symptom.log`
- `clarification.request`
- `none`

## 9. Related Events

- `meal.logged`
- `meal.edited`
- `meal.deleted`
- `biometrics.logged`
- `lifestyle_metric.logged`
- `symptom.logged`

## 10. Operational Notes

`node_runs` should store node input and output for observability, but this node must not know persistence details.

Command handlers are responsible for durable writes into `user_events`. Projectors are responsible for updating `nutrition_status_projection`.
