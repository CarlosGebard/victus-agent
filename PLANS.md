# Fullstack manual-meal event import contract

## Task classification

Documentation and public event-contract change.

## Goal

Define the rules required for the fullstack to deliver manually logged meals to the agent as
idempotent, immutable `meal.logged` events that rebuild existing projections correctly.

## Scope

- Document the producer/consumer ownership boundary and the required inbound data.
- State validation, identity, idempotency, ordering, correction, and projection rules.
- Link the active-events guide to the new contract.

## Assumptions

- The transport is intentionally undecided.
- The fullstack remains authoritative for its user and nutrition-catalog records.
- The agent remains authoritative for its local event store and projections.

## Steps

1. Completed: add the versioned integration contract under `docs/contracts/`.
2. Completed: add a concise reference from `docs/Events.md`.
3. Completed: verify the documented envelope and payload against the current event models and
   registry.

## Validation

- Review the diff for consistency with `src/domain/events/envelope.py`,
  `src/domain/events/nutrition.py`, and `docs/contracts/event-registry.yml`.
- Run `uv run --extra test victus check`.

## Risks

- The shown fullstack schema has no meal-level grouping identifier. The producer must provide one
  before it can emit a multi-item meal without losing grouping semantics.
