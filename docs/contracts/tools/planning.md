---
id: VICTUS-CONTRACT-TOOL-PLANNING
title: Planning Tool
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Planning Tool

Public MCP name: `planning`.

Code: `src/tools/planning/`.

Implemented persistent actions:

- `planning.set_goal` -> `goal.set`
- `planning.adjust_goal` -> `goal.adjusted`
- `planning.start_session` -> `plan.session_started`
- `planning.create_revision` -> `plan.revision_created`
- `planning.save_artifact` -> `plan.artifact_saved`
- `planning.end_session` -> `plan.session_ended`

The tool expects structured action input. It does not generate plan content by itself.
