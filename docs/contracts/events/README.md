---
id: VICTUS-CONTRACT-EVENTS-README
title: Event Contracts
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Event Contracts

Domain events are immutable user history. They are the source of truth for profile, nutrition,
planning, feedback, interaction, safety, and evidence facts.

Code lives under `src/domain/events/`.

```text
base.py            shared contract base and common literals
envelope.py        UserEventEnvelope, EventActor, EventMetadata
refs.py            ToolEventRef
nutrition.py       meal events
health_metrics.py  biometrics, lifestyle metrics, symptoms
profile.py         restrictions and preferences
planning.py        goals, planning sessions, revisions, artifacts
feedback.py        feedback lifecycle
interaction.py     clarification lifecycle
safety.py          safety guard/action events
evidence.py        claims and citations
registry.py        DomainEventPayload union
models.py          compatibility export barrel
```

Rules:

- Events are append-only.
- Corrections must be represented by new events.
- Every persisted tool side effect must return a `ToolEventRef`.
- Event payloads must be Pydantic contract models.
- `models.py` exists only as a compatibility export barrel; new code should import from the
  domain-specific event module.

The database-level event registry remains in `docs/contracts/events/event-registry.yml` because
schema checks read it directly.
