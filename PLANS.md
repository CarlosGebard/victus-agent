# LangGraph package boundaries

## Goal

Reorganize `src/adapters/langgraph/` into explicit runtime, orchestration-engine, and capability
packages without changing graph behavior, contracts, or external HTTP/CLI behavior.

## Scope

- Place persistence, memory, context, session-context, and response support under `runtime/`.
- Place graph assembly, state, routing, tool-node, and agent-loop code under `engine/`.
- Place LangGraph-specific contracts, projections, self-harm response, and translation support under
  `capabilities/`.
- Update internal imports, entrypoint configuration, source references, and focused tests.

## Assumptions

- Existing local changes in the affected modules are authoritative and must be preserved verbatim
  apart from import paths.
- `response.py` belongs with runtime session support because it persists legacy session context.
- `prompts/compose_response.py` remains in the existing prompts package because it was not part of
  the requested module grouping.
- The move changes internal Python module paths but preserves callable names and external APIs.

## Steps

1. Record the package-boundary decision in an ADR.
2. Create the three subpackages and move the requested modules without changing their behavior.
3. Update imports, `langgraph.json`, tests, and documentation source references.
4. Verify there are no stale old-path imports and run focused repository validation.

## Validation

- Search source, tests, configuration, and active docs for obsolete `adapters.langgraph.<module>`
  imports and old source paths.
- `uv run --extra test victus test tests/test_adapters.py`
- `uv run --extra test victus compile`
- `uv run --extra test victus check`

## Risks

- LangGraph Studio depends on the configured graph module path and will fail if `langgraph.json` is
  not updated with the move.
- Legacy session-context modules are currently inactive; moving them must not accidentally wire them
  into the active graph.
- Existing uncommitted work overlaps several moved files and must remain intact.

---

# Contract documentation by domain

## Goal

Make active contracts immediately distinguishable by owning domain, while keeping the fundamental
`Tools.md`, `Events.md`, and `Projections.md` guides at the top of `docs/` and PostgreSQL documented
explicitly under `docs/contracts/`.

## Scope

- Add a minimal contract index.
- Preserve and update active chat, graph state, tool result, event envelope, projection, and database
  schemas against current code.
- Keep the superseded session-context schema clearly separated as a migration reference.
- Remove the remaining generic `docs/contracts/` grouping after its useful content is represented.

## Assumptions

- Code models and database metadata are authoritative when historical contract text differs.
- Redundant indexes, empty imported-contract locks, and future capability notes are not active
  contracts.
- Existing unrelated documentation and runtime changes remain untouched.

## Steps

1. Place agent contracts under `docs/contracts/agent/`.
2. Keep shared tool, event, and projection schemas in the fundamental top-level domain documents.
3. Create the PostgreSQL schema contract and retain the safety artifact contract separately.
4. Add the contract index and update documentation navigation.

## Validation

- Compare documented contract fields with the current typed models and SQLAlchemy metadata.
- Verify every documented source path exists.
- Verify the old generic contract directory contains no remaining active contract.
- Run formatting and repository validation checks.

## Risks

- Historical contracts may contain stale fields; only implemented fields will be presented as
  current.
- The session-context contract is superseded and must not appear active.

---

# Documentation reset: single conceptual overview

## Goal

Replace the numbered documentation system with one current, conceptual `docs/Overview.md` while
preserving the existing documentation as a deprecated archive.

## Scope

- Rename `docs/` to `docs-deprecated/` without deleting its contents.
- Create `docs/Overview.md` in English as the sole current system overview.
- Update active repository guidance and entrypoint links to the new documentation model.
- Prevent the contract sync helper from recreating the retired structure under `docs/`.

## Assumptions

- Deprecated documents are retained as historical material, not current sources of truth.
- The overview describes the implemented system at a conceptual level and contains no code,
  commands, schemas, or implementation walkthroughs.
- Runtime behavior and public contracts remain unchanged.

## Steps

