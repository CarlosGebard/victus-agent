---
id: VICTUS-CONTRACT-EVENTS-INTERACTION-V1
title: Interaction Events V1
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Interaction Events V1

Implemented in `src/domain/events/interaction.py`.

Active event types:

- `clarification.requested`
- `clarification.resolved`
- `confirmation.requested`
- `confirmation.resolved`

Currently emitted by tools:

- `clarification.actions.request` emits `clarification.requested`.
- `clarification.actions.resolve` emits `clarification.resolved`.
- `confirmation.actions.request` emits `confirmation.requested`.
- `confirmation.actions.resolve` emits `confirmation.resolved`.
