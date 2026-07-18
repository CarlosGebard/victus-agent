---
id: VICTUS-CONTRACT-EVENTS-EVIDENCE-V1
title: Evidence Events V1
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Evidence Events V1

Implemented in `src/domain/events/evidence.py`.

Active event types:

- `claim.generated`
- `evidence.cited`

Currently emitted by tools:

- `evidence_answer.actions.generate_claim` emits `claim.generated`.
- `evidence_answer.actions.cite` emits `evidence.cited`.