1. Derive the current system model from the existing documentation and focused runtime sources.
2. Archive the complete current documentation tree under `docs-deprecated/`.
3. Add the consolidated overview and update active documentation rules and links.
4. Check that no active reference requires the retired numbered documents and validate the
   documentation structure.

## Validation

- Verify that `docs/` contains only `Overview.md`.
- Verify that all prior documentation exists under `docs-deprecated/`.
- Search active repository entrypoints for references to the retired numbered documents.
- Run the repository's lightweight validation command.

## Risks

- Archived documents may describe details more precisely than the overview, but they are no longer
  authoritative.
- Existing local changes inside the old documentation tree must remain intact through the rename.

---

# Preserve tool-call history across checkpointed turns

## Goal

Keep checkpointed chat history valid after tool execution so a later `POST /chat` turn in the same
conversation can be sent to LiteLLM without an orphaned tool message.

## Scope

- Persist the assistant message containing the accepted tool call before tool execution.
- Preserve assistant `tool_calls` and tool `tool_call_id` when converting checkpoint messages to LLM
  request dictionaries.
- Add focused HTTP regression coverage for a tool turn followed by another turn on the same thread.

## Assumptions

- LangGraph's existing `messages` reducer and checkpointer remain the source of thread-scoped message
  history.
- Store namespaces and long-term memory behavior do not need changes for this defect.
- Provider exception logging is optional and outside the minimal correctness fix because the HTTP
  debug response already exposes only the exception class.

## Steps

1. Append a provider-compatible assistant tool-call message when `agent_decision` accepts one call.
2. Extend `_message_dict()` to retain tool-call linkage from checkpoint-restored LangChain messages.
3. Add a two-turn authenticated HTTP regression test using one shared in-memory checkpointer.
4. Run focused adapter tests, compilation, and repository checks.

## Validation

- `uv run --extra test victus test tests/test_adapters.py`
- `uv run --extra test victus compile`
- `uv run --extra test victus check`

## Risks

- Tool-call dictionaries must match LangChain's expected shape so `add_messages` can restore them.
- Confirmation and clarification flows must retain the same call id used by the eventual tool result.

---

# Authenticated chat debug endpoint

## Goal

Expose an opt-in `POST /chat/debug` boundary that executes the same authenticated LangGraph turn as
`POST /chat` and returns a bounded, redacted view of the resulting orchestration state for the
Victus webapp backend to render.

## Scope

- Shared HTTP chat execution path for normal and debug responses.
- Additive debug response contract and recursive safe serialization.
- Environment feature flag, contract documentation, and chat operations runbook.
- Focused adapter coverage for disabled access, response shape, redaction, and ownership.

## Assumptions

- The webapp backend forwards its user JWT as the existing bearer token.
- React never calls the agent service directly.
- Debug output may contain the authenticated user's own conversational and projection state, but
  never bearer tokens, credentials, system prompts, environment values, or raw checkpoints.
- `POST /chat` remains backward compatible.

## Steps

1. Add typed debug response fields without changing `ChatResponse`.
2. Refactor the Starlette adapter so both routes share authentication, ownership, resume, and graph
   execution behavior.
3. Build bounded debug snapshots from the actual graph result and post-run pending nodes, with
   recursive secret-key redaction.
4. Gate `/chat/debug` behind `VICTUS_CHAT_DEBUG_ENABLED` and document its secure operation.
5. Extend the existing HTTP adapter test and run the repository validation commands.

## Validation

- `uv run --extra test victus test tests/test_adapters.py`
- `uv run --extra test victus compile`
- `uv run --extra test victus check`

## Risks

- Graph state may contain sensitive user health context; debug access retains normal identity and
  thread ownership checks and should remain disabled outside controlled environments.
- Unbounded state can produce oversized responses; serialization limits depth, collection length,
  and string length.

---

# LangGraph Agent V1

This is the active implementation plan. It supersedes the completed tool-first, MCP discoverability,
and selection-only evaluation plans that previously occupied this file.

