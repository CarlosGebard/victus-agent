---
id: VICTUS-CONTRACT-EVENTS-PLANNING-V1
title: Planning Events V1
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Planning Events V1

Implemented in `src/domain/events/planning.py`.

Active event types:

- `goal.set`
- `goal.adjusted`
- `plan.session_started`
- `plan.revision_created`
- `plan.artifact_saved`
- `plan.session_ended`

Currently emitted by tools:

- `planning.actions.set_goal` emits `goal.set`.
- `planning.actions.adjust_goal` emits `goal.adjusted`.
- `planning.actions.start_session` emits `plan.session_started`.
- `planning.actions.create_revision` emits `plan.revision_created`.
- `planning.actions.save_artifact` emits `plan.artifact_saved`.
- `planning.actions.end_session` emits `plan.session_ended`.
