---
id: VICTUS-CONTRACT-TOOLS-README
title: Tool Contracts
status: current
version: v1
updated_at: 2026-07-18
owners:
  - victus-agent-runtime
---

# Tool Contracts

Public tool metadata and implementation bindings live in `src/tools/catalog.py`.

Tool internals live in `src/tools/<tool>/`:

```text
tool.py
contract.py
policy.py
actions.py or actions/
README.md
```

Active public tools:

- `event_capture`
- `profile_update`
- `planning`
- `feedback`
- `evidence_answer`
- `clarification`
- `confirmation`
- `recuperar_perfil`

Implemented tool contracts in this directory describe active behavior. Draft future-tool notes stay
in `docs/contracts/future-tools/README.md` until they are promoted into the registry.