## Implementation status

Implemented on 2026-07-18 as a testable V1 runtime: model decision, generic `ToolRuntime` execution,
checkpointed clarification/confirmation, bounded Store memory, synchronous projections, authenticated
`POST /chat`, PostgreSQL saver/store lifecycle, and focused in-memory acceptance tests. Legacy custom
memory tables remain for the documented compatibility window; external LiteLLM and PostgreSQL
acceptance depends on configured services.

Local orchestration is packaged in `compose.yml`: PostgreSQL, domain migrations, LangGraph storage
setup, authenticated chat, and MCP start and stop as one dependency-ordered stack.

## Task classification

- feature
- architecture
- database
- storage
- security
- migration
- observability
- contract change
- documentation

## Goal

Deliver the first complete Victus LangGraph agent: multi-turn chat, dynamic selection and execution of
the existing typed tools through `ToolRuntime`, domain-event persistence, safe pause/resume for
clarification and confirmation, short-term memory through LangGraph checkpoints, and bounded
cross-thread memory through LangGraph Store.

V1 exposes one authenticated asynchronous chat API. MCP remains the external tool adapter and
PostgreSQL remains the shared persistence service.

## Non-goals

- No production database is required for development or evaluation.
- Do not replace `ToolRuntime`, the canonical catalog, domain events, or projections.
- Do not store meals, biometrics, allergies, restrictions, goals, plans, or other domain truth in
  LangGraph Store; events and projections remain authoritative.
- No semantic/vector memory in V1. Defer embeddings until there is a model/dimension contract,
  retention policy, and retrieval evaluation.
- No background workers, distributed queues, multi-agent delegation, voice, streaming UI, or broad
  production OAuth rewrite.
- Do not allow model-provided identities, arbitrary tool names, safety bypasses, or unbounded loops.
- Do not add broad test infrastructure; extend focused existing workflows.

## Current state observations

- `src/adapters/langgraph/engine/graph.py` routes every allowed request to fixed `event_capture` and ends.
- `tool_node.py` hardcodes `user_id + normalized_text`; it cannot execute other tool schemas.
- `tool_registry`, `compose_response`, `context_bootstrap`, and `summarize_after_response` exist but
  are not wired. `build_graph()` accepts `session_context_repository` but never uses it.
- `VictusGraphState` has domain sections but no reducer-backed message channel.
- The canonical catalog exposes eight typed tools. MCP, CLI, LangGraph, and tests share `ToolRuntime`.
- The working tree adds LiteLLM function-tool requests, returned `tool_calls`, and a selection-only
  evaluator, but no graph node consumes tool calls yet.
- Runtime config selects `litellm_proxy/gemini-flash-lite`; proxy URL/key configuration already exists.
- PostgreSQL event persistence, idempotency, projections, and rebuilds exist. Projection updates are
  not applied automatically after every mutation.
- Current custom conversation memory uses `ConversationStateSummary`, `PendingInteractionState`,
  `SessionContextRepository`, `conversation_state_summaries`, and `pending_interaction_state`; the
  active graph does not use them.
- `agent_turns` and `node_runs` exist but are not written by active MCP/LangGraph paths.
- Installed versions are LangGraph `1.2.5` and `langgraph-checkpoint 4.1.1`. In-memory saver/store are
  installed; PostgreSQL saver/store modules are missing, requiring a compatible
  `langgraph-checkpoint-postgres` dependency.
- HTTP exposes MCP and health only; there is no chat endpoint.
- `recuperar_perfil` requires authenticated identity, while LangGraph currently invokes anonymously.
- Event capture is regex based. Exact original text must be preserved, and common conjugations such as
  `comio/comió` require policy coverage.

## Memory architecture

### Short-term: LangGraph checkpoints

- Production uses `AsyncPostgresSaver`; unit tests use injected `InMemorySaver`.
- `conversation_id` is the LangGraph `thread_id`:

  ```python
  config = {"configurable": {"thread_id": conversation_id, "user_id": authenticated_user_id}}
  ```

