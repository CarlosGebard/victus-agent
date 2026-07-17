# Llama Guard 4 safety CLI

## Goal

Use `meta-llama/Llama-Guard-4-12B:together` through Hugging Face Router serverless chat
completions for testing arbitrary console inputs and returning Llama Guard safety categories.

## Scope

- Add a Hugging Face Router chat-completions adapter.
- Route `victus safety-check` through Llama Guard 4.
- Update runtime safety config defaults for this test path.
- Add focused tests that stub the router call.

## Assumptions

- Serverless execution requires `HF_TOKEN`, `HUGGING_FACE_TOKEN`, or `HUGGING_FACE_API_KEY`.
- The default router base URL is `https://router.huggingface.co/v1`.
- Llama Guard output maps to Victus safety state as:
  - `safe` -> allow
  - `unsafe\nSx...` -> blocked with mapped Llama Guard category.

## Steps

1. Implement Hugging Face Router chat-completions client.
2. Add Llama Guard 4 category mapping.
3. Change `safety-check` to classify a query and print JSON with raw guard output and normalized
   safety state.
4. Update tests for the new CLI behavior.
5. Run focused CLI tests and compile checks.

## Validation

- `uv run --extra test victus test tests/test_victus_cli.py`
- `uv run --extra test victus compile`

## Risks

- The provider route may return authorization, quota, or provider availability errors at runtime.

# Safety branch split

## Goal

Route blocked safety results to a dedicated user-warning node with no tool exposure, while allowed
requests continue through the existing event-capture flow.

## Scope

- Wire safety precheck into the graph before `event_capture`.
- Add a conditional route from safety state.
- Add a blocked response node that writes only `response` and audit path.
- Keep the existing allowed path behavior intact after normalization and safety.

## Assumptions

- In graph tests without an injected guard client, safety defaults to allowed.
- The blocked node should not register tools or call tool handlers.
- The warning response can be deterministic for now; a future simple model adapter can replace it
  without changing routing.

## Steps

1. Add a graph route helper for `safety.status`.
2. Add/call `safety_blocked_response` for blocked states.
3. Route allowed states to the existing `event_capture` node.
4. Add tests for allowed path and blocked path.
5. Run focused graph and CLI tests plus compile.

## Validation

- `uv run --extra test victus test tests/agent/test_graph.py tests/test_victus_cli.py`
- `uv run --extra test victus compile`

## Risks

- Existing tests expecting a one-node audit path need to be updated to the new graph contract.

# Nemotron safety semantic index

## Goal

Build a standalone BGE-M3/Chroma pipeline that streams Nemotron safety prompts, indexes them in
bounded concurrent batches, and performs local cosine-similarity retrieval without changing or
joining the existing Llama Guard graph flow.

## Scope

- Add an optional dependency group for Hugging Face datasets/inference, ChromaDB, NumPy, and tqdm.
- Add a standalone infrastructure module for endpoint embedding, streaming bulk indexing, and
  semantic querying.
- Store `prompt` as the Chroma document and retain compact safety/source fields as metadata.
- Add focused tests, an architecture decision, and an operational runbook.

## Assumptions

- The dedicated BGE-M3 endpoint returns one 1024-dimensional pooled embedding per input text and
  accepts at most 32 texts per client batch.
- The first real run targets the `train` split and is limited to 10,000 rows.
- `HUGGING_FACE_ENDPOINT` (or its `BGE_M3_ENDPOINT_URL` alias) and an HF token will be supplied at
  runtime and never committed.
- Bulk embedding uses the dedicated endpoint; runtime queries use `hf-inference` with `HF_TOKEN`
  without coupling this pipeline to Llama Guard.

## Steps

1. Declare the optional dependencies and document the independent architecture boundary.
2. Implement the typed endpoint adapter and validate batch count/dimensionality.
3. Implement bounded streaming batches, retrying workers, idempotent Chroma upserts, and progress.
4. Implement local cosine querying with similarity reported as `1 - distance`.
5. Add unit tests using fake datasets, embeddings, and a temporary persistent Chroma database.
6. Run focused tests and compile checks; do not run the paid endpoint smoke until credentials exist.

