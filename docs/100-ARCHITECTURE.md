---
id: VICTUS-AGENT-ARCHITECTURE
title: Victus Agent Architecture
status: draft
updated_at: 2026-06-12
owners:
  - victus-agent-runtime
related_docs:
  - README.md
  - docs/000-SYSTEM-CONTEXT.md
  - 200-OPERATIONS.md
  - 300-CONTRACTS.md
---

# Victus Agent Architecture

## 1. Architectural Overview

Victus Agent is a modular, event-driven, projection-oriented agent runtime.

V1 domain is nutrition and lifestyle support. Workout programming is out of scope; training details may be used only as nutrition context or safety context.

The runtime combines:

- authenticated agent user context
- LangGraph orchestration
- safety-first routing
- embedding-assisted multilingual intent classification
- typed tool execution
- immutable event storage
- PostgreSQL projections
- planning artifact persistence
- evidence adapter boundaries

The LLM is a reasoning component inside the runtime. It is not the owner of agent identity, persisted state, tool side effects, or safety decisions.

The application layer accesses model providers only through the internal `LLMClient`
port. Provider-specific LiteLLM code belongs in `src/infrastructure/llm/` and must
not be imported by LangGraph nodes or application use cases.

Source code follows a layer-oriented layout:

```text
src/domain/             -> domain contracts and pure models
src/application/        -> ports, config, routing, and application services
src/infrastructure/     -> database, repositories, and provider adapters
src/agent/              -> LangGraph orchestration
src/victus_cli/         -> local operational CLI
```

```text
Authenticated Request
  -> Account Context Resolver
  -> Request Normalizer
  -> Context Bootstrap
  -> Safety Precheck
  -> Embedding-Assisted Intent Router
  -> Graph Branch / Node
  -> Typed Tool Handler
  -> Event Store Append
  -> Projector Update
  -> Response Composer
  -> Summary After Response
  -> Trace + Result
```

## 2. Major Components

### 2.1 API Boundary

Responsibility: accept user messages from the application layer and create a request context.

Inputs:

- authenticated request
- raw user text
- optional conversation id
- locale and timezone hints

Outputs:

- `RequestContext`
- normalized user input
- trace id

Boundary:

- must not trust user-provided identity identifiers
- must not execute tool side effects directly
- must pass all mutations through the agent runtime

### 2.2 Account Context Resolver

Responsibility: map trusted caller identity to the agent-local `agent_user_id`.

Inputs:

- external system
- external subject
- validated token claims

Outputs:

- `AuthContext`
- `agent_user_id`
- locale and timezone defaults

Boundary:

- owns identity resolution for the runtime
- does not own the external identity provider
- does not store raw provider tokens in plain database fields

### 2.3 LangGraph Orchestrator

Responsibility: execute the agent turn as a controlled graph.

Inputs:

- `VictusGraphStateV1`
- current projections
- router decision
- node-specific tool registry

Outputs:

- final response payload
- route decision record
- tool execution records
- event references
- warnings or clarification state

Boundary:

- owns orchestration state only
- does not own domain truth
- may checkpoint graph state, but checkpoints are not projections or event history

### 2.4 Safety Layer

Responsibility: classify and block unsafe, medical-risk, unsupported, or policy-sensitive requests before mutation or recommendation.

Inputs:

- raw and normalized user text
- current profile and constraints
- proposed tool action or recommendation candidate

Outputs:

- safety status: `ok`, `warning`, `blocked`, or `needs_clarification`
- risk category
- reasons
- allowed next route

Boundary:

- must run before planning and event mutation
- may run again before response finalization
- does not generate diet plans

### 2.4.1 Session Context Layer

Responsibility: preserve conversation continuity without loading full chat history by default.

Inputs:

- current request text
- latest `ConversationStateSummary`
- active `PendingInteractionState`
- minimal recent context when available

Outputs:

- bootstrapped context for the graph
- standalone routing query
- updated structured summary after response

Boundary:

- does not own domain truth
- does not duplicate projections or events
- does not store large artifacts or full tool outputs
- prioritizes pending interaction state for short replies

The graph owns two explicit session-context nodes:

