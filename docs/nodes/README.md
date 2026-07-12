# Nodes

This directory intentionally keeps only a compact node map.

Detailed node contracts were removed because they described future behavior more than current
runtime behavior. Use the code and root architecture document as the active source of truth.

## Implemented Graph Nodes

Implemented in `src/agent/`:

- `safety_precheck`
- `normalize_request`
- `context_bootstrap`
- `self_harm_response`
- `tool_registry`
- `compose_response`
- `summarize_after_response`

## Implemented Tool Classifiers

Implemented under `src/agent/nodes/` and exposed through `src/application/tools/`:

- `event_capture`
- `profile_update`

Current tool classifiers validate and classify. They do not persist events directly.
