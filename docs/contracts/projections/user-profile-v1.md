---
id: VICTUS-CONTRACT-PROJECTION-USER-PROFILE-V1
title: User Profile Projection V1
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# User Profile Projection V1

Implemented in:

- `src/domain/projections/models/user_profile.py`
- `src/domain/projections/projectors/user_profile.py`

Consumes:

- `restriction.added`
- `preference.updated`
- `goal.set`
- `goal.adjusted`
