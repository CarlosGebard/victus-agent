---
id: VICTUS-CONTRACT-TOOL-EVENT-CAPTURE
title: Event Capture Tool
status: current
version: v1
updated_at: 2026-07-18
owners:
  - victus-agent-runtime
---

# Event Capture Tool

Public MCP name: `event_capture`.

Code: `src/tools/event_capture/`.

Implemented persistent actions:

- `log_meal` -> `meal.logged`
- `log_biometrics` -> `biometrics.logged`
- `log_lifestyle_metric` -> `lifestyle_metric.logged`
- `log_symptom` -> `symptom.logged` for non-safety-blocked symptoms

Classify-only actions:

- `edit_meal`
- `delete_meal`
- `needs_clarification`
- `reroute`

`capture_action` is the canonical decision. Redundant skill, entity, and candidate-event fields are
not part of the result data.
