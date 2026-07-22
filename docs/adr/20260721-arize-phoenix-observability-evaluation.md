---
id: ADR-20260721-ARIZE-PHOENIX-OBSERVABILITY-EVALUATION
title: Arize Phoenix For Local Agent Observability And Evaluation
status: accepted
updated_at: 2026-07-21
owners:
  - victus-agent-runtime
related_docs:
  - ../../compose.yml
  - ../../ops/scripts/phoenix_intent_eval.py
tags:
  - phoenix
  - observability
  - opentelemetry
  - evaluation
  - langgraph
---

# Context

Victus needs a local workflow for inspecting complete agent executions and comparing model or prompt
changes against repeatable cases. The runtime already propagates request, conversation, user, and
tool trace identifiers, but its observable development path depended on optional LangSmith settings
and its intent evaluator only emitted a local JSON report.

The target must preserve the existing LangGraph, LiteLLM, tool runtime, and deterministic test
boundaries. Observability must remain optional: failure or absence of Phoenix must not prevent chat
from starting when tracing is disabled. Phoenix data is diagnostic and must not become domain truth,
conversation persistence, or agent memory.

# Decision

- Use self-hosted Arize Phoenix OSS for local trace inspection, datasets, and experiments.
- Run Phoenix as an independent Compose service backed by a dedicated persistent SQLite volume.
- Export OpenInference traces over OTLP/HTTP to the Phoenix service on internal port `6006`.
- Enable tracing only when `PHOENIX_TRACING_ENABLED=true`; keep it disabled by default.
- Auto-instrument LangGraph through `openinference-instrumentation-langchain`.
- Instrument the repository's `LiteLLMClient` boundary manually with OpenInference spans, preserving
  the installed LiteLLM version instead of installing the incompatible LiteLLM instrumentor.
- Correlate chat traces with authenticated user, conversation session, request, resume state, and
  graph version metadata.
- Reuse `ops/evals/mcp_intent_cases.json` and the existing deterministic `score_case()` function as
  the source and evaluator for Phoenix Experiments.
- Keep pytest and compile checks as the correctness gate. Phoenix experiments supplement them with
  model-level comparisons and trace inspection.

# Implementation

The optional `phoenix` dependency group contains:

- `arize-phoenix-client>=2,<3`
- `arize-phoenix-otel>=0.16,<1`
- `openinference-instrumentation-langchain>=0.1,<1`

`victus_platform.telemetry.phoenix` owns registration, shutdown, request context, LLM span creation,
safe scalar metadata, and token usage attributes. The HTTP application starts and flushes the tracer
through its lifespan. `LiteLLMClient` creates one LLM span per completion without adding prompt,
response, or secret values from that manual boundary.

The Compose service uses `arizephoenix/phoenix:version-19.0.0`, persists data in
`victus_phoenix_data`, and exposes the Phoenix HTTP UI and collector on host port `6007`. The
container continues to use its standard internal port `6006`. Port `6007` avoids conflicting with
another local Phoenix instance already using `6006`; it remains configurable through `PHOENIX_PORT`.

`victus phoenix-intent-eval` upserts stable dataset examples, runs the selection-only model task,
publishes the existing contract score as a code evaluation, and exits non-zero when an evaluation
fails. The initial dataset is named `victus-mcp-intent`.

# Local startup

Start Phoenix and verify its health:

```bash
docker compose up -d phoenix
docker compose ps phoenix
curl --fail http://localhost:6007/healthz
```

Open the UI at `http://localhost:6007`.

Start chat with trace export enabled:

```bash
PHOENIX_TRACING_ENABLED=true docker compose up -d --build chat
```

The containerized chat service sends traces to `http://phoenix:6006`. A process running directly on
the host instead uses `http://localhost:6007` for both Phoenix endpoints.

Run a small experiment after configuring the existing LiteLLM proxy credentials:

```bash
PHOENIX_BASE_URL=http://localhost:6007 \
PHOENIX_COLLECTOR_ENDPOINT=http://localhost:6007 \
PHOENIX_TRACING_ENABLED=true \
uv run --extra phoenix victus phoenix-intent-eval --dry-run 3
```

Remove `--dry-run 3` to execute the complete dataset. `LITELLM_PROXY_API_BASE` and its existing key
configuration must be available to the process; Phoenix does not replace the model gateway.

# Tradeoffs

Positive:

- Local traces expose graph execution, latency, failures, LLM usage, and tool flow in one UI.
- The current deterministic intent cases become comparable, versioned experiment inputs.
- Tracing stays opt-in and does not make chat availability depend on Phoenix health.
- Manual LiteLLM spans avoid downgrading or changing the existing model client.
- Phoenix storage remains isolated from PostgreSQL domain and LangGraph persistence.

Negative:

- The Docker image and Phoenix dependencies increase local download and build size.
- Manual LiteLLM instrumentation must be maintained as the LLM client contract evolves.
- Full LangGraph auto-instrumentation may capture conversational content; Phoenix therefore requires
  controlled access, synthetic evaluation inputs, and an explicit retention policy before broader
  use.
- Host and container endpoints differ (`localhost:6007` versus `phoenix:6006`).
- Model experiments remain dependent on a reachable, authenticated LiteLLM proxy.

# Alternatives considered

- Keep only LangSmith: rejected because the requested development and evaluation workflow is Phoenix
  and the current repository has no dataset/experiment integration through LangSmith.
- Replace deterministic tests with Phoenix evaluations: rejected because external model behavior is
  variable and cannot replace local contract, safety, and compilation checks.
- Install `openinference-instrumentation-litellm`: rejected for this implementation because its
  supported LiteLLM constraint conflicts with the repository's locked `litellm==1.88.1`.
- Downgrade LiteLLM: rejected because observability must not force an unrelated provider-client
  regression.
- Make chat depend on Phoenix health: rejected because optional diagnostics must not become a runtime
  availability dependency.
- Store Phoenix data in the Victus PostgreSQL database: rejected to preserve ownership and lifecycle
  isolation between diagnostics and product data.

# Consequences

- New runtime instrumentation must use the central telemetry boundary instead of registering another
  global OpenTelemetry provider.
- Future LLM clients require equivalent OpenInference attributes if they bypass `LiteLLMClient`.
- Changes to prompts, models, or tool descriptions can be compared using the same Phoenix dataset.
- Shared or non-local Phoenix deployments require authentication, retention, and sensitive-content
  controls before receiving real user traces.
- Phoenix datasets and traces remain disposable diagnostic artifacts; user events, projections,
  checkpoints, and Store documents retain their existing authority.

# Validation evidence

- Phoenix `19.0.0` started healthy through Compose on host port `6007`.
- The `victus-mcp-intent` dataset was created with eight stable examples.
- Phoenix received an OTLP smoke span named `smoke.phoenix` with token usage attributes.
- The Docker agent image built with the optional Phoenix dependency group.
- The repository validation completed with 20 passing tests, successful compilation, valid Compose
  configuration, a current lock file, and no diff whitespace errors.

# Related documents and modules

- [Compose stack](../../compose.yml)
- [Phoenix experiment runner](../../ops/scripts/phoenix_intent_eval.py)
- [Phoenix telemetry boundary](../../src/victus_platform/telemetry/phoenix.py)
- [LiteLLM client](../../src/victus_platform/llm/litellm_client.py)
- [HTTP chat adapter](../../src/adapters/http/app.py)
- [Intent evaluation cases](../../ops/evals/mcp_intent_cases.json)
- [LangGraph memory decision](20260718-langgraph-memory-persistence.md)
