---
id: VICTUS-TOOL-DIET-GENERATE-RECOMMENDATION
contract_id: victus.tool.diet.generate_recommendation
title: Diet Generate Recommendation Tool
status: draft
version: v1
owner: victus-agent-runtime
domain: diet
contract_type: tool_schema
stability: experimental
updated_at: 2026-06-12
---
# Diet Generate Recommendation Tool

## 1. Purpose

Generates a diet recommendation candidate from the current user context, constraints, nutrition status, active goal, and planning intent. This tool produces a candidate recommendation artifact. It does not persist the artifact, mark it as accepted, update goals, or record evidence links by itself.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.diet.generate_recommendation`
- Runtime name: `diet.generate_recommendation`
- Tool identity must not be derived from emitted event names, runtime traces, display labels, or implementation files.

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

| Field | Value |
|---|---|
| Exposed to model | `true` |
| Visible in nodes | `PlanIntentNode` |
| Tool type | `compute` |
| Requires confirmation | `never` |
| Safety class | `planning_compute` |

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "recommendation_type": {
      "type": "string",
      "enum": [
        "full_plan",
        "meal_adjustment",
        "macro_adjustment",
        "food_swap",
        "schedule_adjustment",
        "general_guidance"
      ]
    },
    "goal_id": {
      "type": "string"
    },
    "active_plan_id": {
      "type": "string"
    },
    "revision_id": {
      "type": "string"
    },
    "planning_intent": {
      "type": "string"
    },
    "objectives": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "enum": [
              "kcal",
              "protein",
              "cost",
              "time",
              "adherence",
              "preference_fit",
              "performance",
              "safety"
            ]
          },
          "direction": {
            "type": "string",
            "enum": [
              "down",
              "up",
              "maintain",
              "optimize"
            ]
          },
          "priority": {
            "type": "integer",
            "minimum": 1
          }
        },
        "required": [
          "type",
          "direction",
          "priority"
        ]
      }
    },
    "constraints_digest": {
      "type": "string"
    },
    "user_profile_digest": {
      "type": "string"
    },
    "nutrition_status_digest": {
      "type": "string"
    },
    "evidence_bundle_id": {
      "type": "string"
    },
    "reason": {
      "type": "string"
    }
  },
  "required": [
    "recommendation_type",
    "planning_intent"
  ]
}
```

## 5. Output Schema

```json
{
  "status": "success | needs_clarification | blocked | rejected | error",
  "data": {
    "candidate_artifact": {
      "targets": {},
      "structure": {},
      "warnings": [],
      "scores": {},
      "assumptions": []
    },
    "requires_safety_validation": true,
    "requires_persistence": true
  },
  "events_emitted": [],
  "warnings": [],
  "clarification": null,
  "safety": {
    "status": "ok | warning | blocked",
    "reasons": []
  },
  "meta": {
    "confidence": 0.0,
    "planner_version": 1
  }
}
```

## 6. Field Definitions

| Field | Type | Description |
|---|---|---|
| `recommendation_type` | string | Kind of recommendation to generate. |
| `goal_id` | string | Goal used as planning direction when known. |
| `active_plan_id` | string | Active plan to revise when applicable. |
| `revision_id` | string | Planning revision context when applicable. |
| `planning_intent` | string | Natural-language or normalized planning request. |
| `objectives` | array | Ordered optimization objectives. |
| `constraints_digest` | string | Digest of constraints used for generation. |
| `user_profile_digest` | string | Digest of profile state used for generation. |
| `nutrition_status_digest` | string | Digest of status state used for generation. |
| `evidence_bundle_id` | string | Evidence bundle used as support when available. |
| `reason` | string | Reason for generating the recommendation. |

## 7. Responsibilities

### Required Responsibilities

- Generate a candidate diet recommendation artifact.
- Use current context digests as generation inputs.
- Respect hard constraints and known preferences.
- Return warnings and assumptions explicitly.
- Return scores useful for later plan selection or review.
- Leave persistence to `planning.manage_session`.

### Forbidden Responsibilities

- Must not persist plan artifacts.
- Must not mark recommendations as accepted.
- Must not update goals.
- Must not log meals.
- Must not override hard restrictions.
- Must not cite evidence unless an evidence bundle is provided or attached later.
- Must not hide assumptions inside free text only.

## 8. Validation Rules

- `recommendation_type` must be one allowed value.
- `planning_intent` must not be empty.
- Objectives must have unique priorities when provided.
- Hard constraints must be represented in the generated warnings or satisfied by the candidate.
- Candidate output must include `targets`, `structure`, `warnings`, and `scores`.
- Unsafe or aggressive candidates must return `blocked` or require safety validation before persistence.

## 9. Runtime Behavior

### Reads

- `UserProfile`
- `ConstraintProjection`
- `NutritionStatus`
- `PlanningHistory`
- `ActivePlan`
- `EvidenceBundle when provided`

### May Emit Events

- `None`

### Updates Projections

- `None`

### Internal Validators

- `constraint_fit_validation`
- `macro_target_validation`
- `calorie_target_validation`
- `preference_fit_validation`
- `artifact_shape_validation`
- `safety_plan_policy`

## 10. Failure Modes

| Failure | Meaning |
|---|---|
| `needs_clarification` | Required information is missing, ambiguous, or cannot be resolved safely. |
| `blocked` | The operation is unsafe or violates a safety/constraint policy. |
| `rejected` | The payload is validly parsed but cannot be applied. |
| `error` | Unexpected runtime or infrastructure failure. |

## 11. Relationships

### Upstream Nodes

- `PlanIntentNode`
- `SafetyPreCheckNode`

### Downstream Contracts

- `planning.manage_session`
- `SafetyTriageNode`
- `EvidenceSupport`

### Related Events

- `None`

### Related Projections

- `None`

## 12. Operational Notes

This is the missing generation boundary. It creates the candidate recommendation, while `planning.manage_session` persists it as `plan.artifact_saved` only after validation.

## 13. Versioning

### Patch

Clarifies documentation without changing runtime behavior.

### Minor

Adds optional input fields, optional output fields, or compatible validation behavior.

### Major

Changes required inputs, tool meaning, emitted events, safety behavior, or output semantics.
