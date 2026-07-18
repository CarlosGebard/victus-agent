---
id: VICTUS-CONTRACT-FUTURE-TOOLS
title: Future Tool Capability Backlog
status: draft
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Future Tool Capability Backlog

New tools must follow the same tool-first layout as active tools.

```text
src/tools/<tool>/
  tool.py
  contract.py
  policy.py
  actions.py or actions/
  README.md
```

Folder responsibilities:

- `tool.py` is the public implementation entrypoint.
- `contract.py` defines capability-specific input and result data.
- `policy.py` owns deterministic classification or routing policy.
- `actions.py` or `actions/` contains only cohesive, effective operations.
- `README.md` documents effects, rules, and functional examples.

Each new tool capability must start classify-only unless its target event payload, validation
policy, safety policy, and idempotency rules are documented and implemented.

## Implemented V1 Tool Surface

The initial V1 surface is active in `src/tools/catalog.py`:

- `planning`
- `feedback`
- `evidence_answer`
- `clarification`
- `confirmation`

## Remaining Capability Backlog

### `planning`

Implemented V1 actions exist, but these capabilities remain pending:

- Define plan artifact validation policy.
- Add graph orchestration for plan generation and revision flows.
- Add idempotency strategy for repeated plan saves.

### `feedback`

Implemented V1 actions exist, but these capabilities remain pending:

- Define target reference rules for `target_id`.
- Add projection or query path for unresolved feedback.

### `evidence_answer`

Implemented V1 actions exist, but these capabilities remain pending:

- Define evidence source registry.
- Define grounding and citation validation rules.
- Add retrieval/ranking integration.

### `clarification`

Implemented V1 actions exist, but these capabilities remain pending:

- Define pending interaction lookup and resume semantics.
- Add graph resume orchestration.

### `confirmation`

Implemented V1 actions exist, but these capabilities remain pending:

- Define confirmation timeout and idempotency rules.
- Add side-effect resume semantics after accepted confirmation.
