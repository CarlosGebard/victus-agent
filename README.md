# victus-agent

`victus-agent` is the runtime repository for the first production-oriented version of the Victus Lifestyle Agent.

The repository owns the agent spine: authenticated account context, LangGraph orchestration, safety prechecks, embedding-assisted intent routing, typed tool execution, immutable user events, PostgreSQL projections, planning artifacts, and evidence-facing adapter boundaries.

This repository does not try to solve the full nutrition science problem in V1. It provides the stable runtime foundation required to test, learn, and iterate safely.

## Current Status

Status: `draft / V1 implementation-ready documentation`

The expected next step is implementation by Codex or another coding agent using the four root documents as the source of truth:

```text
docs/000-SYSTEM-CONTEXT.md   -> why the repository exists and what it owns
docs/100-ARCHITECTURE.md     -> how the system is shaped and how components interact
docs/200-OPERATIONS.md       -> how to run, validate, debug, and recover the runtime
docs/300-CONTRACTS.md        -> stable schemas, events, tables, states, and tool boundaries
```

## V1 Scope

V1 domain: nutrition and lifestyle support.

The agent handles meals, biometrics, symptoms, restrictions, preferences, goals, diet-plan generation/revision, weekly nutrition review, and evidence questions. Training or workout details may appear only as context for nutrition decisions or safety triage; V1 does not generate workout programs.

V1 should implement the minimum runtime capable of:

- resolving account and user context from an authenticated request
- running a LangGraph-based agent turn
- applying safety prechecks before routing and mutation
- routing user intent with embeddings plus deterministic thresholds
- executing typed backend tools
- appending immutable domain events
- rebuilding projections from events
- storing planning sessions, revisions, and artifacts
- returning traceable responses with event references, route decisions, warnings, and tool results

## Quick Start

These commands define the expected developer interface. If the repository is empty, Codex should create these targets during the first implementation pass.

```bash
cp .env.example .env
make install
make db-up
make db-migrate
make seed-router
make dev
```

Run the minimum validation suite:

```bash
uv run --extra test victus check
```

Useful validation commands:

```bash
uv run --extra test victus test
uv run --extra test victus test tests/routing
uv run --extra test victus compile
uv run --extra test victus check
uv run victus db-upgrade
uv run victus db-current
uv run victus smoke-event-store
uv run victus smoke-projections
uv run victus smoke-projectors
uv run victus projections-rebuild local-smoke-user
```

## Documentation

Read in this order:

1. [`docs/000-SYSTEM-CONTEXT.md`](docs/000-SYSTEM-CONTEXT.md)
2. [`docs/100-ARCHITECTURE.md`](docs/100-ARCHITECTURE.md)
3. [`docs/300-CONTRACTS.md`](docs/300-CONTRACTS.md)
4. [`docs/200-OPERATIONS.md`](docs/200-OPERATIONS.md)

## Repository Responsibilities

This repository owns:

- agent runtime orchestration
- account/user context resolution for the agent
- embedding-assisted intent routing
- safety routing and blocking behavior
- typed tool handlers
- immutable event storage
- projection rebuild logic
- planning session and artifact persistence
- runtime traces and operational validation
- local LangGraph visualization through `uv run victus graph-dev`

This repository does not own:

- infrastructure provisioning
- identity provider implementation
- full food database normalization
- scientific paper processing pipelines
- final mobile application UI
- external wearable provider behavior
- medical diagnosis or treatment decisions

## Non-Negotiable Rule

The language model is never the source of truth.

The source of truth is the event store. Projections are derived read models. LangGraph checkpoints are orchestration state only. Tools validate and execute commands. Safety policy decides whether an action is allowed. Evidence supports explanations but does not override safety or user constraints.
