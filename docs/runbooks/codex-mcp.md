---
id: VICTUS-RUNBOOK-CODEX-MCP
title: Codex MCP Connection
status: current
updated_at: 2026-07-16
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
uv run victus mcp-call event_capture '{"user_id":"local-smoke-user","normalized_text":"hoy comi arroz"}'
BACKEND_API_URL=http://localhost:8000 uv run victus login
BACKEND_API_URL=http://localhost:8000/v1 uv run victus mcp-call recuperar_perfil '{}'
codex mcp add victus-agent -- uv run victus-mcp
codex mcp list
```

The active exposed tools are:

```text
event_capture
profile_update
recuperar_perfil
```

`victus login` uses browser OAuth PKCE and saves `access_token`, `refresh_token`, `expires_at`,
`token_type`, and `scope` in `~/.victus/session.json`. `recuperar_perfil` relays the current access
token to the backend `/me` endpoint, refreshing first when possible.

## Rollback

Remove the local MCP server registration:

```bash
codex mcp remove victus-agent
```
