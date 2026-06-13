---
id: VICTUS-WORKFLOW-V1-RUNTIME-FLOW
title: V1 Runtime Flow
status: draft
version: v1
owner: victus-agent-runtime
updated_at: 2026-06-12
---
# V1 Runtime Flow

```text
receive user input
  -> normalize request
  -> load lightweight context
  -> safety precheck
  -> if blocked: safety response
  -> route intent
  -> load node-specific projections
  -> expose node-specific tools
  -> call backend tool handler
  -> append events if needed
  -> run projectors affected by emitted events
  -> compose response
  -> return route, response, event refs, warnings
```

## Rule

Every state mutation must pass through this chain:

```text
tool input validation
  -> safety/policy validation when needed
  -> event append
  -> projector update
  -> response composition
```

No node should mutate projections directly.
