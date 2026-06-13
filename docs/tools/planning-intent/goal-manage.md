---

## id: VICTUS-TOOL-GOAL-MANAGE  
contract_id: victus.tool.goal.manage  
title: Goal Manage Tool  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: goal  
contract_type: tool_schema  
stability: experimental  
updated_at: 2026-06-12
---
# Goal Manage Tool

## 1. Purpose

Manages the user’s active goal.

This tool sets or adjusts the user’s abstract objective, energy target, horizon, and macro targets. It does not create meal plans, save plan artifacts, log meals, or answer evidence questions.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.goal.manage`
    
- Runtime name: `goal.manage`
    
- Tool identity must not be derived from `goal_id`, goal labels, or emitted event names.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

|Field|Value|
|---|---|
|Exposed to model|`true`|
|Visible in nodes|`PlanIntentNode`|
|Tool type|`command`|
|Requires confirmation|`on_aggressive_or_safety_relevant_change`|
|Safety class|`planning_state_write`|

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["set", "adjust"]
    },
    "goal_id": {
      "type": "string"
    },
    "primary_goal": {
      "type": "string",
      "enum": ["cut", "maintain", "bulk", "performance", "health", "unknown"]
    },
    "horizon_weeks": {
      "type": "integer",
      "minimum": 1
    },
    "energy_target": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": ["delta_daily", "target_daily", "unknown"]
        },
        "kcal_per_day": {
          "type": "number"
        }
      }
    },
    "macro_targets": {
      "type": "object",
      "properties": {
        "protein_g_per_day": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "enum": ["min", "target", "range"]
            },
            "value": {
              "type": "number"
            },
            "min": {
              "type": "number"
            },
            "max": {
              "type": "number"
            }
          }
        },
        "carbs_g_per_day": {
          "type": "object"
        },
        "fat_g_per_day": {
          "type": "object"
        }
      }
    },
    "reason": {
      "type": "string"
    },
    "user_confirmed": {
      "type": "boolean"
    }
  },
  "required": ["operation"]
}
```

## 5. Output Schema

```json
{
  "status": "success | needs_clarification | blocked | rejected | error",
  "data": {
    "goal_id": "uuid?"
  },
  "events_emitted": [
    {
      "event_type": "goal.set | goal.adjusted",
      "event_id": "uuid",
      "seq": 0
    }
  ],
  "warnings": [],
  "clarification": null,
  "safety": {
    "status": "ok | warning | blocked",
    "reasons": []
  },
  "meta": {
    "confidence": 0.0
  }
}
```

## 6. Field Definitions

|Field|Type|Description|
|---|---|---|
|`operation`|string|Whether the user is setting a new goal or adjusting an existing one.|
|`goal_id`|string|Stable identifier of the goal when adjusting a known goal.|
|`primary_goal`|string|Main user objective.|
|`horizon_weeks`|integer|Intended goal duration.|
|`energy_target`|object|Daily energy target or daily energy delta.|
|`macro_targets`|object|Protein, carbohydrate, and fat targets.|
|`reason`|string|Reason for the goal change.|
|`user_confirmed`|boolean|Confirmation for aggressive or safety-relevant changes.|

## 7. Responsibilities

### Required Responsibilities

- Set a new active goal when `operation = set`.
    
- Adjust an existing goal when `operation = adjust`.
    
- Preserve explicit goal targets and reasoning.
    
- Request clarification when the user intent is goal-like but underspecified.
    
- Trigger safety validation for aggressive or risky targets.
    
- Delegate event emission to backend command handlers.
    

### Forbidden Responsibilities

- Must not create plan artifacts.
    
- Must not revise meal structure.
    
- Must not log meals.
    
- Must not answer evidence questions.
    
- Must not infer aggressive targets without confirmation.
    
- Must not bypass safety constraints.
    

## 8. Validation Rules

- `operation` must be one allowed value.
    
- `set` must include enough information to create a meaningful active goal.
    
- `adjust` must reference an active goal or resolvable goal context.
    
- `horizon_weeks` must be greater than `0` when provided.
    
- Aggressive energy targets must require safety validation.
    
- Missing target details must return `needs_clarification` when required for execution.
    

## 9. Runtime Behavior

### Reads

- `UserProfile`
    
- `ConstraintProjection`
    
- `NutritionStatus`
    
- `PlanningHistory`
    

### May Emit Events

- `goal.set`
    
- `goal.adjusted`
    

### Updates Projections

- `UserProfile`
    
- `ConstraintProjection`
    
- `PlanningHistory`
    

### Internal Validators

- `goal_target_validation`
    
- `macro_target_validation`
    
- `energy_target_validation`
    
- `safety_goal_policy`
    
- `active_goal_resolution`
    

## 10. Failure Modes

|Failure|Meaning|
|---|---|
|`needs_clarification`|Goal, target, horizon, or reason is missing or ambiguous.|
|`blocked`|Requested goal violates safety policy.|
|`rejected`|Goal cannot be applied because the payload is invalid.|
|`error`|Unexpected runtime failure.|

## 11. Relationships

### Upstream Nodes

- `PlanIntentNode`
    
- `SafetyPreCheckNode`
    

### Downstream Contracts

- `DomainEventStore`
    
- `UserProfile`
    
- `ConstraintProjection`
    
- `PlanningHistory`
    

### Related Events

- `goal.set`
    
- `goal.adjusted`
    

### Related Projections

- `UserProfile`
    
- `ConstraintProjection`
    
- `PlanningHistory`
    

## 12. Operational Notes

This tool changes direction, not execution.

If the user asks for an actual plan, use `planning.manage_session` after goal handling or instead of goal-only handling.

## 13. Versioning

### Patch

Clarifies goal operation behavior.

### Minor

Adds optional goal metadata.

### Major

Changes goal operation semantics, required fields, emitted events, or safety behavior.