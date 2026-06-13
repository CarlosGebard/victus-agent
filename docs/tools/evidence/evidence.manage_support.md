---
id: VICTUS-TOOL-EVIDENCE-MANAGE-SUPPORT
contract_id: victus.tool.evidence.manage_support
title: Evidence Manage Support Tool
status: draft
version: v1
owner: victus-agent-runtime
domain: evidence
contract_type: tool_schema
stability: experimental
updated_at: 2026-06-12
---
# Evidence Manage Support Tool

## 1. Purpose

Builds or attaches stable evidence support for a generated claim, recommendation, or planning revision. It does not search broadly by itself and does not modify nutrition status or profile context.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.evidence.manage_support`
- Runtime name: `evidence.manage_support`
- Tool identity must not be derived from emitted event names, runtime traces, display labels, or implementation files.

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

| Field | Value |
|---|---|
| Exposed to model | `partially` |
| Visible in nodes | `EvidenceAnswerNode, PlanIntentNode` |
| Tool type | `command` |
| Requires confirmation | `never` |
| Safety class | `evidence_write` |

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "operation": {
      "type": "string",
      "enum": [
        "build_bundle",
        "attach_to_claim",
        "attach_to_revision"
      ]
    },
    "revision_id": {
      "type": "string"
    },
    "claim_id": {
      "type": "string"
    },
    "candidate_sources": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "source_type": {
            "type": "string",
            "enum": [
              "doi",
              "pmid",
              "url",
              "guideline"
            ]
          },
          "source_id": {
            "type": "string"
          },
          "title": {
            "type": "string"
          },
          "locator": {
            "type": "string"
          },
          "quote_hash": {
            "type": "string"
          }
        },
        "required": [
          "source_type",
          "source_id"
        ]
      }
    },
    "bundle_id": {
      "type": "string"
    },
    "reason": {
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
    "bundle_id": "uuid?",
    "claim_id": "uuid?",
    "revision_id": "uuid?"
  },
  "events_emitted": [
    {
      "event_type": "claim.generated | evidence.cited",
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

| Field | Type | Description |
|---|---|---|
| `operation` | string | Evidence support operation. |
| `revision_id` | string | Planning revision that evidence supports when applicable. |
| `claim_id` | string | Claim that evidence supports when applicable. |
| `candidate_sources` | array | Evidence candidates selected from retrieval results. |
| `bundle_id` | string | Stable evidence bundle identifier when attaching an existing bundle. |
| `reason` | string | Reason for building or attaching evidence support. |

## 7. Responsibilities

### Required Responsibilities

- Build evidence bundles from retrieved candidate sources.
- Attach evidence bundles to claims or revisions.
- Preserve source identifiers, locators, titles, and quote hashes.
- Emit evidence-related events through backend handlers.

### Forbidden Responsibilities

- Must not perform unconstrained evidence search.
- Must not modify user nutrition status.
- Must not update goals.
- Must not fabricate sources.
- Must not attach evidence without at least one source.

## 8. Validation Rules

- `operation` must be one allowed value.
- `build_bundle` must include candidate sources.
- `attach_to_claim` must include a valid claim or claim context.
- `attach_to_revision` must include a valid revision.
- Sources must have stable source identifiers.
- Evidence attachments must preserve traceability to retrieved evidence.

## 9. Runtime Behavior

### Reads

- `EvidenceRAG`
- `PlanningHistory`
- `Claims`

### May Emit Events

- `claim.generated`
- `evidence.cited`

### Updates Projections

- `PlanningHistory`
- `Claims`
- `EvidenceLinks`

### Internal Validators

- `source_validation`
- `bundle_shape_validation`
- `claim_resolution`
- `revision_resolution`
- `evidence_traceability_check`

## 10. Failure Modes

| Failure | Meaning |
|---|---|
| `needs_clarification` | Required information is missing, ambiguous, or cannot be resolved safely. |
| `blocked` | The operation is unsafe or violates a safety/constraint policy. |
| `rejected` | The payload is validly parsed but cannot be applied. |
| `error` | Unexpected runtime or infrastructure failure. |

## 11. Relationships

### Upstream Nodes

- `EvidenceAnswerNode`
- `PlanIntentNode`

### Downstream Contracts

- `DomainEventStore`
- `PlanningHistory`
- `Claims`
- `EvidenceLinks`

### Related Events

- `claim.generated`
- `evidence.cited`

### Related Projections

- `PlanningHistory`
- `Claims`
- `EvidenceLinks`

## 12. Operational Notes

This tool represents the epistemology boundary. Search is separate from support attachment so the system can distinguish retrieval from persisted justification.

## 13. Versioning

### Patch

Clarifies documentation without changing runtime behavior.

### Minor

Adds optional input fields, optional output fields, or compatible validation behavior.

### Major

Changes required inputs, tool meaning, emitted events, safety behavior, or output semantics.
