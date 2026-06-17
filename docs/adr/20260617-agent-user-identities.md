# 20260617 Agent User Identities

## Context

The agent database is separate from the webapp database. Modeling `accounts`, `users`,
memberships, and connected accounts inside the agent DB made it look like this repository owned
the platform user system.

## Decision

Replace the agent-owned account/user tables with a single minimal table:
`agent_user_identities`.

The table stores the user as seen by the agent plus the external source reference:
`agent_user_id`, `external_system`, and `external_subject`.

## Consequences

- The webapp remains the source of truth for platform users and permissions.
- The agent DB stores only the identity bridge needed for events, projections, and runtime state.
- Authorization beyond active identity status is delegated to the external caller for now.
