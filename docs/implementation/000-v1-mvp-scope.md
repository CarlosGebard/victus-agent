---
id: VICTUS-IMPLEMENTATION-V1-MVP-SCOPE
title: Victus Agent V1 MVP Scope
status: draft
version: v1
owner: victus-agent-runtime
updated_at: 2026-06-12
---
# Victus Agent V1 MVP Scope

## 1. Goal

Create the first runnable Victus Lifestyle Agent skeleton.

V1 is successful when the system can take a user message, route it, validate it, call the correct typed tool, write immutable events when needed, rebuild projections, and return a grounded response or clarification.

The V1 domain is nutrition and lifestyle support. Workout generation is out of scope; exercise/training details are accepted only when they inform nutrition context or safety triage.

## 2. In Scope

- PostgreSQL event store
- projector offsets
- core projections
- LangGraph state and routing
- safety precheck
- intent router
- event capture node
- profile update node
- plan intent node
- evidence answer adapter node
- clarification node
- common tool result envelope
- tool handlers for currently documented tools
- basic response composer
- tests for routing, writes, projections, and safety blocks

## 3. Out of Scope

- full medical advice
- diagnosis
- full food database integration
- accurate macro and micronutrient estimation
- advanced optimization engine
- full RAG retrieval quality
- long-term analytics dashboards
- workout program generation
- multi-user product UI
- wearables integration
- notifications

## 4. V1 Quality Bar

The system should be conservative and traceable.

A small number of reliable actions is better than many loosely modeled actions.

The implementation should prefer `needs_clarification` over guessing when identifiers, quantities, timestamps, or safety-relevant details are missing.