- `ContextBootstrapNode`: loads compact session state and writes `request.routing_query` before safety/routing.
- `SummaryAfterResponseNode`: updates `ConversationStateSummary` after response composition.

The current summary implementation is deterministic. The target architecture allows an LLM-backed summarizer after final response composition through the `LLMClient` port, but it must emit structured JSON and must not receive full chat history by default.

### 2.5 Embedding-Assisted Intent Router

Responsibility: route multilingual user requests to the correct graph branch using semantic similarity, deterministic thresholds, rules, and optional LLM fallback.

Inputs:

- normalized user text
- request metadata
- route definitions
- route example embeddings
- safety status

Outputs:

- route label
- confidence
- top candidate routes
- routing method: `rule`, `embedding`, `hybrid`, `llm_fallback`, or `clarification`
- ambiguity reasons if applicable

Boundary:

- selects the next graph branch
- does not execute tools
- does not mutate user state
- does not answer evidence questions directly

V1 route families:

```text
log_update_data       -> EventCaptureGraph
new_plan              -> PlanningSessionGraph
revise_plan           -> PlanRevisionGraph
weekly_review         -> WeeklyReviewGraph
evidence_question     -> EvidenceAnswerGraph
profile_update        -> ProfileUpdateGraph
risk_medical_unsafe   -> SafetyTriageRoute
mixed_ambiguous       -> MixedIntentResolver
needs_clarification   -> ClarificationRoute
```

Embedding routing flow:

```text
normalized_text
  -> embed text with configured multilingual model
  -> search active route examples in pgvector
  -> compute candidate scores
  -> apply hard rules and safety overrides
  -> if top score >= threshold and margin >= min_margin: route
  -> if ambiguous: call MixedIntentResolver or LLM classifier
  -> if still unclear: ClarificationRoute
```

### 2.6 Graph Branches and Nodes

V1 graph branches:

| Branch | Responsibility |
|---|---|
| `SafetyTriageRoute` | Block, warn, or redirect risky requests. |
| `EventCaptureGraph` | Log meals, biometrics, symptoms, and factual user events. |
| `ProfileUpdateGraph` | Update stable restrictions, preferences, and durable profile context. |
| `PlanningSessionGraph` | Create new goals, sessions, revisions, and candidate plan artifacts. |
| `PlanRevisionGraph` | Revise existing plan artifacts using feedback and current projections. |
| `WeeklyReviewGraph` | Summarize recent adherence and create review events or recommendations. |
| `EvidenceAnswerGraph` | Search evidence and answer explanation questions without mutating user state by default. |
| `ClarificationRoute` | Ask missing-field questions and store resumable clarification state. |
| `MixedIntentResolver` | Split or sequence requests with multiple intents. |

### 2.7 Tool Registry and Tool Handlers

Responsibility: expose only node-appropriate tool handlers with typed input/output contracts.

V1 tool handlers:

```text
safety.triage
clarification.manage
nutrition.manage_meal
biometrics.log
symptom.log
profile.manage_context
goal.manage
planning.manage_session
diet.generate_recommendation
feedback.record
evidence.search
evidence.manage_support
```

Boundary:

- tools validate inputs before execution
- write tools emit events instead of mutating projections directly
- compute tools may return artifacts without saving them
- retrieval tools may read evidence but must not update user profile or nutrition state

### 2.8 Event Store

Responsibility: store immutable domain events as the canonical history of user-relevant changes.

Inputs:

- validated tool command
- actor context
- request context
- event payload
- idempotency key

Outputs:

- event id
- monotonic sequence
- event references for responses and projectors

Boundary:

- events are append-only
- corrections are represented by additional events
- events are not current state

### 2.9 Projectors and Projections

Responsibility: derive current read models from immutable events.

Projection families:

- user profile projection
- constraint projection
- nutrition status projection
- planning history projection

Boundary:

- projections are rebuildable
- projections are not manually edited by graph nodes
- projector offsets track processing progress

### 2.10 Planning Artifact Store

Responsibility: persist planning sessions, revisions, and versioned artifacts.

Planning artifacts are larger than individual events and are read frequently. They should be referenced by events but stored in dedicated tables or external object storage when they grow.

Boundary:

