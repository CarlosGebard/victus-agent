---
id: VICTUS-TOOL-SAFETY-TRIAGE
contract_id: victus.tool.safety.triage
title: Safety Triage Tool
status: draft
version: v1
owner: victus-agent-runtime
domain: safety
contract_type: tool_schema
stability: experimental
updated_at: 2026-06-12
---
# Safety Triage Tool

## 1. Purpose

Evaluates safety risk for user requests, proposed actions, symptoms, restrictions, and generated recommendations. It decides whether execution may continue, needs warning, needs clarification, or must be blocked.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.safety.triage`
- Runtime name: `safety.triage`
- Tool identity must not be derived from emitted event names, runtime traces, display labels, or implementation files.

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

| Field | Value |
|---|---|
| Exposed to model | `false` |
| Visible in nodes | `SafetyPreCheckNode, SafetyTriageNode` |
| Tool type | `safety` |
| Requires confirmation | `never` |
| Safety class | `safety_core` |

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "normalized_text": {
      "type": "string"
    },
    "proposed_action": {
      "type": "object"
    },
    "risk_context": {
      "type": "object"
    },
    "user_context_digest": {
      "type": "string"
    },
    "constraints_digest": {
      "type": "string"
    },
    "nutrition_status_digest": {
      "type": "string"
    }
  },
  "required": []
}
```

## 5. Output Schema

```json
{
  "status": "success | needs_clarification | blocked | rejected | error",
  "data": {
    "safety_status": "ok | warning | blocked | needs_clarification",
    "risk_category": "medical_symptom | extreme_deficit | eating_risk | allergy_or_restriction | unsafe_training | unknown",
    "reasons": [],
    "recommended_next_node": "continue | clarification | safety_response"
  },
  "events_emitted": [
    {
      "event_type": "safety.guard_triggered | safety.action_blocked",
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
    "ruleset_version": 1
  }
}
```

## 6. Field Definitions

| Field | Type | Description |
|---|---|---|
| `normalized_text` | string | Normalized user input when evaluating natural language risk. |
| `proposed_action` | object | Structured action being evaluated. |
| `risk_context` | object | Additional context relevant to safety. |
| `user_context_digest` | string | Digest of profile context used. |
| `constraints_digest` | string | Digest of constraints used. |
| `nutrition_status_digest` | string | Digest of status context used. |

## 7. Responsibilities

### Required Responsibilities

- Evaluate safety before sensitive writes or recommendations.
- Return clear safety status and reason codes.
- Block unsafe actions when required.
- Ask clarification when safety cannot be determined.
- Emit safety events through backend handlers when needed.

### Forbidden Responsibilities

- Must not generate full user-facing medical advice.
- Must not diagnose the user.
- Must not create or revise plans.
- Must not log symptoms directly.
- Must not silently allow high-risk actions.

## 8. Validation Rules

- Safety status must be one allowed value.
- Blocked actions must include reasons.
- Risk category must be provided when risk is detected.
- Safety-sensitive plan changes must not continue without this check.
- Ruleset version must be recorded for reproducibility.

## 9. Runtime Behavior

### Reads

- `UserProfile`
- `ConstraintProjection`
- `NutritionStatus`
- `ProposedAction`

### May Emit Events

- `safety.guard_triggered`
- `safety.action_blocked`

### Updates Projections

- `PlanningHistory`
- `ConstraintProjection when temporary guards are created`

### Internal Validators

- `risk_category_detection`
- `constraint_policy_check`
- `medical_risk_policy`
- `goal_safety_policy`
- `recommendation_safety_policy`

## 10. Failure Modes

| Failure | Meaning |
|---|---|
| `needs_clarification` | Required information is missing, ambiguous, or cannot be resolved safely. |
| `blocked` | The operation is unsafe or violates a safety/constraint policy. |
| `rejected` | The payload is validly parsed but cannot be applied. |
| `error` | Unexpected runtime or infrastructure failure. |

## 11. Relationships

### Upstream Nodes

- `SafetyPreCheckNode`
- `PlanIntentNode`
- `EventCaptureNode`
- `ProfileUpdateNode`

### Downstream Contracts

- `SafetyTriageNode`
- `ClarificationNode`
- `DomainEventStore`

### Related Events

- `safety.guard_triggered`
- `safety.action_blocked`

### Related Projections

- `PlanningHistory`
- `ConstraintProjection when temporary guards are created`

## 12. Operational Notes

This should be deterministic-first. The LLM should not receive broad write tools before safety precheck has passed.

## 13. Versioning

### Patch

Clarifies documentation without changing runtime behavior.

### Minor

Adds optional input fields, optional output fields, or compatible validation behavior.

### Major

Changes required inputs, tool meaning, emitted events, safety behavior, or output semantics.
