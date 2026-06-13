# Plan: LiteLLM Port and LangGraph Integration

## Task classification

- feature
- infra
- documentation
- contract change

## Goal

Integrate LiteLLM behind a clean architecture LLM port, then use that port as the only LLM access path for the upcoming LangGraph runtime.

The application layer must know only `LLMClient`, `LLMRequest`, and `LLMResponse`. LiteLLM must remain isolated in `src/infrastructure/llm/litellm_client.py`.

## Non-goals

- Do not implement full event store, projections, auth, or database migrations in this pass.
- Do not make LangGraph nodes mutate projections or persist events directly.
- Do not expose `.env` values, proxy keys, or Tailscale-private endpoint details in logs, tests, or docs.
- Do not keep provider-specific Gemini or LiteLLM calls inside graph nodes.
- Do not replace the router prototype with a database-backed pgvector router yet.

## Current state observations

- `pyproject.toml` includes runtime dependencies for LangGraph, LiteLLM, Pydantic, and PyYAML.
- Runtime code now has `src/application/`, `src/infrastructure/`, `src/agent/`, `src/events/`, `src/tools/`, and `src/projections/` packages.
- Local validation passes with `uv run --extra test victus check`.
- `config/router/*.yml` exists and is the current router config source.
- `docs/100-ARCHITECTURE.md` already states that the LLM is not the owner of identity, persisted state, side effects, or safety decisions.
- `docs/200-OPERATIONS.md` documents `LLM_PROVIDER` and `LLM_MODEL`, but not LiteLLM proxy variables.
- `docs/contracts/langgraph-state-v1.md` defines orchestration state; the current Python state is in `src/agent/state.py`.
- `dev/langgraph-viewer/src/agent.py` is the development visualization harness for the real graph, not a second runtime.
- `.env` is ignored and may contain private LiteLLM proxy credentials. Do not read or print it.

## Likely touch points

- `pyproject.toml`
- `uv.lock`
- `src/application/ports/llm.py`
- `src/infrastructure/llm/litellm_client.py`
- `src/infrastructure/llm/factory.py`
- `src/agent/`
- `config/runtime.yml` or `config/llm.yml`
- `tests/application/`
- `tests/infrastructure/llm/`
- `tests/agent/`
- `docs/100-ARCHITECTURE.md`
- `docs/200-OPERATIONS.md`
- `docs/implementation/010-build-order.md`
- `dev/langgraph-viewer/langgraph.json`
- `dev/langgraph-viewer/src/agent.py`

## Milestones

### 1. Establish clean architecture package boundaries

Purpose: create the package shape before adding runtime behavior.

Expected outcome:

- `src/application/ports/` contains stable application-facing protocols.
- `src/infrastructure/llm/` contains provider-specific implementation.
- `src/agent/` is reserved for LangGraph orchestration and graph composition.
- Existing `src/victus_routing/` stays intact while integration proceeds.

Likely touch points:

- `src/application/__init__.py`
- `src/application/ports/__init__.py`
- `src/infrastructure/__init__.py`
- `src/infrastructure/llm/__init__.py`
- `src/agent/__init__.py`

Validation commands:

```bash
uv run --extra test pytest
```

### 2. Add the LLM application port

Purpose: define the internal contract that application and graph code depend on.

Expected outcome:

- Add `LLMRequest`, `LLMResponse`, and `LLMClient` in `src/application/ports/llm.py`.
- Keep request metadata explicit through `operation` and `metadata`.
- Keep response text, raw provider payload, and usage separate.
- No LiteLLM import appears outside infrastructure tests or `src/infrastructure/llm/`.

Likely touch points:

- `src/application/ports/llm.py`
- `tests/application/test_llm_port.py`

Validation commands:

```bash
uv run --extra test pytest
rg -n "import litellm|from litellm" src tests
```

Expected `rg` result after this milestone:

- no production references yet

### 3. Add LiteLLM adapter and factory

Purpose: connect to the private LiteLLM proxy through an infrastructure adapter while preserving the application port.

Expected outcome:

- Add dependency `litellm>=1,<2`.
- Implement `LiteLLMClient` in `src/infrastructure/llm/litellm_client.py`.
- Implement `build_llm_client()` in `src/infrastructure/llm/factory.py`.
- Read only these env vars:
  - `LITELLM_PROXY_API_BASE`
  - `LITELLM_PROXY_API_KEY`
  - `LITELLM_KEY`
- Do not read or print `.env`.
- Unit tests mock the `litellm` module or adapter boundary; they must not call the private proxy.

Likely touch points:

- `pyproject.toml`
- `uv.lock`
- `src/infrastructure/llm/litellm_client.py`
- `src/infrastructure/llm/factory.py`
- `tests/infrastructure/llm/test_litellm_client.py`