- generating a recommendation candidate does not imply persistence
- saving a plan artifact emits a domain event
- revisions supersede previous revisions explicitly

### 2.11 Evidence Adapter

Responsibility: provide a stable interface to evidence search and evidence support attachment.

Boundary:

- evidence may support explanations and recommendations
- evidence must not override safety, agent identity, user restrictions, or hard constraints
- V1 may use a stub or simple adapter until the evidence RAG matures

### 2.12 Observability Layer

Responsibility: capture traces, route decisions, tool executions, event references, safety outcomes, and projection lag.

Boundary:

- logs must not expose secrets or raw provider tokens
- traces should support debugging without becoming the source of truth

## 3. System Boundaries

### Internal Boundaries

```text
Auth resolution       -> agent identity only
Router                -> route decision only
LangGraph             -> orchestration only
Tools                 -> validation and side effects
Event store           -> historical truth
Projectors            -> rebuildable read state
Planning artifacts    -> versioned plan outputs
Evidence adapter      -> retrieval/support only
```

### External Systems

| External System | Used For | Boundary |
|---|---|---|
| Identity provider | login/auth claims | not owned by this repo |
| PostgreSQL | events, projections, route embeddings, planning records | canonical persistence for V1 |
| pgvector | router semantic search | route classification support only |
| LLM provider | reasoning, generation, fallback classification | not source of truth |
| Embedding provider | route embeddings | replaceable adapter |
| Evidence RAG | scientific support | external or stubbed in V1 |
| Observability backend | traces/logs/metrics | operational inspection only |
| Secret store | token/secret custody | tokens referenced, not stored raw |

## 4. Runtime Flow

```text
1. API receives authenticated user message.
2. Account Context Resolver creates AuthContext.
3. Request Normalizer creates normalized_text.
4. Safety Precheck evaluates obvious risk.
5. Intent Router embeds normalized_text and retrieves route candidates.
6. Router applies thresholds, margin checks, safety overrides, and fallback logic.
7. LangGraph dispatches to the selected graph branch.
8. Branch loads only required projections.
9. Branch exposes only allowed tools.
10. Tool handler validates input and safety class.
11. Write tool appends domain events with idempotency key.
12. Projectors update affected projections.
13. Response composer returns answer, event refs, route metadata, warnings, or clarification.
14. Observability layer records trace, route decision, tool execution, and errors.
```

## 5. Data Flow

```text
User Message
  -> RequestContext
  -> RouterDecision
  -> ToolCommand
  -> DomainEvent(s)
  -> Projection Update(s)
  -> ResponsePayload
```

Planning flow:

```text
Current Projections + Goal + Constraints
  -> diet.generate_recommendation
  -> Candidate Planning Artifact
  -> planning.manage_session
  -> plan.revision_created + plan.artifact_saved events
  -> PlanningHistoryProjection
```

Router embedding flow:

```text
Route Definition
  -> Route Example Texts
  -> Embedding Job
  -> intent_route_examples.embedding
  -> Runtime Similarity Search
  -> RouterDecision
```

## 6. Quality Attributes

The architecture prioritizes:

- recoverability: projections can be rebuilt from events
- auditability: route, event, and tool execution records are traceable
- safety: risky requests are blocked before mutation
- multilingual routing: embeddings handle Spanish/English input without hardcoded language dependence
- idempotency: retries do not duplicate events
- modularity: each graph branch exposes only relevant tools
- replaceability: embedding, LLM, evidence, and auth providers are adapters
- operational simplicity: V1 uses PostgreSQL as the main persistence surface

## 7. Implementation Order

Codex should implement in this order:

1. repository scaffold and configuration loading
2. PostgreSQL migrations from `300-CONTRACTS.md`
3. agent identity resolver
4. event store append/read with idempotency
5. projection tables and projectors
6. route definitions and embedding seed flow
7. embedding-assisted router with tests
8. LangGraph state and graph skeleton
9. safety precheck and clarification route
10. event capture tools
11. profile and goal tools
12. planning session/artifact tools
13. evidence adapter stubs
14. smoke tests and observability records

## 8. Related Documentation

- `README.md`
- `docs/000-SYSTEM-CONTEXT.md`
- `200-OPERATIONS.md`
- `300-CONTRACTS.md`
