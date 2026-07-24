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

# Agent Intent Selection With Codex

MCP Inspector validates discovery and direct invocation, but it does not test agent selection because
the operator chooses the tool. Use Codex as the MCP host to evaluate natural-language intent.

After adding the server, verify that Codex sees it:

```bash
codex mcp list
```

Run one isolated case non-interactively. Keep the sandbox read-only so the evaluation cannot edit the
repository; MCP tool side effects still depend on the configured server and database:

```bash
codex exec --ephemeral --json \
  "Do not edit files. Act as the Victus assistant. For mutating Victus tools, the current test user_id is mcp-smoke-user. Process this user message using the victus-agent MCP tools only when appropriate: Hoy comi arroz con pollo."
```

The JSONL stream includes MCP tool-call events. Verify the selected tool, arguments, result status,
and whether a tool call was correctly avoided. Use a new ephemeral execution for each independent
case so earlier conversation does not reveal the expected route.

Minimum intent matrix:

| User message | Expected selection | Important exclusion |
| --- | --- | --- |
| `Hoy comi arroz con pollo` | `event_capture` | Not `profile_update` |
| `Soy intolerante a la lactosa` | `profile_update` | Not `event_capture` |
| `Quiero bajar de peso durante tres meses` | `planning` | Not `profile_update` |
| `No me gusto el ultimo plan` | `feedback` | Do not revise the plan directly |
| `Muestrame mi perfil actual` | `recuperar_perfil` | No `user_id` argument |
| `Comi algo` | Clarification before capture | Do not persist an incomplete event |
| `Si, confirmalo` without pending context | No confirmation | No tool call |
| `Que puedes hacer?` | No mutating tool | No tool call |

For each product case, record the input, expected tool or abstention, forbidden tools, required
argument values, and expected result status. Test close paraphrases and ambiguous negative cases, not
only the canonical phrase.

## LiteLLM Selection-Only Evaluation

Use the existing LiteLLM proxy to run the versioned intent matrix without invoking tools or writing
events. Gemini credentials, rotation, and provider limits remain inside LiteLLM; Victus only receives
the proxy URL and proxy key.

```bash
export LITELLM_PROXY_API_BASE=http://localhost:4000/v1
export LITELLM_PROXY_API_KEY=<proxy-key>

uv run victus intent-eval --model litellm_proxy/gemini-flash-lite
```

Do not commit or print the proxy key. The evaluator sends the canonical MCP names, descriptions, and
JSON schemas to the model with `tool_choice=auto`. It reports selection, abstention, arguments, and
whether `normalized_text` preserved the exact user input. It never calls `ToolRuntime`, MCP, or
PostgreSQL.

Cases live in `ops/evals/mcp_intent_cases.json`. A successful run exits `0`; selection failures exit
`1`; invalid configuration or provider failures exit `2`.

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
  "arguments": {
    "items": [{"name": "arroz", "quantity": 100, "unit": "g"}]
  }
}
```

Expected: `status=success` and one `meal.logged` reference when the database is enabled.

Any argument other than `items` or `occurred_at_text` is rejected. A missing quantity or unit
returns a clarification request and does not emit an event.

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
- Natural-language intent cases select the expected tool or correctly abstain.
- Selected calls contain schema-valid arguments without inventing missing user facts.