Validation commands:

```bash
uv lock
uv run --extra test pytest
rg -n "LITELLM_PROXY_API_KEY|LITELLM_KEY" src docs tests
```

Security check:

- `rg` must show variable names only, never secret values.

### 4. Add runtime LLM configuration

Purpose: make model selection explicit and environment-safe.

Expected outcome:

- Add a small config file, preferably `config/runtime.yml` unless a broader config module is introduced.
- Include:

```yaml
llm:
  provider: litellm
  model: litellm_proxy/gemini-flash-lite
```

- Add a lightweight config loader only if needed by graph/runtime code.
- Keep credentials in environment variables, not YAML.

Likely touch points:

- `config/runtime.yml`
- optional `src/application/config.py`
- tests for config defaults/loading if a loader is added

Validation commands:

```bash
uv run --extra test pytest
rg -n "gemini-flash-lite|LITELLM_PROXY_API_BASE|LITELLM_PROXY_API_KEY|LITELLM_KEY" config src docs tests
```

### 5. Introduce minimal LangGraph runtime skeleton

Purpose: create the first real graph entrypoint without implementing the full domain runtime.

Expected outcome:

- Add a minimal `VictusGraphState` Python type/model aligned with `docs/contracts/langgraph-state-v1.md`.
- Add a graph builder under `src/agent/`.
- First graph can be deterministic:
  - normalize request
  - safety precheck
  - route intent with existing `victus_routing`
  - compose a traceable response
- LLM usage should be injected through `LLMClient` only and limited to a clearly named node when needed, such as response composition or clarification wording.
- No node imports `litellm`.

Likely touch points:

- `src/agent/state.py`
- `src/agent/graph.py`
- `src/agent/nodes/`
- `tests/agent/test_graph.py`

Validation commands:

```bash
uv run --extra test pytest
rg -n "litellm|import litellm|from litellm" src tests dev/langgraph-viewer
```

Expected result:

- `litellm` appears only in infrastructure adapter/tests.

### 6. Convert LangGraph viewer into a dev visualization harness

Purpose: make `dev/langgraph-viewer` visualize the real graph instead of owning a separate demo graph.

Expected outcome:

- Update `dev/langgraph-viewer/src/agent.py` to import the real graph from `src/agent/graph.py`.
- Remove direct provider construction from the viewer.
- Keep viewer-specific virtualenv, `.env`, checkpoints, and nested Git ignored/untracked.
- Keep the viewer documentation explicit that it is development-only.

Likely touch points:

- `dev/langgraph-viewer/src/agent.py`
- `dev/langgraph-viewer/langgraph.json`
- `dev/langgraph-viewer/README.md`

Validation commands:

```bash
uv run --extra test pytest
rg -n "import litellm|from litellm" dev/langgraph-viewer src
```

### 7. Document operational contract for LiteLLM

Purpose: keep operations accurate without leaking private connection details.

Expected outcome:

- Update `docs/100-ARCHITECTURE.md` with the LLM port/adapters boundary.
- Update `docs/200-OPERATIONS.md` with LiteLLM proxy env variable names and safety rules.
- Update `docs/implementation/010-build-order.md` so LLM port comes before LangGraph runtime nodes.
- Do not document actual proxy URL or API key values.

Likely touch points:

- `docs/100-ARCHITECTURE.md`
- `docs/200-OPERATIONS.md`
- `docs/implementation/010-build-order.md`

Validation commands:

```bash
uv run --extra test pytest
rg -n "LITELLM_PROXY_API_KEY|LITELLM_KEY|LITELLM_PROXY_API_BASE" docs src tests
```

### 8. Optional live smoke test through private LiteLLM proxy

Purpose: verify real connectivity only when explicitly requested.

Expected outcome:

- Add a smoke command or script that performs one tiny completion through `LLMClient`.
- The smoke test is skipped by default unless an explicit env flag is set, for example `VICTUS_LIVE_LLM_SMOKE=1`.
- The smoke output must include operation name, model, text length, and usage if present, but not request secrets or full raw payload.

Likely touch points:

- `ops/scripts/` or `tests/smoke/`
- `docs/200-OPERATIONS.md`

Validation commands:

```bash
uv run --extra test pytest
VICTUS_LIVE_LLM_SMOKE=1 uv run python -m <smoke_module>
```

Blocker:

- Requires Tailscale/private network access and valid env vars.

## Final validation before handoff

Run:

```bash
uv run --extra test pytest
rg -n "import litellm|from litellm" src tests dev/langgraph-viewer
git status --short --ignored
```

Expected:

- Tests pass.
- LiteLLM imports are isolated to infrastructure adapter/tests.
- `.env`, `.venv`, caches, and LangGraph local checkpoints remain ignored.
