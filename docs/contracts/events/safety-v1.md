---
id: VICTUS-CONTRACT-EVENTS-SAFETY-V1
title: Safety Events V1
status: draft
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Safety Events V1

Implemented payload models live in `src/domain/events/safety.py`.

Planned event types:

- `safety.guard_triggered`
- `safety.action_blocked`

The current safety precheck writes graph state and response state; it does not append safety events.
