---
id: VICTUS-CONTRACT-TOOL-CONFIRMATION
title: Confirmation Tool
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Confirmation Tool

Public MCP name: `confirmation`.

Code: `src/tools/interaction/confirmation.py`.

Implemented persistent actions:

- `confirmation.request` -> `confirmation.requested`
- `confirmation.resolve` -> `confirmation.resolved`

This tool records explicit yes/no confirmation events. Applying the confirmed side effect remains
the responsibility of the tool or graph flow that requested confirmation.
