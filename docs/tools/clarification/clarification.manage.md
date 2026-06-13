---
id: VICTUS-TOOL-CLARIFICATION-MANAGE
contract_id: victus.tool.clarification.manage
title: Clarification Manage Tool
status: draft
version: v1
owner: victus-agent-runtime
domain: clarification
contract_type: tool_schema
stability: experimental
updated_at: 2026-06-12
---
# Clarification Manage Tool

## 1. Purpose

Creates or resolves clarification state when a request cannot be safely or correctly executed. It asks for the minimum missing information and preserves enough state to resume the blocked node.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.clarification.manage`
- Runtime name: `clarification.manage`
- Tool identity must not be derived from emitted event names, runtime traces, display labels, or implementation files.

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

| Field | Value |
|---|---|
| Exposed to model | `false` |
| Visible in nodes | `ClarificationNode` |
| Tool type | `clarification` |
| Requires confirmation | `never` |
| Safety class | `interaction` |

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "request",
        "resolve"
      ]
    },
    "clarification_id": {
      "type": "string"
    },
    "blocked_node": {
      "type": "string"
    },
    "blocked_action": {
      "type": "string"
    },
    "missing_fields": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "ambiguity_reason": {
      "type": "string"
    },
    "clarification_question": {
      "type": "string"
    },
    "expected_answer_type": {
      "type": "string",
      "enum": [
        "quantity",
        "time",
        "meal_reference",
        "preference_strength",
        "restriction_type",
        "goal_target",
        "yes_no",
        "free_text"
      ]
    },
    "user_answer": {
      "type": "string"
    },
    "resume_node": {
      "type": "string"
    },
    "resume_action": {
      "type": "string"
    }
  },
  "required": [
    "operation"
  ]
}
```

## 5. Output Schema

```json
{
  "status": "success | needs_clarification | blocked | rejected | error",
  "data": {
    "clarification_id": "uuid?",
    "resume_node": "string?",
    "resume_action": "string?"
  },
  "events_emitted": [
    {
      "event_type": "clarification.requested | clarification.resolved",
      "event_id": "uuid",
      "seq": 0
    }
  ],
  "warnings": [],
  "clarification": {
    "question": "string?",
    "missing_fields": []
  },
  "safety": null,
  "meta": {
    "confidence": 0.0
  }
}
```

## 6. Field Definitions

| Field | Type | Description |
|---|---|---|
| `operation` | string | Whether clarification is being requested or resolved. |
| `clarification_id` | string | Stable clarification identifier when resolving existing state. |
| `blocked_node` | string | Node that could not continue. |
| `blocked_action` | string | Action that was blocked by missing information. |
| `missing_fields` | array | Fields required to continue. |
| `ambiguity_reason` | string | Reason execution could not proceed. |
| `clarification_question` | string | User-facing question. |
| `expected_answer_type` | string | Expected answer category. |
| `user_answer` | string | User answer when resolving clarification. |
| `resume_node` | string | Node to resume after clarification. |
| `resume_action` | string | Action to resume after clarification. |

## 7. Responsibilities

### Required Responsibilities

- Create clarification requests with minimal missing information.
- Resolve clarification state when the user answers.
- Preserve blocked node and resume action.
- Avoid unnecessary broad questioning.

### Forbidden Responsibilities

- Must not execute the blocked domain action.
- Must not change nutrition, profile, planning, or evidence state directly.
- Must not ask for unrelated profile information.
- Must not expose internal routing details to the user.

## 8. Validation Rules

- `operation` must be one allowed value.
- `request` must include missing fields and a specific question.
- `resolve` must reference an existing clarification or active clarification state.
- `expected_answer_type` must be one allowed value when requesting.
- Clarification must not request more information than needed for the blocked action.

## 9. Runtime Behavior

### Reads

- `ConversationState`
- `ClarificationState`

### May Emit Events

- `clarification.requested`
- `clarification.resolved`

### Updates Projections

- `PlanningHistory when persisted as interaction history`

### Internal Validators

- `missing_field_validation`
- `resume_node_validation`
- `answer_type_validation`
- `clarification_state_resolution`

## 10. Failure Modes

| Failure | Meaning |
|---|---|
| `needs_clarification` | Required information is missing, ambiguous, or cannot be resolved safely. |
| `blocked` | The operation is unsafe or violates a safety/constraint policy. |
| `rejected` | The payload is validly parsed but cannot be applied. |
| `error` | Unexpected runtime or infrastructure failure. |

## 11. Relationships

### Upstream Nodes

- `ClarificationNode`
- `EventCaptureNode`
- `ProfileUpdateNode`
- `PlanIntentNode`
- `EvidenceAnswerNode`
- `SafetyPreCheckNode`

### Downstream Contracts

- `ClarificationState`
- `DomainEventStore`

### Related Events

- `clarification.requested`
- `clarification.resolved`

### Related Projections

- `PlanningHistory when persisted as interaction history`

## 12. Operational Notes

In v1 this can remain internal. Nodes can request clarification by returning a structured `needs_clarification` result, while this tool persists/resolves clarification state when needed.

## 13. Versioning

### Patch

Clarifies documentation without changing runtime behavior.

### Minor

Adds optional input fields, optional output fields, or compatible validation behavior.

### Major

Changes required inputs, tool meaning, emitted events, safety behavior, or output semantics.
