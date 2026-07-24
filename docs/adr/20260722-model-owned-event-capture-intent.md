---
id: ADR-20260722-MODEL-OWNED-EVENT-CAPTURE-INTENT
title: Model-Owned Event Capture Intent
status: accepted
updated_at: 2026-07-22
owners:
  - victus-agent-runtime
related_docs:
  - ../../src/tools/event_capture/contract.py
  - ../../src/tools/event_capture/policy.py
  - ../../src/tools/event_capture/tool.py
tags:
  - event-capture
  - langgraph
  - tool-contracts
---

# Context

`event_capture` used regex rules inside tool execution to decide whether a user message represented
a meal, biometric, lifestyle metric, symptom, edit, delete, or reroute. Real usage such as "logear mi
comida" showed that this duplicated and weakened the LLM's semantic decision, especially for
multilingual and colloquial input.

# Decision

The LLM owns semantic event classification. `event_capture` now accepts structured
`capture_action` and `extracted` fields from the model and no longer uses regex to validate capture
intent from `normalized_text`.

The tool remains responsible for contract validation, missing-field clarification, event payload
invariants, and safety guardrails. Missing or incomplete structured event input returns
`needs_clarification` instead of a rejected reroute. High-risk symptom detection remains a safety
guardrail, not an intent classifier.

# Consequences

- Multilingual and natural user phrasing no longer fails because a local regex missed the wording.
- Tool-call quality depends more directly on the schema and catalog description exposed to the LLM.
- Future work should strengthen clarification resume so short answers like "si" or "exacto" resolve
  against a stored pending action instead of being treated as standalone text.
