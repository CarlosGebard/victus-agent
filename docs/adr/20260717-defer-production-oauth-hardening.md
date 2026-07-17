---
id: ADR-20260717-DEFER-PRODUCTION-OAUTH-HARDENING
title: Defer Production OAuth Hardening
status: accepted
date: 2026-07-17
owners:
  - victus-agent-runtime
---

# Context

`victus-agent` now supports local OAuth Authorization Code + PKCE for `victus login`, stores the
resulting session in `~/.victus/session.json`, refreshes access tokens when possible, and relays the
access token through the MCP tool boundary.

This is sufficient for local development and integration testing with the decoupled web backend,
but it is not the final production-grade secret-handling model.

# Decision

Keep the current PKCE implementation as the local/dev integration path.

Defer production hardening to a later version.

# Deferred Work

- Store tokens in the OS keychain/secret store instead of plain JSON.
- Add backend token revocation to `victus logout`.
- Validate refresh-token rotation and reuse detection end to end.
- Tighten callback hardening, issuer/audience expectations, and minimum scopes.
- Add production-specific security tests for local secret handling and session lifecycle.

# Consequences

The current implementation remains usable for local MCP/Codex integration.

Production distribution must not treat `~/.victus/session.json` as the final token storage design.