- The API verifies thread ownership before invoke, read, update, replay, or resume.
- Checkpoint state owns messages, current proposal, results, loop count, interrupts, compact summary,
  graph version, and resume position.
- Database handles, clients, secrets, repositories, and large projection/artifact bodies never enter
  checkpoint state.
- Clarification/confirmation use `interrupt()` and `Command(resume=...)` on the same owned thread.

### Long-term: LangGraph Store

- Production uses `PostgresStore`; unit tests use injected `InMemoryStore`.
- Namespaces are rooted only in authenticated identity:

  ```text
  ("users", <user_id>, "agent_memory", "semantic")
  ("users", <user_id>, "agent_memory", "procedural")
  ```

- Semantic agent memory contains bounded non-domain conversational facts across threads. Procedural
  memory contains explicit interaction preferences such as language or response detail.
- Documents include stable key, kind, content, source thread/turn, timestamps, and confidence or an
  explicit-user flag.
- V1 retrieval is deterministic by namespace/key/filter with strict result limits; no embeddings.
- The model may propose memories, but deterministic policy accepts, updates, ignores, or deletes them.
- Candidates belonging to domain truth must go through tools/events/projections, never Store.

### Domain persistence remains separate

- `user_events` is immutable mutation history; projections are current domain read models.
- Checkpoints are execution state, not business audit records.
- Store is conversational memory, not a profile/event substitute.
- MCP retains the canonical catalog externally. Internal graph nodes call `ToolRuntime` directly and
  do not connect back to their own MCP server.

## Target graph

```text
START
  -> ingest_turn
  -> recall_long_term_memory
  -> load_domain_projections
  -> safety_precheck
      -> safety_response                              [blocked]
      -> agent_decision                               [allowed]
           -> compose_final_response                  [no tool]
           -> validate_proposed_tool                  [tool]
                -> confirmation_interrupt             [approval required]
                -> execute_tool
                     -> clarification_interrupt       [missing input]
                     -> agent_decision                [result; bounded loop]
                     -> safety_response               [blocked]
                     -> compose_error_response        [error/rejected]
  -> update_long_term_memory
  -> finalize_turn
  -> END
```

The loop has a configured maximum. V1 accepts at most one tool call per model response; multiple calls
fail closed or are serialized only after explicit ordering and side-effect validation.

## Likely touch points

- `pyproject.toml`, `uv.lock`, `config/runtime.yml`, `.env.example`
- `src/adapters/langgraph/{engine,runtime}/` graph and runtime modules
- new focused nodes under `src/adapters/langgraph/`
- `src/bootstrap/` for graph and storage lifecycle
- `src/victus_platform/llm/`, projection repositories/projectors, `src/tools/runtime.py`
- `src/tools/event_capture/policy.py`
- new async chat boundary under `src/adapters/http/`
- `ops/db/migrations/`, `ops/scripts/`
- focused existing tests
- architecture, operations, contracts, runbooks, and memory ADRs

## Deprecations and removals

### Deprecate when saver/store integration lands

- `SessionContextRepository` and repository reads/writes in `context_bootstrap` and
  `summarize_after_response`.
- `ConversationStateSummary`, `PendingInteractionState`, and `BootstrapContext` as persistence
  contracts. A compact summary may remain only as checkpointed internal state.
- `conversation_state_summaries` and `pending_interaction_state` tables.
- ADR `20260614-session-context-management`, superseded by the LangGraph memory ADR.

### Remove after migration and one compatibility window

- `src/victus_platform/repositories/session_context.py` and duplicate protocols/state fields.
- Custom summary/pending table definitions and then the tables through a forward Alembic migration.
- Fixed `tool_node(name, runtime)` after the generic executor passes adapter/persistence tests.
- Implicit `user_id="local-user"` and hardcoded safety-to-`event_capture` routing.

### Migration policy

