---
id: VICTUS-CONTRACT-EVENTS-PROFILE-V1
title: Profile Events V1
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Profile Events V1

Implemented in `src/domain/events/profile.py`.

Active event types:

- `restriction.added`
- `restriction.updated`
- `preference.updated`

Currently emitted by tools:

- `profile_update.actions.add_restriction` emits `restriction.added` for non-safety-blocked
  decisions.
- `profile_update.actions.update_preference` emits `preference.updated`.

Not yet emitted:

- `restriction.updated` requires stable restriction reference resolution.

Events referenced by current policy but not yet contracted:

- `restriction.removed`
- `preference.removed`
- `profile.identity_updated`
