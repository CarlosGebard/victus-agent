---

## id: VICTUS-TOOL-PLANNING-MANAGE-SESSION  
contract_id: victus.tool.planning.manage_session  
title: Planning Manage Session Tool  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: planning  
contract_type: tool_schema  
stability: experimental  
updated_at: 2026-06-12
---
# Planning Manage Session Tool

## 1. Purpose

Manages planning sessions, revisions, and plan artifacts.

This tool creates or updates the planning workflow around a user’s goal and current context. It does not log meals, manage profile restrictions, or search evidence directly.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.planning.manage_session`
    
- Runtime name: `planning.manage_session`
    
- Tool identity must not be derived from `session_id`, `revision_id`, `artifact_id`, or emitted event names.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

|Field|Value|
|---|---|
|Exposed to model|`partially`|
|Visible in nodes|`PlanIntentNode`|
|Tool type|`command`|
|Requires confirmation|`on_accept_or_destructive_change`|
|Safety class|`planning_state_write`|

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": ["start_session", "create_revision", "save_artifact", "accept_artifact", "reject_artifact", "end_session"]
    },
    "session_id": {
      "type": "string"
    },
    "revision_id": {
      "type": "string"
    },
    "parent_revision_id": {
      "type": "string"
    },
    "artifact_id": {
      "type": "string"
    },
    "reason": {
      "type": "string"
    },
    "objectives": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": {
            "type": "string",
            "enum": ["kcal", "protein", "performance", "cost", "time", "adherence", "preference_fit"]
          },
          "direction": {
            "type": "string",
            "enum": ["down", "up", "maintain", "optimize"]
          },
          "priority": {
            "type": "integer",
            "minimum": 1
          }
        },
        "required": ["type", "direction", "priority"]
      }
    },
    "artifact": {
      "type": "object",
      "properties": {
        "targets": {
          "type": "object"
        },
        "structure": {
          "type": "object"
        },
        "warnings": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "scores": {
          "type": "object"
        }
      }
    },
    "status": {
      "type": "string",
      "enum": ["completed", "abandoned", "canceled", "error"]
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
    "session_id": "uuid?",
    "revision_id": "uuid?",
    "artifact_id": "uuid?"
  },
  "events_emitted": [
    {
      "event_type": "plan.session_started | plan.revision_created | plan.artifact_saved | plan.session_ended | planning.artifact_accepted | planning.artifact_rejected",
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
    "confidence": 0.0,
    "planner_version": 1
  }
}
```

## 6. Field Definitions

|Field|Type|Description|
|---|---|---|
|`operation`|string|Planning workflow operation.|
|`session_id`|string|Stable planning session identifier.|
|`revision_id`|string|Stable revision identifier.|
|`parent_revision_id`|string|Parent revision when creating a revision from a previous one.|
|`artifact_id`|string|Stable plan artifact identifier.|
|`reason`|string|Reason for the planning action.|
|`objectives`|array|Ordered optimization objectives for a revision.|
|`artifact`|object|Concrete plan artifact payload to save.|
|`status`|string|Final session status when ending a session.|
|`user_confirmed`|boolean|Confirmation for accepting or rejecting relevant plan artifacts.|

## 7. Responsibilities

### Required Responsibilities

- Start a planning session.
    
- Create plan revisions from current context.
    
- Save generated plan artifacts.
    
- Accept or reject plan artifacts when explicitly requested.
    
- End planning sessions.
    
- Preserve planning reasons, objectives, and artifact references.
    
- Delegate event emission to backend command handlers.
    

### Forbidden Responsibilities

- Must not log meals.
    
- Must not manage restrictions or preferences.
    
- Must not search evidence directly.
    
- Must not bypass safety validation.
    
- Must not mark a plan as accepted without explicit user intent.
    
- Must not create a revision without required context digests.
    

## 8. Validation Rules

- `operation` must be one allowed value.
    
- `create_revision` must have a valid session.
    
- `save_artifact` must have a valid revision.
    
- `accept_artifact` must have a valid artifact and explicit user intent.
    
- `end_session` must include valid final status.
    
- Revision objectives must have unique priorities.
    
- Planning actions that affect user safety must require safety validation.
    

## 9. Runtime Behavior

### Reads

- `UserProfile`
    
- `ConstraintProjection`
    
- `NutritionStatus`
    
- `PlanningHistory`
    
- `ActivePlan`
    

### May Emit Events

- `plan.session_started`
    
- `plan.revision_created`
    
- `plan.artifact_saved`
    
- `plan.session_ended`
    
- `planning.artifact_accepted`
    
- `planning.artifact_rejected`
    

### Updates Projections

- `PlanningHistory`
    
- `ActivePlan` when a plan artifact is accepted
    

### Internal Validators

- `session_resolution`
    
- `revision_resolution`
    
- `artifact_resolution`
    
- `planning_context_digest_validation`
    
- `objective_priority_validation`
    
- `plan_constraint_validation`
    
- `safety_plan_policy`
    

## 10. Failure Modes

|Failure|Meaning|
|---|---|
|`needs_clarification`|Planning target, session, revision, artifact, or user intent is unclear.|
|`blocked`|Planning action violates safety or constraints.|
|`rejected`|Required planning context is missing or invalid.|
|`error`|Unexpected runtime failure.|

## 11. Relationships

### Upstream Nodes

- `PlanIntentNode`
    
- `SafetyPreCheckNode`
    

### Downstream Contracts

- `DomainEventStore`
    
- `PlanningHistory`
    
- `ActivePlan`
    

### Related Events

- `plan.session_started`
    
- `plan.revision_created`
    
- `plan.artifact_saved`
    
- `plan.session_ended`
    
- `planning.artifact_accepted`
    
- `planning.artifact_rejected`
    

### Related Projections

- `PlanningHistory`
    
- `ActivePlan`
    

## 12. Operational Notes

This tool is intentionally medium-sized.

The LLM may request planning operations, but backend handlers must construct context digests, validate constraints, and enforce safety before events are emitted.

## 13. Versioning

### Patch

Clarifies planning operation behavior.

### Minor

Adds optional operation metadata.

### Major

Changes operation semantics, required fields, emitted events, or acceptance behavior.