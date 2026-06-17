# Llama Guard safety-precheck restructure

## Goal

Move `safety_precheck` to the first graph node and make its first standalone test path use an injectable Llama Guard model decision instead of YAML rule matching.

## Scope

- Keep the existing `state["safety"]` shape for downstream compatibility.
- Add runtime config for the safety model.
- Use the existing LLM port so tests can stub the model.
- Update graph tests for the new node order.

## Assumptions

- `Llama-Guard-3-1B` is loaded locally through `transformers`.
- Llama Guard returns text beginning with `safe` or `unsafe`.
- Dataset/eval cleanup is a later change, not part of this first cut.

## Steps

1. Add `safety.model` runtime config.
2. Replace graph safety precheck execution with an injectable Llama Guard call.
3. Move `safety_precheck` before normalization/context bootstrap.
4. Update focused tests with a stubbed Llama Guard response.

## Validation

- `uv run pytest tests/agent/test_graph.py tests/application/test_config.py`

## Risks

- If local model output format differs from standard Llama Guard, parser may need adjustment.
- Running safety before normalization means it checks the raw/original user text.

# ProfileUpdateNode V1

## Goal

Implement a V1 profile update classifier node that returns a validated `ProfileUpdateDecision` for durable or slow-changing user profile changes.

## Scope

- Add the profile update node package under the existing `src/agent/nodes/` package layout.
- Keep the node free of database writes, event emission, plan creation/revision, meal logging, goal mutation, and science answers.
- Support deterministic policy decisions for obvious cases and optional LLM-backed JSON decisions through the existing LLM port.
- Enforce hard validation rules before returning a decision.

## Assumptions

- The repository package layout makes `src/agent/nodes/profile_update/` the smallest importable location.
- Command handlers outside this node will consume the decision and emit events.
- No tests are added for this task per request.

## Steps

1. Add schemas, prompts, skill manifest, and event mapping.
2. Add deterministic policy helpers for reroutes, restrictions, preferences, removals, and ambiguity.
3. Add validators that enforce the hard safety and shape rules.
4. Add a thin node wrapper that uses LLM output when configured and falls back to policy heuristics.
5. Run compile validation.

## Validation

- `uv run python -m compileall src/agent/nodes/profile_update`

## Risks

- Heuristics are intentionally conservative and will not cover every phrasing in V1.
- Without tests in this task, validation is limited to import/compile checks.

# EventCaptureNode V1

## Goal

Implement a V1 event capture classifier node that returns a validated `EventCaptureDecision` for fast-changing user data.

## Scope

- Add the event capture node package under the existing `src/agent/nodes/` package layout.
- Keep the node free of database writes, event emission, planning, goal changes, durable profile updates, scientific answers, and nutrition calculations.
- Support meals, biometrics, lifestyle metrics, and symptoms.
- Add the `lifestyle_metric.logged` event registry entry and update node documentation.

## Assumptions

- The repository package layout makes `src/agent/nodes/event_capture/` the smallest importable location.
- Command handlers outside this node will consume decisions and emit events.
- No tests are added for this task per request.

## Steps

1. Add schemas, prompts, skill manifest, and event mapping.
2. Add deterministic policy helpers for reroutes, edit/delete ambiguity, biometrics, lifestyle metrics, meals, symptoms, and high-risk symptom detection.
3. Add validators that enforce hard shape, action, event, safety, and no-invented-nutrition rules.
4. Add a thin node wrapper that uses LLM output when configured and falls back to policy heuristics.
5. Update event registry and Event Capture Node documentation.
6. Run compile validation and focused smoke checks.

## Validation

- `uv run python -m compileall src/agent/nodes/event_capture`

## Risks

- Heuristics are intentionally conservative and will not cover every phrasing in V1.
- Without tests in this task, validation is limited to compile and smoke checks.
