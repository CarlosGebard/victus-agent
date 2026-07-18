---
id: VICTUS-CONTRACT-TOOL-CLARIFICATION
title: Clarification Tool
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Clarification Tool

Public MCP name: `clarification`.

Code: `src/tools/interaction/clarification.py`.

Implemented persistent actions:

- `clarification.request` -> `clarification.requested`
- `clarification.resolve` -> `clarification.resolved`

This tool records interaction state events only. Resume orchestration is not implemented here.
