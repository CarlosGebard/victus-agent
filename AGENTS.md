# AGENTS.md

Operational rules for coding agents working in this repository.

The goal is simple:
make correct, minimal, maintainable changes without generating noise.

---

# Core Principles

- Think before coding.
- Prefer simple solutions.
- Make surgical changes.
- Do not over-engineer.
- Do not generate unnecessary files.
- Do not silently assume.
- Match existing repository patterns.
- Stop and ask when uncertain.

---

# Repository Philosophy

This repository values:

- minimalism
- operational clarity
- stable contracts
- low-noise collaboration

Avoid unnecessary complexity in:

- code
- documentation
- testing
- planning
- abstractions

---

# Read Before Changing

Read only what is necessary.

Typical order:

1. `README.md`
2. `docs/000-SYSTEM-CONTEXT.md`
3. `docs/100-ARCHITECTURE.md`
4. `docs/200-OPERATIONS.md`
5. `docs/400-CONTRACTS.md`

Do not recursively scan the repository unless required.

---

# Behavioral Rules

## Think Before Coding

- State assumptions explicitly.
- Surface ambiguities.
- Mention simpler alternatives.
- Ask instead of guessing.

If unclear: stop and ask.

---

## Simplicity First

Implement the smallest correct solution.

Do not add:

- speculative abstractions
- unnecessary configuration
- generic utilities
- extensibility without need
- premature optimization

If the solution feels overcomplicated, simplify it.

---

## Surgical Changes

Touch only what is required.

Do not:

- refactor unrelated code
- reformat unrelated files
- rename unrelated symbols
- reorganize structure without reason

Every changed line should trace to the request.

Remove only unused code introduced by YOUR changes.

---

## Goal-Driven Execution

Turn requests into verifiable goals.

Examples:

- bug fix → reproduce → fix → verify
- validation → failing case → pass
- refactor → preserve behavior

For non-trivial tasks:

1. state brief plan
2. define verification
3. execute incrementally

---

# Testing Rules

Testing must stay proportional.

Prefer:

- focused tests
- behavior verification
- existing test patterns

Avoid:

- massive test suites
- excessive mocking
- unnecessary frameworks

Do not introduce large testing infrastructure without permission.

---

# Documentation Rules

Documentation must stay minimal and useful.

Do not create:

- `TASKS.md`
- `TODO.md`
- `ROADMAP.md`
- `STATUS.md`
- temporary planning files

unless explicitly requested.

Tasks are managed outside the repository.

Only update documentation when changes affect:

- architecture
- operations
- contracts
- public APIs
- configuration
- workflows

Do not generate documentation noise.

---

# Contract Awareness

Treat these as contracts:

- APIs
- CLI interfaces
- schemas
- env vars
- event payloads
- storage layouts
- config structures

When modifying contracts:

- preserve compatibility when possible
- explicitly mention breaking changes

---

# Commands and Tooling

Do not invent commands.

Inspect existing:

- scripts
- Makefiles
- task runners
- CI workflows
- Docker flows

Prefer existing repository patterns.

Do not introduce tooling without justification.

---

# Security Rules

Never:

- hardcode secrets
- expose credentials
- print `.env`
- assume production access

Use existing secret management systems.

---
# Documentation Verification Before Commit

Before finishing a task or preparing a commit/push, verify whether the changes affect:

- architecture
- operations
- contracts
- public APIs
- configuration
- workflows
- repository structure

If documentation is affected:

- update the relevant documentation
OR
- explicitly state what should be updated and why

Do not silently leave documentation inconsistent with the codebase.

Do not generate unnecessary documentation updates for purely internal changes.

---

# Ask Before

Ask before:

- large refactors
- destructive operations
- architecture rewrites
- dependency changes
- public interface changes
- repository restructuring
- deleting files

When uncertain: ask.

---

# Success Criteria

Success means:

- smaller diffs
- simpler solutions
- clean repositories
- useful documentation
- predictable behavior
- maintainable systems