- Audit row counts before changing data.
- Stop custom-table writes, retain read-only fallback for one compatibility window, verify Store, and
  only then drop tables.
- Migrate only safe non-domain durable facts from summaries to Store with deterministic namespaces.
- Do not fabricate checkpoints from `pending_interaction_state`; it lacks a valid execution position.
  Expire those rows and ask affected users to repeat the pending action.
- Before drop, rollback is configuration-based while old tables remain. After drop, recovery requires
  database backup restoration.

### Retain

- `ToolRuntime`, tool catalog/schemas, safety, event store, idempotency, projections, MCP adapters,
  LiteLLM proxy integration, selection evaluator, `user_events`, and projection tables.
- `clarification`/`confirmation` tools remain for MCP compatibility and interaction events; LangGraph
  interrupts own internal control flow.

### Review later

- Do not wire unused `agent_turns`/`node_runs` into V1. Confirm no consumers and record a separate
  decision before removal because checkpoint history and tracing may supersede them.

## Milestones

### 1. Lock contracts and dependency compatibility

Purpose: define V1 state, chat, identity, memory, interrupt, and loop contracts first.

Expected outcome:
- Resolve/install the PostgreSQL LangGraph package compatible with current LangGraph/checkpoint; do
  not silently downgrade core packages.
- Add reducer-backed messages, exact original text, verified identity, proposed action, results, loop
  count, compact summary, graph version, and response to state.
- Define chat schemas, Store documents, limits, and `thread_id == conversation_id` invariant.

Likely touch points: dependencies, lockfile, state/contracts, configuration.

Validation:
- `uv lock --check`
- import `AsyncPostgresSaver` and `PostgresStore`
- schema tests for chat, state, proposal, and memory documents

Blocker: stop if package versions cannot resolve; establish the supported version matrix explicitly.

### 2. Add PostgreSQL saver/store lifecycle

Purpose: provide supported persistent short- and long-term memory.

Expected outcome:
- Async bootstrap owns saver/store connection lifecycle and compiles with `checkpointer=` and `store=`.
- Dedicated deployment command runs both `setup()` methods; request startup never runs migrations.
- Normalize existing SQLAlchemy `DATABASE_URL` to the driver DSN without logging credentials.
- Dependency injection supplies in-memory implementations to unit tests.

Validation:
- idempotent setup
- checkpoint survives resource restart and resumes the same thread
- Store put/search/delete persists and is isolated by user namespace
- no credential appears in output or checkpoint state

### 3. Implement model-driven agent decision

Purpose: let Gemini select canonical tools or abstain.

Expected outcome:
- Build functions directly from catalog descriptions/schemas.
- Add `agent_decision` consuming LiteLLM `tool_calls`.
- Never overwrite original text; derived text uses a separate field.
- Enforce allowed tools, one call per response, valid JSON, exact identity, no-tool behavior, and loop cap.
- Supply bounded Store memories and projections with provenance.

Validation:
- fake-client coverage for every tool, abstention, invalid/multiple calls, changed identity, exact text
- `uv run victus intent-eval` against the promoted LiteLLM alias
- existing MCP catalog tests remain green

### 4. Implement generic safe tool execution and routing

Purpose: execute any selected tool through one safe path.

Expected outcome:
- Replace fixed node with a generic `ToolInvocation` executor using authenticated `ToolContext`.
- Override/reject model `user_id`; preserve schema, safety, trace, idempotency, and persistence.
- Route all `ToolResult` statuses and return successful results to the bounded agent loop.
- Never claim persistence without matching result/event evidence.

Validation:
- focused tests for success, clarification, blocked, rejected, error
- PostgreSQL test for one event, idempotent repeat, safety block, rejected invocation
- MCP behavior unchanged

### 5. Add checkpointed clarification and confirmation

Purpose: pause and resume sensitive or incomplete work safely.

Expected outcome:
- Structured interrupts retain proposed action and required fields in checkpoint state.
- Resume via `Command(resume=...)` on the same owned thread.
- Existing interaction tools record events where applicable; interrupts control execution.
- Reject wrong-user/thread, completed, and graph-version-incompatible resumes.

