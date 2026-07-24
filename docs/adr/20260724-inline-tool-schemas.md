---
id: ADR-20260724-INLINE-TOOL-SCHEMAS
title: Public Tool Schemas Are Inline And Audit-Readable
status: accepted
updated_at: 2026-07-24
owners:
  - victus-agent-runtime
tags:
  - tools
  - contracts
  - observability
---

# Context

Victus tool schemas are inspected in LLM requests and Phoenix traces. Schemas generated directly
from Pydantic may use `$defs` and `$ref`, which are valid JSON Schema but make the active tool
contract harder to audit during runtime debugging.

The active tool surface is intentionally being reduced and rebuilt from simple tools toward more
complex tools. The first active tool is `event_capture` for food and beverage logging.

# Decision

All public tool schemas sent to LLM providers, MCP clients, CLI discovery, and traces must be
published inline. Nested object fields must appear where they are used, for example
`items.items.properties.name`, `items.items.properties.quantity`, and
`items.items.properties.unit`, instead of being hidden behind `$defs` and `$ref`.

Tool schemas must prefer:

- small top-level argument objects
- explicit `properties`
- explicit `required`
- `additionalProperties: false`
- stable, domain-level field names
- human-readable descriptions that explain when to use and when not to use the tool

For food logging, each item requires `name`, `quantity`, and `unit` in the public schema. Missing or
unknown quantity data remains a clarification case at the policy layer; flows may accept `null` for
clarification when that is needed to avoid recording incomplete food data.

# Tradeoffs

Inline schemas are more verbose than `$defs` schemas, but they are easier to inspect in traces and
less ambiguous for humans auditing the active tool contract.

Keeping clarification behavior in policy means the public schema can communicate required business
data without turning every incomplete user utterance into a low-level validation failure.

# Alternatives Considered

Keep generated `$defs` schemas unchanged. This was rejected because it obscures the actual nested
arguments during tool audits.

Make every business-required field strictly non-null at schema validation. This was rejected for
clarification workflows because the runtime must be able to ask for missing quantity details instead
of silently failing before policy execution.

# Consequences

Future tools must expose audit-readable inline schemas. If a model library generates `$defs`, the
tool catalog or adapter must inline those references before publication.

Contract tests should assert the public schema shape, not only the Pydantic model shape.

# Related Documents

- `docs/Tools.md`
- `src/tools/catalog.py`
- `src/tools/event_capture/contract.py`
