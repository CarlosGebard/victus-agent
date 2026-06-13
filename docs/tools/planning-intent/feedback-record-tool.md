---

## id: VICTUS-TOOL-FEEDBACK-RECORD  
contract_id: victus.tool.feedback.record  
title: Feedback Record Tool  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: feedback  
contract_type: tool_schema  
stability: experimental  
updated_at: 2026-06-12
---
# Feedback Record Tool

## 1. Purpose

Records user feedback about a plan, revision, meal, schedule, macro target, cost, time burden, or recommendation.

This tool captures the user’s reaction. It does not resolve the feedback, revise the plan directly, or create a new plan artifact.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.feedback.record`
    
- Runtime name: `feedback.record`
    
- Tool identity must not be derived from `feedback_id`, `revision_id`, or feedback text.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

|Field|Value|
|---|---|
|Exposed to model|`true`|
|Visible in nodes|`PlanIntentNode`|
|Tool type|`command`|
|Requires confirmation|`never`|
|Safety class|`planning_state_write`|

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "revision_id": {
      "type": "string"
    },
    "artifact_id": {
      "type": "string"
    },
    "verdict": {
      "type": "string",
      "enum": ["accepted", "rejected", "partial", "unclear"]
    },
    "scope": {
      "type": "object",
      "properties": {
        "type": {
          "type": "string",
          "enum": ["plan", "meal", "macro_targets", "schedule", "cost", "time", "recommendation", "other"]
        },
        "ref_id": {
          "type": "string"
        }
      },
      "required": ["type"]
    },
    "reason_tags": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "too_expensive",
          "too_restrictive",
          "too_time_consuming",
          "hungry",
          "low_energy",
          "doesnt_fit_schedule",
          "too_repetitive",
          "too_complex",
          "preference_mismatch",
          "unclear"
        ]
      }
    },
    "note": {
      "type": "string"
    }
  },
  "required": ["verdict", "scope"]
}
```

## 5. Output Schema

```json
{
  "status": "success | needs_clarification | blocked | rejected | error",
  "data": {
    "feedback_id": "uuid?"
  },
  "events_emitted": [
    {
      "event_type": "user.feedback",
      "event_id": "uuid",
      "seq": 0
    }
  ],
  "warnings": [],
  "clarification": null,
  "safety": null,
  "meta": {
    "confidence": 0.0
  }
}
```

## 6. Field Definitions

|Field|Type|Description|
|---|---|---|
|`revision_id`|string|Plan revision the feedback refers to when known.|
|`artifact_id`|string|Plan artifact the feedback refers to when known.|
|`verdict`|string|User’s acceptance, rejection, partial acceptance, or unclear reaction.|
|`scope`|object|Area of the plan or recommendation affected by the feedback.|
|`reason_tags`|array|Structured reasons for the feedback.|
|`note`|string|User-provided feedback text or additional detail.|

## 7. Responsibilities

### Required Responsibilities

- Record explicit user feedback.
    
- Preserve scope, verdict, reason tags, and note.
    
- Link feedback to a revision or artifact when possible.
    
- Request clarification when the feedback target is ambiguous.
    
- Delegate event emission to backend command handlers.
    

### Forbidden Responsibilities

- Must not revise plans directly.
    
- Must not resolve feedback directly.
    
- Must not create a new plan artifact.
    
- Must not change goals.
    
- Must not log meals.
    
- Must not treat feedback as accepted plan change.
    

## 8. Validation Rules

- `verdict` must be one allowed value.
    
- `scope.type` must be one allowed value.
    
- `reason_tags` may be empty only when `verdict = accepted`.
    
- Feedback should reference a revision, artifact, or active plan when available.
    
- Ambiguous feedback targets must return `needs_clarification`.
    

## 9. Runtime Behavior

### Reads

- `PlanningHistory`
    
- `ActivePlan`
    

### May Emit Events

- `user.feedback`
    

### Updates Projections

- `PlanningHistory`
    

### Internal Validators

- `feedback_scope_validation`
    
- `revision_resolution`
    
- `artifact_resolution`
    
- `active_plan_resolution`
    
- `reason_tag_validation`
    

## 10. Failure Modes

|Failure|Meaning|
|---|---|
|`needs_clarification`|Feedback target or scope is unclear.|
|`blocked`|Feedback implies unsafe requested action and must route to safety.|
|`rejected`|Feedback payload is invalid or cannot be linked.|
|`error`|Unexpected runtime failure.|

## 11. Relationships

### Upstream Nodes

- `PlanIntentNode`
    

### Downstream Contracts

- `DomainEventStore`
    
- `PlanningHistory`
    

### Related Events

- `user.feedback`
    
- `feedback.resolved`
    

### Related Projections

- `PlanningHistory`
    

## 12. Operational Notes

This tool records feedback only.

Plan changes caused by feedback must be handled by `planning.manage_session` after validation.

## 13. Versioning

### Patch

Clarifies feedback behavior.

### Minor

Adds optional scopes or reason tags.

### Major

Changes feedback identity, required fields, emitted events, or resolution behavior.