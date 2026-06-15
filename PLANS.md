# Plan: Clean Architecture Source Layout

## Task classification

- refactor
- architecture
- documentation

## Goal

Reorder `src` into clearer Clean Architecture layers while preserving current runtime behavior.

Target shape:

```text
src/
  agent/                 # LangGraph orchestration
  application/           # ports, config, application services
    routing/
  domain/                # domain contracts and pure models
    events/
    projections/
    session_context/
    tools/
  infrastructure/        # adapters and persistence implementations
    db/
    llm/
    repositories/
  victus_cli/            # developer/runtime CLI
```

## Scope

- Move domain models out of root-level packages.
- Move routing under `application`.
- Move SQLAlchemy schema/engine and repositories under `infrastructure`.
- Update imports, packaging, docs, migrations, CLI, and tests.
- Keep compatibility behavior the same.

## Assumptions

- The repo is early enough to prefer the cleaner import paths now.
- No external package imports depend on the old root-level modules.
- This pass is structural; it should not change schemas, events, graph behavior, or router scoring.

## Non-goals

- Do not rewrite business logic.
- Do not add compatibility shims for old imports unless tests reveal a real need.
- Do not change database migrations.
- Do not add new dependencies.

## Steps

1. Move packages into layer-oriented directories.
2. Update imports mechanically.
3. Update packaging and docs references.
4. Run focused checks, then full validation.

## Validation

```bash
uv run --extra test victus check
```

## Risks

- Import path churn can break scripts if a reference is missed.
- Existing docs may mention old paths; update only architecture-relevant references.
