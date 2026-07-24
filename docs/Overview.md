# Victus Agent Overview

## Purpose

Victus Agent is the conversational runtime that connects Victus users with lifestyle and nutrition
capabilities. It interprets a user turn, applies safety and identity controls, selects an appropriate
capability, coordinates any required clarification or confirmation, and returns a bounded response.

This repository contains the agent runtime rather than the complete Victus product. User interfaces,
the main Victus backend, and broader product experiences remain outside its ownership.

## Current State

The system is a testable first-version runtime built around a tool-first architecture. It supports
multi-turn conversations, model-guided capability selection, controlled tool execution, persistent
domain history, rebuildable user views, and bounded conversational memory.

The runtime can operate with in-memory persistence for deterministic testing or with PostgreSQL for
a durable deployment. Full acceptance of provider-backed behavior depends on configured external
model, identity, and database services.

It is not yet a complete autonomous nutrition coach. Its current value is the stable runtime
foundation on which richer product behavior can be built.

## System Responsibilities

The runtime owns:

- conversational orchestration and bounded multi-turn continuity;
- selection and execution of the registered Victus capabilities;
- validation of capability inputs and normalization of their results;
- safety checks before model-directed execution;
- authenticated identity propagation and conversation ownership;
- immutable user-event persistence and rebuildable projections;
- clarification and confirmation pauses for incomplete or sensitive actions;
- consistent capability exposure through chat, MCP, local command-line access, and tests;
- dependency assembly, runtime configuration, and persistence integration.

The runtime does not own:

- the main Victus web or mobile experience;
- the authoritative external user account system;
- general medical diagnosis or emergency care;
- unrestricted autonomous actions;
- unbounded long-term conversation storage;
- background job orchestration or distributed workflow processing;
- provider infrastructure for language models, identity, or databases.

## Architectural Shape

Victus Agent is organized around a single capability runtime. Each capability has one registered
definition and one implementation. Every access surface delegates execution to that same runtime,
which prevents chat, MCP, command-line, and test behavior from drifting into separate versions.

The system has five conceptual layers:

1. **Capabilities** define user-facing actions and their accepted inputs, outcomes, risk, and side
   effects.
2. **Domain** represents durable user events, rebuildable projections, session concepts, and shared
   business invariants.
3. **Orchestration and access adapters** translate conversations or external requests into capability
   invocations without owning business behavior.
4. **Platform services** provide persistence, model access, safety classification, identity,
   configuration, and telemetry.
5. **Bootstrap** assembles the runtime and supplies concrete dependencies to the access surfaces.

Dependencies point inward toward stable capability and domain concepts. Capabilities do not depend
on a particular conversational graph, transport, command-line interface, or database implementation.

## Conversation Lifecycle

A conversation begins with an authenticated user turn associated with a conversation identity. The
runtime normalizes the request, recalls bounded conversational memory, loads relevant domain views,
and performs a safety assessment.

If the turn is allowed, the model receives the available capability definitions and chooses either a
direct response or one capability invocation. The runtime validates that proposal before execution.
Actions that need explicit approval pause for confirmation. Actions missing required information
pause for clarification. Both resume within the same owned conversation.

After execution, the result is returned to the conversational graph. The graph may make another
bounded decision or compose the final response. It then updates eligible conversational memory and
finalizes the turn. Safety blocks, invalid proposals, and execution failures are represented as
controlled outcomes rather than bypassing the runtime boundary.

## Capability Landscape

The current public capability is capturing meals and beverages.

Capabilities are intentionally narrow. A capability may emit domain events, request continuation,
return data, or reject an unsafe or invalid action. Adding or renaming a public capability changes a
stable system boundary and must be treated accordingly.

## Data and Memory Model

The system separates domain truth from conversational continuity.

Immutable user events are the historical source of truth for user activity and durable changes.
Projections are current read models derived from those events and can be rebuilt. Successful event
persistence updates the affected projection as part of the same durable operation.

Conversational checkpoints preserve the state required to continue a specific thread, including
pending clarification or confirmation. Cross-thread agent memory stores a small, policy-controlled
set of non-domain conversational facts and interaction preferences. Neither form of conversational
memory replaces events or projections as the source of user truth.

This separation keeps conversational convenience from silently becoming an alternative profile or
health record.

## Interfaces and External Systems

The runtime exposes an authenticated chat service, MCP transports for local and deployable tool
access, and command-line entrypoints for local operation and validation. These interfaces share the
same capability catalog and execution boundary.

PostgreSQL provides durable event, projection, checkpoint, and conversational-memory storage.
LangGraph coordinates the conversation lifecycle. LiteLLM provides model access, while a dedicated
safety model can classify unsafe requests. The Victus backend validates bearer identities and is the
external source for authenticated profile retrieval.

These dependencies are replaceable infrastructure integrations. Business decisions remain inside
the capability and domain boundaries.

## Trust, Safety, and Identity

Identity is resolved by an adapter and checked by the capability runtime. It is never inferred from
free-form model output. Conversation state is scoped to both the authenticated user and the owned
conversation, preventing one user from resuming another user's thread.

Tool names, inputs, exposure, risk, side effects, and identity requirements come from one canonical
catalog. Model output is treated as a proposal and must pass catalog, schema, identity,
authorization, and safety checks before execution.

Sensitive actions can require explicit confirmation, and incomplete actions can require structured
clarification. Secrets and provider credentials are configuration concerns and must not become
ordinary conversational or domain data.

## Operational Model

A durable deployment consists of PostgreSQL, database migrations, conversational storage setup, the
authenticated chat service, and the MCP service. Startup ordering ensures persistence is ready before
the runtime begins serving dependent interfaces.

The chat and MCP services remain separate access boundaries even though they share the same runtime.
Health checks describe service readiness, while optional debug visibility is intentionally gated and
must retain normal authentication and conversation-ownership controls.

Local development can replace durable graph storage and external integrations with controlled test
doubles. This keeps the core behavior deterministic without changing the production architecture.

## Design Principles

- **One capability implementation:** every interface executes the same registered behavior.
- **Tool-first orchestration:** the model proposes actions; the runtime validates and executes them.
- **Explicit boundaries:** adapters translate, capabilities decide, and platform services provide
  infrastructure.
- **Durable domain truth:** events are authoritative and projections are derived.
- **Bounded state:** graph state and cross-thread memory are limited to their orchestration purpose.
- **Authenticated ownership:** identity and conversation access are verified outside model control.
- **Fail-closed behavior:** unsafe, unauthorized, invalid, or ambiguous actions do not execute.
- **Stable public contracts:** capability names, schemas, event shapes, and external interfaces evolve
  deliberately.
- **Operational simplicity:** local and durable deployments use the same conceptual system shape.

## Current Limitations and Direction

The current runtime deliberately favors a small, inspectable foundation over broad autonomy. It does
not provide streaming conversation, multi-agent delegation, semantic or vector-based conversational
memory, distributed background work, or medical diagnosis. Production readiness still depends on
the surrounding identity, provider, observability, and deployment environment.

Future development should extend the existing capability runtime and preserve the separation between
domain truth, conversational state, and infrastructure. New behavior should become active only when
its implementation and stable boundary agree.

## Documentation Policy

This overview is the current conceptual system document. `Tools.md`, `Events.md`, and
`Projections.md` document the fundamental system pieces. [Graph-Flow.md](Graph-Flow.md) documents
the current LangGraph nodes and routes. Specialized contracts live under `docs/contracts/`.
Documentation should guide readers while the code remains authoritative. The overview must not
contain source code, command sequences, detailed schemas, runbooks, or numbered documentation
stages.