## Validation

- `uv run --extra test --extra safety-index pytest tests/infrastructure/test_safety_similarity.py`
- `uv run --extra test --extra safety-index python -m compileall src tests`
- With runtime credentials: `uv run --extra safety-index python -m infrastructure.safety_similarity`

## Risks

- Endpoint batch limits may require reducing the default batch size from 64.
- Concurrent endpoint capacity may be lower than four requests and trigger retries.
- Existing collections created with a different embedding dimension or distance metric are
  incompatible and must use a different collection name or be recreated explicitly.
- Dataset prompts intentionally contain harmful material and must not be rendered directly to end
  users outside authorized safety workflows.

# Logistic safety classifier over BGE-M3 embeddings

## Goal

Train, persist, evaluate, and query a standalone binary logistic-regression classifier using the
existing normalized BGE-M3 vectors without coupling it to the Llama Guard graph path.

## Scope

- Read embeddings and metadata from `nemotron_safety_bge` in bounded chunks.
- Keep only text-only `task_type=safety` rows labeled `safe` or `unsafe`.
- Use deterministic stratified train/validation/test partitions.
- Tune L2 regularization and an unsafe threshold against validation recall.
- Persist portable NumPy weights plus a JSON manifest; runtime inference must not require
  scikit-learn.
- Add focused tests, artifact documentation, and operational commands.

## Assumptions

- Stored BGE-M3 vectors are finite, normalized, and 1024-dimensional.
- `unsafe` is the positive class and false negatives are more costly than false positives.
- A minimum validation recall of 0.95 is an initial policy target, not a production guarantee.
- The current 10,000-row train sample supports a baseline evaluation; official validation/test
  embeddings remain necessary before production use.

## Steps

1. Add an optional `safety-training` dependency group with scikit-learn.
2. Implement filtered Chroma extraction and deterministic dataset splitting.
3. Train candidate logistic models, select a threshold, and report global/per-language metrics.
4. Export validated NumPy/JSON artifacts and implement NumPy-only runtime classification.
5. Add CLI-style `train` and `query` demonstrations without graph integration.
6. Add tests, train the real baseline artifact, and run focused/full validation.

## Validation

- `uv run --extra test --extra safety-index --extra safety-training pytest tests/infrastructure/test_safety_classifier.py`
- `uv run --extra test --extra safety-index --extra safety-training python -m compileall src tests`
- `uv run --extra safety-index --extra safety-training python -m infrastructure.safety_classifier train`
- With endpoint credentials: `uv run --env-file .env --extra safety-index python -m infrastructure.safety_classifier query "test query"`

## Risks

- Random held-out rows from a single train subset may contain near-duplicates or source leakage.
- Text embeddings cannot learn labels that depend on omitted images.
- A linear classifier may miss adversarial intent, negation, quotation, or unseen languages.
- Probabilities and thresholds require validation on the official dataset splits before acting as a
  production safety gate.

# MCP tool boundary restructure

## Goal

Make the MCP-exposed tool registry the active skill/tool surface while moving duplicated
event-capture and profile-update contracts out of graph nodes and into the domain/application tool
boundary.

## Scope

- Move tool input/decision models, validation rules, event mappings, and skill metadata out of
  `agent/nodes/event_capture` and `agent/nodes/profile_update`.
- Keep public tool names stable: `event_capture` and `profile_update`.
- Keep the existing MCP stdio server entrypoint as the external tool surface.
- Update the graph to consume the application tool boundary instead of running classifier nodes
  directly.
- Update architecture/contract docs only where active behavior changes.

## Assumptions

- Current handlers classify and validate only; they do not persist events.
- Deterministic policy classifiers remain the default path when no LLM client/model is provided.
- Codex connection should use the `victus-mcp` stdio server command.

## Steps

1. Move schemas, validators, skill metadata, event mapping, and deterministic policies into
   `domain/tools`.
2. Update `application.tools` to import domain contracts and execute domain policies directly.
3. Update graph orchestration to call the tool boundary and store a `ToolResult` envelope.
4. Remove duplicate node-local schema, validator, and skill-manifest modules.
5. Update focused tests and docs for the new boundary.

