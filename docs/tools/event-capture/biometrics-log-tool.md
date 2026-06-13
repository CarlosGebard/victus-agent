---

## id: VICTUS-TOOL-BIOMETRICS-LOG  
contract_id: victus.tool.biometrics.log  
title: Biometrics Log Tool  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: biometrics  
contract_type: tool_schema  
stability: experimental  
updated_at: 2026-06-12
---
# Biometrics Log Tool

## 1. Purpose

Registers user-reported biometric or activity-related measurements.

This tool captures explicit measurements such as weight, height, sleep, and steps. It does not interpret trends, revise plans, diagnose health conditions, or modify goals.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.biometrics.log`
    
- Runtime name: `biometrics.log`
    
- Tool identity must not be derived from `biometrics_id`, measurement values, or timestamps.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

|Field|Value|
|---|---|
|Exposed to model|`true`|
|Visible in nodes|`EventCaptureNode`|
|Tool type|`command`|
|Requires confirmation|`on_unrealistic_values`|
|Safety class|`state_write`|

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "measured_at": {
      "type": "string"
    },
    "source": {
      "type": "string",
      "enum": ["manual", "wearable", "import"]
    },
    "measurements": {
      "type": "object",
      "properties": {
        "height_cm": {
          "type": "number"
        },
        "weight_kg": {
          "type": "number"
        },
        "sleep_hours": {
          "type": "number"
        },
        "steps": {
          "type": "integer"
        }
      }
    },
    "notes": {
      "type": "string"
    }
  },
  "required": ["measurements"]
}
```

## 5. Output Schema

```json
{
  "status": "success | needs_clarification | blocked | rejected | error",
  "data": {
    "biometrics_id": "uuid?"
  },
  "events_emitted": [
    {
      "event_type": "biometrics.logged",
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
|`measured_at`|string|Time when the measurement was taken.|
|`source`|string|Origin of the measurement.|
|`measurements`|object|Explicit biometric or activity values reported by the user.|
|`height_cm`|number|User height in centimeters.|
|`weight_kg`|number|User body weight in kilograms.|
|`sleep_hours`|number|Sleep duration in hours.|
|`steps`|integer|Step count for the relevant day or period.|
|`notes`|string|Optional user-provided context.|

## 7. Responsibilities

### Required Responsibilities

- Register explicitly stated biometric measurements.
    
- Preserve the measurement source.
    
- Validate measurement ranges before persistence.
    
- Ask clarification when time, unit, or value is ambiguous.
    
- Delegate event emission to backend command handlers.
    

### Forbidden Responsibilities

- Must not infer unstated measurements.
    
- Must not detect trends.
    
- Must not revise plans.
    
- Must not change goals.
    
- Must not diagnose health status.
    
- Must not treat one measurement as long-term progress.
    

## 8. Validation Rules

- `measurements` must contain at least one supported measurement.
    
- Numeric values must be within reasonable ranges.
    
- Unknown units must return `needs_clarification`.
    
- Unusually extreme values must require confirmation.
    
- Measurements must not overwrite historical events.
    

## 9. Runtime Behavior

### Reads

- `NutritionStatus`
    
- `UserProfile`
    

### May Emit Events

- `biometrics.logged`
    

### Updates Projections

- `NutritionStatus`
    
- `UserProfile` when durable anthropometrics are updated
    

### Internal Validators

- `measurement_range_validation`
    
- `unit_validation`
    
- `timestamp_resolution`
    
- `duplicate_measurement_check`
    

## 10. Failure Modes

|Failure|Meaning|
|---|---|
|`needs_clarification`|Measurement, unit, or time is missing or ambiguous.|
|`blocked`|Measurement cannot be safely accepted without additional handling.|
|`rejected`|Value is invalid or unsupported.|
|`error`|Unexpected runtime failure.|

## 11. Relationships

### Upstream Nodes

- `EventCaptureNode`
    

### Downstream Contracts

- `DomainEventStore`
    
- `NutritionStatus`
    
- `UserProfile`
    

### Related Events

- `biometrics.logged`
    

### Related Projections

- `NutritionStatus`
    
- `UserProfile`
    

## 12. Operational Notes

Durable fields such as height may update profile-level projections.

Fast-changing fields such as weight, sleep, and steps should primarily update status projections.

## 13. Versioning

### Patch

Clarifies measurement descriptions or validation wording.

### Minor

Adds optional supported measurements.

### Major

Changes required fields, measurement semantics, or projection update behavior.