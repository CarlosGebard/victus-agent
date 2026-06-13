---

## id: VICTUS-TOOL-NUTRITION-MANAGE-MEAL  
contract_id: victus.tool.nutrition.manage_meal  
title: Nutrition Manage Meal Tool  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: nutrition  
contract_type: tool_schema  
stability: experimental  
updated_at: 2026-06-12
---
# Nutrition Manage Meal Tool

## 1. Purpose

Manages user-reported meals.

This tool logs, edits, or deletes meals depending on the requested operation. It captures explicit meal information and delegates validation, normalization, and event emission to backend handlers.

It does not estimate full nutrition by itself, create plans, revise goals, or answer evidence questions.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.nutrition.manage_meal`
    
- Runtime name: `nutrition.manage_meal`
    
- Tool identity must not be derived from `meal_id`, food labels, timestamps, or emitted event names.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

|Field|Value|
|---|---|
|Exposed to model|`true`|
|Visible in nodes|`EventCaptureNode`|
|Tool type|`command`|
|Requires confirmation|`on_delete_or_ambiguous_reference`|
|Safety class|`state_write`|

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["log", "edit", "delete"]
    },
    "meal_id": {
      "type": "string"
    },
    "meal_reference": {
      "type": "string"
    },
    "meal_type": {
      "type": "string",
      "enum": ["breakfast", "lunch", "dinner", "snack", "unknown"]
    },
    "consumed_at": {
      "type": "string"
    },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "item_id": {
            "type": "string"
          },
          "operation": {
            "type": "string",
            "enum": ["add", "update", "remove"]
          },
          "food_label": {
            "type": "string"
          },
          "quantity": {
            "type": "object",
            "properties": {
              "value": {
                "type": "number"
              },
              "unit": {
                "type": "string",
                "enum": ["g", "ml", "unit", "serving", "cup", "tbsp", "tsp", "unknown"]
              }
            },
            "required": ["value", "unit"]
          },
          "notes": {
            "type": "string"
          }
        }
      }
    },
    "reason": {
      "type": "string"
    },
    "user_confirmed": {
      "type": "boolean"
    },
    "source": {
      "type": "string",
      "enum": ["manual", "voice", "import"]
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
    "meal_id": "uuid?"
  },
  "events_emitted": [
    {
      "event_type": "meal.logged | meal.edited | meal.deleted",
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
|`operation`|string|Meal operation requested by the user.|
|`meal_id`|string|Stable meal identifier when known. Required for direct edit or delete.|
|`meal_reference`|string|Natural-language reference to the target meal when `meal_id` is unknown.|
|`meal_type`|string|Meal category.|
|`consumed_at`|string|Time of consumption if provided or resolvable.|
|`items`|array|Meal items involved in the operation.|
|`items.item_id`|string|Stable item identifier when updating or removing an existing item.|
|`items.operation`|string|Item-level operation used during meal edits.|
|`items.food_label`|string|User-facing food name before canonical food resolution.|
|`items.quantity`|object|Explicit quantity reported by the user.|
|`reason`|string|Reason for edit or delete.|
|`user_confirmed`|boolean|Confirmation for destructive or ambiguous operations.|
|`source`|string|Origin of the input.|

## 7. Responsibilities

### Required Responsibilities

- Log a new meal when `operation = log`.
    
- Edit a known or resolvable meal when `operation = edit`.
    
- Delete or invalidate a known meal when `operation = delete`.
    
- Preserve explicitly reported foods, quantities, times, and user notes.
    
- Request clarification when required references or quantities are missing.
    
- Delegate food resolution, safety checks, idempotency, and event emission to backend handlers.
    

### Forbidden Responsibilities

- Must not invent missing quantities.
    
- Must not estimate calories or macros by itself.
    
- Must not create or revise plans.
    
- Must not update goals.
    
- Must not physically erase immutable event history.
    
- Must not delete a meal without confirmation.
    
- Must not silently edit an ambiguous meal reference.
    

## 8. Validation Rules

- `operation` must be one allowed value.
    
- `log` must include at least one meal item.
    
- `edit` must resolve exactly one target meal.
    
- `delete` must resolve exactly one target meal.
    
- `delete` must require `user_confirmed = true`.
    
- Item updates or removals must reference existing item identifiers when available.
    
- Restricted foods must trigger safety validation.
    
- Ambiguous meal references must return `needs_clarification`.
    
- Duplicate retries must be handled idempotently by runtime.
    

## 9. Runtime Behavior

### Reads

- `UserProfile`
    
- `ConstraintProjection`
    
- `NutritionStatus`
    
- `MealLog`
    

### May Emit Events

- `meal.logged`
    
- `meal.edited`
    
- `meal.deleted`
    

### Updates Projections

- `NutritionStatus`
    

### Internal Validators

- `food_resolution`
    
- `quantity_validation`
    
- `meal_reference_resolution`
    
- `item_reference_resolution`
    
- `restriction_check`
    
- `duplicate_meal_check`
    
- `delete_confirmation_check`
    

## 10. Failure Modes

|Failure|Meaning|
|---|---|
|`needs_clarification`|Required quantity, meal reference, item reference, or time is missing or ambiguous.|
|`blocked`|Operation conflicts with a high-severity safety constraint.|
|`rejected`|Operation cannot be applied because the input or target is invalid.|
|`error`|Unexpected runtime failure.|

## 11. Relationships

### Upstream Nodes

- `EventCaptureNode`
    

### Downstream Contracts

- `DomainEventStore`
    
- `NutritionStatus`
    

### Related Events

- `meal.logged`
    
- `meal.edited`
    
- `meal.deleted`
    

### Related Projections

- `NutritionStatus`
    

## 12. Operational Notes

This tool replaces separate meal log, edit, and delete tools.

The LLM should decide the intended operation, but the backend must validate whether that operation can actually be applied.

## 13. Versioning

### Patch

Clarifies meal operation behavior.

### Minor

Adds optional fields, units, or item metadata.

### Major

Changes operation semantics, required fields, emitted events, or delete confirmation behavior.