## Validation

- `uv run --extra test victus test tests/application/test_tool_handlers.py tests/victus_mcp/test_server.py tests/agent/test_graph.py tests/contracts/test_tool_models.py`
- `uv run --extra test victus compile`

## Risks

- The graph test contract changes from storing a raw classifier decision to storing the
  `ToolResult.data` payload under the existing `last_tool_result` key.
- Existing imports from removed node-local modules must be migrated in one pass to avoid stale
  compatibility shims.

# MCP token relay authentication

## Goal

Allow the local Victus MCP server to relay a user JWT to the decoupled web backend without asking
the user to manually configure environment variables for every Codex session.

## Scope

- Add a local session utility that reads `VICTUS_API_TOKEN` first and then OAuth tokens from
  `~/.victus/session.json`.
- Replace `victus login` token entry with browser OAuth Authorization Code + PKCE.
- Add `victus logout` to remove the local session.
- Add an MCP-visible `recuperar_perfil` tool that calls `GET {BACKEND_API_URL}/me`.
- Use `Authorization: Bearer <token>` and handle missing, expired, unavailable, and malformed
  backend states gracefully.
- Document the backend integration prompt and local validation flow.

## Assumptions

- The backend API remains in a separate repository.
- The default auth backend URL is `http://localhost:8000`.
- The default profile API URL is `http://localhost:8000/v1`.
- The MCP server should keep returning the repository-standard `ToolResult` envelope.

## Steps

1. Implement `victus_mcp.utils.auth`.
2. Add CLI browser login with local loopback callback.
3. Add refresh-token handling and logout.
4. Add async profile recovery handler and register it as `recuperar_perfil`.
5. Update tests for auth, CLI, tool handling, and MCP exposure.
6. Update operations docs and backend integration prompt.

## Validation

- `uv run --extra test victus test tests/victus_mcp/test_auth.py tests/application/test_tool_handlers.py tests/test_victus_cli.py tests/victus_mcp/test_server.py`
- `uv run --extra test victus compile`
- `uv run victus mcp-list-tools`
- `uv run victus mcp-call recuperar_perfil '{}'`

## Risks

- `~/.victus/session.json` stores a bearer token and must remain local-only with restrictive
  permissions.
- The backend `/me` response shape must stay compatible with the profile summary formatter.

# Deployable MCP HTTP transport

## Goal

Expose the same Victus MCP tool surface over a deployable Streamable HTTP transport while keeping
the existing local stdio MCP server for Codex desktop and MCP registry use.

## Scope

- Keep `victus-mcp` as the local stdio server.
- Add `victus-mcp-http` as a stateless Streamable HTTP MCP server.
- Reuse `src/victus_mcp/server.py` and `application.tools` so tool definitions stay single-source.
- Add a health endpoint and Dockerfile for infrastructure deployment.
- Document how a LangGraph web app can consume the HTTP MCP endpoint with
  `langchain-mcp-adapters`.

## Assumptions

- Local users keep using OAuth session files through the stdio server.
- Web/infrastructure users should not rely on `~/.victus/session.json`; request/session auth should
  come from the web backend or infrastructure layer.
- The first deployable transport can be stateless and read-only from the MCP session perspective.

## Steps

1. Build a Starlette ASGI app mounted at `/mcp` using the MCP SDK's
   `StreamableHTTPSessionManager`.
2. Add `victus-mcp-http` entrypoint with host/port environment overrides.
3. Add Dockerfile for the HTTP server runtime.
4. Add focused tests for health/app construction and current tool registration.
5. Update architecture and operations docs with local stdio vs deployable HTTP split.

## Validation

- `uv run --extra test victus test tests/victus_mcp`
- `uv run --extra test victus compile`
- `uv run victus-mcp-http` and `curl http://localhost:8765/health`

## Risks

- Remote HTTP MCP auth must not depend on local session files in production.
- LangGraph web app integration should consume `/mcp` over HTTP and pass user auth explicitly at
  the application boundary.
