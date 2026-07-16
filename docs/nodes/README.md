# Nodes

This directory intentionally keeps only a compact node map.

Detailed node contracts were removed because they described future behavior more than current
runtime behavior. Use the code and root architecture document as the active source of truth.

## Active Graph Nodes

Currently wired into `src/agent/graph.py`:

- `normalize_request`
- `safety_precheck`
- `safety_blocked_response`
- `event_capture`

Allowed requests continue to `event_capture`. Blocked requests stop at `safety_blocked_response`
and expose no tools.

## Implemented Tool Classifiers

Implemented under `src/agent/nodes/` and exposed through `src/application/tools/`:

- `event_capture`
- `profile_update`

Current tool classifiers validate and classify. They do not persist events directly.
