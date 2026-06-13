---
id: VICTUS-TOOL-EVIDENCE-SEARCH
contract_id: victus.tool.evidence.search
title: Evidence Search Tool
status: draft
version: v1
owner: victus-agent-runtime
domain: evidence
contract_type: tool_schema
stability: experimental
updated_at: 2026-06-12
---
# Evidence Search Tool

## 1. Purpose

Searches the scientific evidence RAG for support, explanation, or uncertainty reduction. It retrieves evidence candidates but does not update user state, persist claims, or attach evidence to planning history.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.tool.evidence.search`
- Runtime name: `evidence.search`
- Tool identity must not be derived from emitted event names, runtime traces, display labels, or implementation files.

### Ownership

Owned by `victus-agent-runtime`.

## 3. Exposure

| Field | Value |
|---|---|
| Exposed to model | `true` |
| Visible in nodes | `EvidenceAnswerNode, PlanIntentNode` |
| Tool type | `retrieval` |
| Requires confirmation | `never` |
| Safety class | `read` |

## 4. Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string"
    },
    "question_type": {
      "type": "string",
      "enum": [
        "general_science",
        "recommendation_support",
        "safety_support",
        "tradeoff",
        "guideline",
        "unknown"
      ]
    },
    "population_context": {
      "type": "string"
    },
    "intervention_or_exposure": {
      "type": "string"
    },
    "outcome": {
      "type": "string"
    },
    "max_results": {
      "type": "integer",
      "minimum": 1,
      "maximum": 20
    }
  },
  "required": [
    "query"
  ]
}
```

## 5. Output Schema

```json
{
  "status": "success | needs_clarification | blocked | rejected | error",
  "data": {
    "results": [
      {
        "source_id": "string",
        "source_type": "doi | pmid | url | guideline",
        "title": "string?",
        "snippet": "string?",
        "score": 0.0,
        "locator": "string?"
      }
    ]
  },
  "events_emitted": [],
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
| `query` | string | Evidence search query. |
| `question_type` | string | Reason evidence is being requested. |
| `population_context` | string | Relevant population if known. |
| `intervention_or_exposure` | string | Relevant intervention or exposure if known. |
| `outcome` | string | Relevant outcome if known. |
| `max_results` | integer | Maximum number of evidence results to return. |

## 7. Responsibilities

### Required Responsibilities

- Retrieve relevant evidence candidates from the evidence RAG.
- Preserve source identifiers and locators.
- Return enough metadata for later bundle building.
- Keep user personalization separate from general evidence retrieval.

### Forbidden Responsibilities

- Must not update user state.
- Must not persist claims.
- Must not attach evidence to planning history.
- Must not fabricate sources.
- Must not treat retrieval score as final truth.

## 8. Validation Rules

- `query` must not be empty.
- `max_results` must be within allowed bounds.
- Returned sources must include stable source identifiers.
- No result must be fabricated when retrieval is empty.

## 9. Runtime Behavior

### Reads

- `EvidenceRAG`

### May Emit Events

- `None`

### Updates Projections

- `None`

### Internal Validators

- `query_validation`
- `retrieval_result_validation`
- `source_identifier_validation`

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

- `EvidenceRAG`
- `EvidenceBundleCandidate`

### Related Events

- `None`

### Related Projections

- `None`

## 12. Operational Notes

This tool only searches. Use `evidence.manage_support` to build or attach a stable evidence bundle.

## 13. Versioning

### Patch

Clarifies documentation without changing runtime behavior.

### Minor

Adds optional input fields, optional output fields, or compatible validation behavior.

### Major

Changes required inputs, tool meaning, emitted events, safety behavior, or output semantics.
