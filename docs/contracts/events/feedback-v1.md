---
id: VICTUS-CONTRACT-EVENTS-FEEDBACK-V1
title: Feedback Events V1
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Feedback Events V1

Implemented in `src/domain/events/feedback.py`.

Active event types:

- `feedback.recorded`
- `feedback.resolved`

Currently emitted by tools:

- `feedback.actions.record` emits `feedback.recorded`.
- `feedback.actions.resolve` emits `feedback.resolved`.