Validation:
- pause/restart/resume for clarification and confirmation
- decline produces no mutation
- resume never repeats completed side effects

### 6. Add bounded long-term memory

Purpose: carry allowed conversational context across threads.

Expected outcome:
- Recall bounded authenticated namespaces before decision.
- Validate candidates after response; support explicit remember/forget.
- Record provenance and reject secrets, health events, domain constraints, artifacts, tool payloads, and
  unverified inferences.

Validation:
- same-user memory crosses threads
- no cross-user recall
- domain facts rejected from Store
- forget deletes expected key
- bounded retrieval prevents prompt growth

### 7. Keep projections current

Purpose: make successful mutations visible to the next dependent turn.

Expected outcome:
- Apply relevant projectors at a deterministic synchronous persistence boundary for V1.
- Load bounded current projections before decision; retain rebuild commands for recovery.

Validation:
- profile/meal changes visible next turn without manual rebuild
- replay rebuild matches live projection and offset
- failures cannot acknowledge a state that required projections do not reflect

### 8. Expose authenticated chat API

Purpose: provide the supported multi-turn application boundary.

Expected outcome:
- Async `POST /chat` maps `conversation_id` to `thread_id`, injects identity, invokes/resumes graph,
  and returns status, message, interrupt, tool summary, event refs, and trace ID.
- Readiness covers DB, LiteLLM config, saver, and Store.
- Chat and MCP remain separate explicit contracts. V1 JSON is non-streaming.

Validation:
- auth/request validation; new/resumed threads; no-tool, tool, clarification, confirmation, safety,
  provider and DB failures
- cross-user thread access denied

### 9. Migrate and retire custom memory

Purpose: remove duplicate persistence after saver/store proof.

Expected outcome:
- Audit, stop writes, migrate eligible facts, hold read-only compatibility, remove code, then drop
  custom tables in a later migration.
- Update/retire experimental session-context contract.

Validation:
- deterministic migration dry-run without secrets
- no active imports of deprecated code
- fresh/migrated users start supported conversations
- restore procedure documented before table drop

### 10. Complete observability, documentation, and acceptance

Purpose: make V1 operable and evidence-backed.

Expected outcome:
- Trace IDs join chat, graph, LLM, tool, and event refs.
- Document storage setup, run, recovery, thread inspection, memory deletion, retention, and failures.
- Synchronize architecture/contracts and decide unused audit tables separately.

Validation:
- formatting, lint, typecheck if configured, focused unit/integration tests, compile/build, security and
  config checks, and full manual `/chat` acceptance matrix

## V1 acceptance criteria

- Multi-turn threads survive restart through checkpoints.
- Same-user new threads recall allowed Store memory; other users cannot access it.
- Gemini selects every supported tool or abstains from the canonical catalog.
- Arguments are schema-valid, use verified identity, and preserve exact source text where required.
- Mutations emit one idempotent event and matching reference; projections are current next turn.
- Clarification/confirmation survive restart and resume exactly once.
- Safety blocks and declined actions create no prohibited mutation.
- Responses describe actual results and never invent persistence success.
- Custom session summary/pending writes are disabled with visible migration status.
- Relevant validation passes or reports the exact unavailable external dependency.

## Risks

- Unbounded checkpoint messages can grow storage/prompts; define trimming and compact-summary limits.
- New graph code applies to old threads; version state and reject/migrate incompatible resumes.
- Weak Store policy creates a shadow profile; enforce memory categories and provenance.
- Replay can duplicate side effects; align checkpoints with stable idempotency keys.
- One PostgreSQL service simplifies operation but increases blast radius; use separate schemas/roles
  where supported and test backup/restore.
- LiteLLM aliases differ in function behavior; run the matrix for each promoted alias.
- Old pending rows cannot resume safely; expire explicitly instead of fabricating checkpoint positions.
