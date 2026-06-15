# Plan: V1 Self-Harm Safety Precheck

## Task classification

- feature
- security
- data pipeline
- contract change
- documentation

## Goal

Implement a declarative V1 `safety_precheck` that detects self-harm risk from YAML rules, emits a structured decision, gates downstream routes/tools, and provides Aegis 2.0 dataset normalization/eval utilities.

## Scope

- Add a minimal generic safety rule engine.
- Add self-harm rules, decision matrix, and tool gates in YAML.
- Replace the graph precheck implementation with the new engine.
- Keep router behavior for safe inputs unchanged.
- Add focused tests for loading, matching, golden positives, hard negatives, and graph routing fields.
- Add basic Aegis loader/normalizer/eval scripts without committing dataset contents.

## Assumptions

- `context_bootstrap` may provide translated English safety text in `request.normalized_text`; V1 uses that as the primary safety input.
- Existing graph route names can represent safety outcomes through `SafetyTriageRoute` and `EmergencySupportResponse` in safety state, even if only the router graph branch is fully skeletal today.
- Aegis data is an offline governed source; network access is not required for unit tests.

## Steps

1. Add safety engine schemas, rule loader, evaluator, decision resolver, and precheck service.
2. Add self-harm YAML rules, decision matrix, tool gates, and Aegis data-source metadata.
3. Integrate graph `safety_precheck` with the new service and remove deprecated hardcoded self-harm logic from Python paths.
4. Add Aegis loader, normalizer, and eval runner scripts.
5. Add focused tests and run validation.

## Validation

```bash
uv run --extra test pytest tests/safety/test_self_harm_rules.py tests/agent/test_graph.py tests/routing/test_safety_gate.py
uv run --extra test victus check
```

## Risks

- Router still has broader safety behavior; the compatibility wrapper must not route safe inputs differently.
- Full Aegis evaluation depends on downloading external data and is intentionally outside default tests.
