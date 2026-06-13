---

## id: VICTUS-TOOL-PROFILE-MANAGE-CONTEXT  
contract_id: victus.tool.profile.manage_context  
title: Profile Manage Context Tool  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: profile  
contract_type: tool_schema  
stability: experimental  
updated_at: 2026-06-12
---
# Profile Manage Context Tool

## 1. Purpose

Manages stable user profile context.

This tool adds or updates user restrictions and preferences. It handles durable context that should influence future recommendations, planning, and constraint checks.

It does not manage goals, log meals, revise plans, or answer evidence questions.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.profile.manage_context`
    
- Runtime name: `profile.manage_context`
    
- Tool identity must not be derived from `restriction_id`, `preference_id`, labels, or emitted event names.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

|Field|Value|
|---|---|
|Exposed to model|`true`|
|Visible in nodes|`ProfileUpdateNode`|
|Tool type|`command`|
|Requires confirmation|`on_safety_relevant_or_low_confidence`|
|Safety class|`safety_relevant`|

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "target_type": {
      "type": "string",
      "enum": ["restriction", "preference"]
    },
    "operation": {
      "type": "string",
      "enum": ["add", "update", "deactivate", "set"]
    },
    "target_id": {
      "type": "string"
    },
    "target_reference": {
      "type": "string"
    },
    "restriction": {
      "type": "object",
      "properties": {
        "restriction_kind": {
          "type": "string",
          "enum": ["medical", "religious", "allergy", "intolerance", "advisory", "unknown"]
        },
        "condition_label": {
          "type": "string"
        },
        "restricted_substance_label": {
          "type": "string"
        },
        "severity": {
          "type": "string",
          "enum": ["low", "medium", "high", "unknown"]
        },
        "scope": {
          "type": "string",
          "enum": ["absolute", "dietary", "advisory", "unknown"]
        },
        "evidence_level": {
          "type": "string",
          "enum": ["declared", "clinical", "unknown"]
        }
      }
    },
    "preference": {
      "type": "object",
      "properties": {
        "category": {
          "type": "string",
          "enum": ["food", "cuisine", "budget", "time", "schedule", "cooking", "other"]
        },
        "item_label": {
          "type": "string"
        },
        "preference": {
          "type": "string",
          "enum": ["like", "neutral", "dislike"]
        },
        "strength": {
          "type": "number",
          "minimum": 0,
          "maximum": 1
        }
      }
    },
    "reason": {
      "type": "string"
    },
    "user_confirmed": {
      "type": "boolean"
    },
    "note": {
      "type": "string"
    }
  },
  "required": ["target_type", "operation"]
}
```

## 5. Output Schema

```json
{
  "status": "success | needs_clarification | blocked | rejected | error",
  "data": {
    "target_type": "restriction | preference",
    "target_id": "uuid?"
  },
  "events_emitted": [
    {
      "event_type": "restriction.added | restriction.updated | preference.updated",
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
|`target_type`|string|Profile object being managed.|
|`operation`|string|Requested operation for the target type.|
|`target_id`|string|Stable identifier when updating or deactivating an existing object.|
|`target_reference`|string|Natural-language reference when `target_id` is unknown.|
|`restriction`|object|Restriction payload when managing a restriction.|
|`preference`|object|Preference payload when managing a preference.|
|`reason`|string|Reason for update or deactivation.|
|`user_confirmed`|boolean|Confirmation for safety-relevant changes.|
|`note`|string|Optional user-provided detail.|

## 7. Responsibilities

### Required Responsibilities

- Add or update user restrictions.
    
- Set or update user preferences.
    
- Preserve the distinction between hard restrictions and soft preferences.
    
- Require confirmation when reducing safety-relevant restriction severity or scope.
    
- Request clarification when the target type, target reference, or meaning is ambiguous.
    
- Delegate canonical coding, safety checks, and event emission to backend handlers.
    

### Forbidden Responsibilities

- Must not manage goals.
    
- Must not log meals.
    
- Must not create or revise plans.
    
- Must not answer evidence questions.
    
- Must not treat preferences as medical restrictions.
    
- Must not infer clinical status from casual language.
    
- Must not silently reduce safety constraints.
    
- Must not overwrite unrelated profile context.
    

## 8. Validation Rules

- `target_type` must be one allowed value.
    
- `operation` must be one allowed value.
    
- `target_type = restriction` must provide `restriction` fields required by the selected operation.
    
- `target_type = preference` must provide `preference` fields required by the selected operation.
    
- Updating or deactivating existing targets must resolve exactly one target.
    
- Reducing restriction severity or scope must require `user_confirmed = true`.
    
- High-severity restrictions must trigger safety validation.
    
- Ambiguous profile statements must return `needs_clarification`.
    

## 9. Runtime Behavior

### Reads

- `UserProfile`
    
- `ConstraintProjection`
    

### May Emit Events

- `restriction.added`
    
- `restriction.updated`
    
- `preference.updated`
    

### Updates Projections

- `UserProfile`
    
- `ConstraintProjection`
    

### Internal Validators

- `target_type_validation`
    
- `restriction_type_validation`
    
- `restricted_substance_resolution`
    
- `preference_item_resolution`
    
- `target_reference_resolution`
    
- `duplicate_reconciliation`
    
- `severity_change_policy`
    
- `safety_constraint_policy`
    

## 10. Failure Modes

|Failure|Meaning|
|---|---|
|`needs_clarification`|Target type, target reference, substance, preference, or safety meaning is unclear.|
|`blocked`|Requested change creates unsafe downstream behavior.|
|`rejected`|Target does not exist, confirmation is missing, or payload is invalid.|
|`error`|Unexpected runtime failure.|

## 11. Relationships

### Upstream Nodes

- `ProfileUpdateNode`
    
- `SafetyPreCheckNode`
    

### Downstream Contracts

- `DomainEventStore`
    
- `UserProfile`
    
- `ConstraintProjection`
    

### Related Events

- `restriction.added`
    
- `restriction.updated`
    
- `preference.updated`
    

### Related Projections

- `UserProfile`
    
- `ConstraintProjection`
    

## 12. Operational Notes

This tool replaces separate restriction and preference tools.

Goals are intentionally excluded because they belong to planning intent, not profile context.

Hard restrictions must always override soft preferences.

## 13. Versioning

### Patch

Clarifies profile operation behavior.

### Minor

Adds optional restriction or preference metadata.

### Major

Changes target type semantics, required fields, emitted events, or safety behavior.