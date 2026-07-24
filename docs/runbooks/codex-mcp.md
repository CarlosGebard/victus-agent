---
id: VICTUS-RUNBOOK-CODEX-MCP
title: Codex MCP Connection
status: current
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Codex MCP Connection

## Purpose

Connect Codex to the local Victus MCP stdio server so Codex can list and call the active Victus
tools.

## Commands

From the repository root:

```bash
uv run victus mcp-list-tools
uv run victus mcp-call event_capture '{"items":[{"name":"arroz","quantity":100,"unit":"g"}]}'
DATABASE_URL=postgresql+psycopg://victus:victus@localhost:5432/victus \
  uv run victus mcp-call profile_update '{"user_id":"local-smoke-user","normalized_text":"soy intolerante a la lactosa"}'
BACKEND_API_URL=http://localhost:8000 uv run victus login
BACKEND_API_URL=http://localhost:8000/v1 uv run victus mcp-call recuperar_perfil '{}'
codex mcp add victus-agent -- uv run victus-mcp
codex mcp list
```

The active exposed tools are:

```text
event_capture
profile_update
planning
feedback
evidence_answer
clarification
confirmation
recuperar_perfil
```

`profile_update` can emit non-safety-blocked `restriction.added` and `preference.updated` events
for supported actions when `DATABASE_URL` points at a migrated event store. Without `DATABASE_URL`,
local MCP calls still classify and return the decision envelope without appended events.

`event_capture` follows the same pattern for supported meal capture events and emits
`meal.logged`.

`planning`, `feedback`, `evidence_answer`, `clarification`, and `confirmation` expose structured
action inputs and can append their contracted V1 events when `DATABASE_URL` points at a migrated
event store.

`victus login` uses browser OAuth PKCE and saves `access_token`, `refresh_token`, `expires_at`,
`token_type`, and `scope` in `~/.victus/session.json`. `recuperar_perfil` relays the current access
token to the backend `/me` endpoint, refreshing first when possible.

## Rollback

Remove the local MCP server registration:

```bash
codex mcp remove victus-agent
```
