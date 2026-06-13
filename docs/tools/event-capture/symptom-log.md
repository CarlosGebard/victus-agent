---
## id: VICTUS-TOOL-SYMPTOM-LOG  
contract_id: victus.tool.symptom.log  
title: Symptom Log Tool  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: symptom  
contract_type: tool_schema  
stability: experimental  
updated_at: 2026-06-12
---
# Symptom Log Tool

## 1. Purpose

Registers a user-reported symptom or subjective signal relevant to nutrition, recovery, adherence, or safety.

This tool captures the symptom report. It does not diagnose, prescribe treatment, revise plans directly, or decide final medical safety outcomes.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.symptom.log`
    
- Runtime name: `symptom.log`
    
- Tool identity must not be derived from `symptom_id`, symptom label, severity, or timestamp.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

|Field|Value|
|---|---|
|Exposed to model|`true`|
|Visible in nodes|`EventCaptureNode`|
|Tool type|`command`|
|Requires confirmation|`on_high_severity`|
|Safety class|`safety_relevant`|

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "reported_at": {
      "type": "string"
    },
    "symptom": {
      "type": "object",
      "properties": {
        "category": {
          "type": "string",
          "enum": ["energy", "sleep", "hunger", "recovery", "mood", "performance", "digestive", "pain", "other"]
        },
        "label": {
          "type": "string"
        }
      },
      "required": ["category", "label"]
    },
    "severity_1_10": {
      "type": "integer",
      "minimum": 1,
      "maximum": 10
    },
    "expected_duration": {
      "type": "string",
      "enum": ["day", "few_days", "week", "unknown"]
    },
    "context": {
      "type": "object",
      "properties": {
        "training_week_heavy": {
          "type": "boolean"
        },
        "workload_high": {
          "type": "boolean"
        },
        "diet_change_recent": {
          "type": "boolean"
        },
        "sleep_low_recent": {
          "type": "boolean"
        }
      }
    },
    "note": {
      "type": "string"
    }
  },
  "required": ["symptom"]
}
```

## 5. Output Schema

```json
{
  "status": "success | needs_clarification | blocked | rejected | error",
  "data": {
    "symptom_id": "uuid?"
  },
  "events_emitted": [
    {
      "event_type": "symptom.logged",
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
|`reported_at`|string|Time when the symptom was reported or experienced.|
|`symptom`|object|Symptom category and user-facing label.|
|`category`|string|Broad symptom class.|
|`label`|string|Specific symptom label provided or normalized from user text.|
|`severity_1_10`|integer|User-reported intensity from 1 to 10.|
|`expected_duration`|string|User-estimated duration if provided.|
|`context`|object|Optional contextual factors around the symptom.|
|`note`|string|Optional user-provided detail.|

## 7. Responsibilities

### Required Responsibilities

- Register explicit symptom or subjective signal reports.
    
- Preserve symptom category, label, severity, and context when available.
    
- Trigger safety validation for high-severity or medically sensitive symptoms.
    
- Ask clarification when symptom meaning or severity is unclear.
    
- Delegate event emission to backend command handlers.
    

### Forbidden Responsibilities

- Must not diagnose the user.
    
- Must not prescribe treatment.
    
- Must not revise nutrition plans directly.
    
- Must not change goals directly.
    
- Must not minimize high-severity symptoms.
    
- Must not infer clinical conditions from vague symptoms.
    

## 8. Validation Rules

- `symptom.category` must be one allowed value.
    
- `symptom.label` must not be empty.
    
- `severity_1_10` must be between `1` and `10` when provided.
    
- High-severity symptoms must require safety validation.
    
- Medical-risk symptoms must route to safety handling.
    
- Ambiguous symptom reports must return `needs_clarification`.
    

## 9. Runtime Behavior

### Reads

- `UserProfile`
    
- `ConstraintProjection`
    
- `NutritionStatus`
    

### May Emit Events

- `symptom.logged`
    
- `safety.guard_triggered`
    
- `safety.action_blocked`
    

### Updates Projections

- `NutritionStatus`
    
- `ConstraintProjection` when a temporary guard is created
    

### Internal Validators

- `symptom_category_validation`
    
- `severity_validation`
    
- `medical_risk_detection`
    
- `temporary_constraint_policy`
    

## 10. Failure Modes

|Failure|Meaning|
|---|---|
|`needs_clarification`|Symptom, severity, time, or risk context is unclear.|
|`blocked`|The requested follow-up action is unsafe.|
|`rejected`|Symptom payload is invalid or unsupported.|
|`error`|Unexpected runtime failure.|

## 11. Relationships

### Upstream Nodes

- `EventCaptureNode`
    
- `SafetyPreCheckNode`
    

### Downstream Contracts

- `DomainEventStore`
    
- `NutritionStatus`
    
- `ConstraintProjection`
    
- `SafetyTriageNode`
    

### Related Events

- `symptom.logged`
    
- `safety.guard_triggered`
    
- `safety.action_blocked`
    

### Related Projections

- `NutritionStatus`
    
- `ConstraintProjection`
    

## 12. Operational Notes

This tool records what the user reports.

Risk interpretation belongs to safety validators and safety nodes, not to the tool schema itself.

## 13. Versioning

### Patch

Clarifies symptom field descriptions or validation wording.

### Minor

Adds optional symptom categories or context fields.

### Major

Changes safety behavior, required fields, or symptom semantics.