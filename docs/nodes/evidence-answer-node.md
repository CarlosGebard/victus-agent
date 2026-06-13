---

## id: VICTUS-NODE-EVIDENCE-ANSWER  
contract_id: victus.node.evidence_answer  
title: Evidence Answer Node  
status: draft  
version: v1  
owner: victus-agent-runtime  
domain: orchestration  
contract_type: orchestration_node  
stability: experimental  
updated_at: 2026-06-12
---
# Evidence Answer Node

## 1. Purpose

Handles user questions that require scientific, guideline, or evidence-backed explanation.

This node uses the evidence RAG to support answers. It does not modify user state, create plans, or log personal events.

## 2. Identity

### Identity Rules

- Canonical identifier: `victus.node.evidence_answer`
    
- One execution belongs to one evidence-oriented user request.
    
- Node identity must not be confused with `claim_id`, `bundle_id`, or source identifiers.
    

### Ownership

Owned by `victus-agent-runtime`.

## 3. Input

```ts
type EvidenceAnswerInput = {
  user_id: string
  normalized_text: string
  user_context_digest?: string
  evidence_query?: string
  personalization_allowed: boolean
}
```

## 4. Output

```ts
type EvidenceAnswerOutput = {
  answer_mode:
    | "general_evidence_answer"
    | "personalized_explanation"
    | "recommendation_support"
    | "needs_clarification"
    | "reroute"

  evidence_required: boolean
  claim_recording_required: boolean
  reason: string
}
```

## 5. Responsibilities

### Required Responsibilities

- Detect whether the user asks for evidence, explanation, or recommendation support.
    
- Search evidence when the answer depends on scientific support.
    
- Separate general scientific answers from personalized recommendations.
    
- Use user context only when personalization is required.
    
- Record claims and evidence links only when the answer supports a system recommendation or plan decision.
    

### Forbidden Responsibilities

- Must not log user data.
    
- Must not update goals.
    
- Must not create or revise plans.
    
- Must not treat RAG results as user memory.
    
- Must not cite evidence that was not retrieved or attached.
    
- Must not over-personalize general scientific questions.
    

## 6. Validation Rules

- `answer_mode` must be one allowed value.
    
- Evidence-backed claims must be supported by retrieved sources.
    
- Personalized explanations must use current user context.
    
- Unsupported claims must be marked as uncertain or avoided.
    
- Medical-risk questions must be rerouted to safety handling.
    

## 7. Lifecycle

### Created

Created when the router selects evidence-oriented intent.

### Updated

Node decisions are immutable.

### Superseded

May be superseded by safety triage, clarification, or plan intent if the user asks for action instead of evidence.

## 8. Relationships

### Upstream Contracts

- `IntentRouterNode`
    
- `SafetyPreCheckNode`
    
- `EvidenceRAG`
    
- `UserProfile`
    
- `ConstraintProjection`
    
- `NutritionStatus`
    
- `PlanningHistory`
    

### Downstream Contracts

- `ResponseComposerNode`
    
- `ClarificationNode`
    
- `SafetyTriageNode`
    

### Visible Tools

- `evidence.search`
    
- `context.get_user_context_snapshot`
    

### Internal Tools

- `evidence.build_bundle`
    
- `evidence.attach_bundle_to_claim`
    
- `explanation.record_claim`
    

### Related Events

- `claim.generated`
    
- `evidence.cited`
    

## 9. Operational Notes

This node should not expose the full evidence corpus to the model.

The model should receive retrieved evidence bundles, not raw uncontrolled search space.

## 10. Versioning

### Patch

Clarifies evidence answer behavior.

### Minor

Adds a new answer mode or evidence tool.

### Major

Changes when evidence is required or changes claim recording semantics.