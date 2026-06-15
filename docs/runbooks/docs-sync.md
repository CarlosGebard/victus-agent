---
id: VICTUS-RUNBOOK-DOCS-SYNC
title: Docs Sync Runbook
status: draft
updated_at: 2026-06-14
owners:
  - victus-agent-runtime
---

# Docs Sync Runbook

## Purpose

Keep repository documentation synchronized with the central docs repository:

```text
https://github.com/CarlosGebard/victus-docs
```

## Publish Repository Docs

On pushes to `main`, `.github/workflows/sync-docs.yml` copies:

```text
README.md
docs/**
```

into:

```text
CarlosGebard/victus-docs:repos/victus-agent
```

Required secret:

```text
SYNC_DOCS
```

The token must have push permission to `CarlosGebard/victus-docs`.

## Import Fundamental Contracts

Local command:

```bash
uv run contracts list
uv run contracts sync
uv run contracts validate
```

Destination:

```text
docs/contracts/fundamental/
```

Lockfile:

```text
docs/contracts/fundamental/contracts.lock.json
```

Do not edit Markdown files under `docs/contracts/fundamental/` by hand. Update them in `victus-docs`, then run `uv run contracts sync` here and commit the synchronized files plus lockfile.

## Validation

Before merging docs sync changes:

```bash
uv run contracts validate
uv run --extra test victus check
```
