---
id: VICTUS-CONTRACT-PROJECTIONS-README
title: Projection Contracts
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Projection Contracts

Projections are rebuildable read models derived from immutable events.

Code lives under `src/domain/projections/`.

```text
models/
  user_profile.py
  nutrition_status.py
  constraint.py
  planning_history.py
projectors/
  user_profile.py
  nutrition_status.py
  constraint.py
  planning_history.py
registry.py
```

Rules:

- Projections are not historical truth.
- Projectors must be idempotent.
- Projectors process events in `event_seq` order.
- Projection event ownership lives in `src/domain/projections/registry.py`.
- Compatibility barrels exist at `domain.projections.models` and `domain.projections.projectors`.
