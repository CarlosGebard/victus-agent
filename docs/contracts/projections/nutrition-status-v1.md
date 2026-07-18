---
id: VICTUS-CONTRACT-PROJECTION-NUTRITION-STATUS-V1
title: Nutrition Status Projection V1
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Nutrition Status Projection V1

Implemented in:

- `src/domain/projections/models/nutrition_status.py`
- `src/domain/projections/projectors/nutrition_status.py`

Consumes:

- `meal.logged`
- `meal.deleted`
- `biometrics.logged`
- `lifestyle_metric.logged`
- `symptom.logged`
