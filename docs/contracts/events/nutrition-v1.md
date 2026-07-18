---
id: VICTUS-CONTRACT-EVENTS-NUTRITION-V1
title: Nutrition Events V1
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Nutrition Events V1

Implemented in `src/domain/events/nutrition.py`.

Active event types:

- `meal.logged`
- `meal.edited`
- `meal.deleted`

Currently emitted by tools:

- `event_capture.actions.log_meal` emits `meal.logged`.

Not yet emitted:

- `meal.edited` requires stable meal reference resolution.
- `meal.deleted` requires stable meal reference resolution and confirmation.
