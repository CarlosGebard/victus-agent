---
id: VICTUS-CONTRACT-TOOL-EVIDENCE-ANSWER
title: Evidence Answer Tool
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Evidence Answer Tool

Public MCP name: `evidence_answer`.

Code: `src/tools/evidence/`.

Implemented persistent actions:

- `evidence.generate_claim` -> `claim.generated`
- `evidence.cite` -> `evidence.cited`

The tool records claims and citations. It does not retrieve or rank evidence by itself.
