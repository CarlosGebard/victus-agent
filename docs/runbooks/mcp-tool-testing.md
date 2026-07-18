---
id: VICTUS-RUNBOOK-MCP-TOOL-TESTING
title: MCP Tool Testing
status: current
updated_at: 2026-07-18
owners:
  - victus-agent-runtime
---

# Purpose

Validate real tool discovery, invocation, safety, interaction results, authentication, and event
persistence through the MCP adapters. These are manual boundary checks; do not add automated tests
unless they expose a critical regression not covered by the minimal suite.

# Prerequisites

```bash
uv sync --extra test
uv run --extra test victus check
```

For persisted events:

```bash
docker compose up -d postgres
export DATABASE_URL=postgresql+psycopg://victus:postgres@localhost:5432/victus_agent
uv run victus db-upgrade
```

Without `DATABASE_URL`, tools still execute but `events_emitted` remains empty.

# Stdio MCP

Start the server through an MCP client. With Codex:

```bash
codex mcp add victus-agent -- uv run victus-mcp
codex mcp list
```

Alternatively, start MCP Inspector:

```bash
npx @modelcontextprotocol/inspector uv run victus-mcp
```

In the client, verify discovery contains `event_capture`, `profile_update`, `planning`, `feedback`,
`evidence_answer`, `clarification`, `confirmation`, and `recuperar_perfil`.

# HTTP MCP

```bash
uv run victus-mcp-http
curl http://localhost:8765/health
```

Connect the MCP client or Inspector to:

```text
http://localhost:8765/mcp
```

Expected health fields include `status=ok` and `transport=streamable_http`.

# Critical Invocations

Invoke these through the connected MCP client.

Successful capture:

```json
{
  "name": "event_capture",
  "arguments": {"user_id": "mcp-smoke-user", "normalized_text": "hoy comi arroz"}
}
```

Expected: `status=success`, `data.capture_action=log_meal`, and one `meal.logged` reference when the
database is enabled.

Safety block:

```json
{
  "name": "event_capture",
  "arguments": {"user_id": "mcp-smoke-user", "normalized_text": "me quiero suicidar"}
}
```

Expected: `status=blocked`, `safety.status=blocked`, and no emitted event.

Interaction continuation:

```json
{
  "name": "clarification",
  "arguments": {
    "user_id": "mcp-smoke-user",
    "action": "request",
    "missing_fields": ["time"],
    "question": "A que hora fue?"
  }
}
```

Expected: `status=needs_clarification` with a `clarification.requested` event when persistence is
enabled.

# Authenticated Profile

```bash
BACKEND_API_URL=http://localhost:8000 uv run victus login
```

Then invoke `recuperar_perfil` with `{}`. Expected: `status=success` and profile data from `/me`.
Missing or expired authentication must return structured login guidance; tokens must never appear
in logs or results.

# Persistence Check

After a successful mutating invocation:

```bash
docker compose exec -T postgres psql -U victus -d victus_agent \
  -c "SELECT event_type, user_id, event_seq FROM user_events WHERE user_id = 'mcp-smoke-user' ORDER BY event_seq DESC LIMIT 5;"
```

Verify the expected event type exists once, the user matches, and the MCP result reference matches
the stored sequence. Repeating the same invocation must not create a second event with the same
idempotency key.

# Exit Criteria

- Both transports expose the catalog without adapter-specific tool definitions.
- Successful, blocked, and interaction results use the same `ToolResult` shape.
- Safety-blocked calls persist nothing.
- Authenticated reads never expose credentials.
- Persisted event references match PostgreSQL.
