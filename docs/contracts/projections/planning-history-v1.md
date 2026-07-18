---
id: VICTUS-CONTRACT-PROJECTION-PLANNING-HISTORY-V1
title: Planning History Projection V1
status: draft
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Planning History Projection V1

Implemented in:

- `src/domain/projections/models/planning_history.py`
- `src/domain/projections/projectors/planning_history.py`

Consumes:

- `goal.set`
- `goal.adjusted`
- `plan.session_started`
- `plan.revision_created`
- `plan.artifact_saved`
- `plan.session_ended`
- `feedback.recorded`
- `feedback.resolved`
