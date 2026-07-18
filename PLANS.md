# Tool-first repository migration

## Goal

Make each Victus tool a vertical capability executed through one shared runtime by LangGraph, MCP,
CLI, and tests.

## Scope

- Add `tools`, `adapters`, `platform`, and `bootstrap` packages.
- Move tool contracts, policy, actions, and execution out of `domain/tools` and `application/tools`.
- Preserve public tool names and event/database contracts.
- Update tests, packaging, architecture, contracts, and operations documentation.

## Assumptions

- Existing working-tree changes are the migration baseline and must be preserved.
- Public tool names remain stable; internal result payloads may be simplified with contract tests.
- No new dependency is required.

## Steps

1. Add common contracts, catalog, and runtime.
2. Migrate `event_capture`, then the remaining capabilities and interaction mechanisms.
3. Add dependency bootstrap and technical platform packages.
4. Route LangGraph, MCP, and CLI through the shared runtime.
5. Remove superseded packages and compatibility paths.
6. Update documentation and validate the repository.

## Validation

- Minimal critical tool, adapter, domain, safety, and persistence tests.
- `uv run --extra test victus compile`
- `uv run --extra test victus check`

## Risks

- Contract drift while removing redundant decision fields.
- Duplicate execution or persistence paths during migration.
- Pre-existing missing `safety` package may block the full test suite.
