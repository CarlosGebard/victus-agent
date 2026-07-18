---
id: VICTUS-CONTRACT-TOOL-PROFILE-UPDATE
title: Profile Update Tool
status: current
version: v1
updated_at: 2026-07-18
owners:
  - victus-agent-runtime
---

# Profile Update Tool

Public MCP name: `profile_update`.

Code: `src/tools/profile/`.

Implemented persistent actions:

- `add_restriction` -> `restriction.added` for non-safety-blocked decisions
- `update_preference` -> `preference.updated`

Classify-only actions:

- `update_restriction`
- `remove_restriction`
- `remove_preference`
- `needs_clarification`
- `reroute`
