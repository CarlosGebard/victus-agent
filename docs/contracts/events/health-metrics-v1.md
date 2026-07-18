---
id: VICTUS-CONTRACT-EVENTS-HEALTH-METRICS-V1
title: Health Metric Events V1
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Health Metric Events V1

Implemented in `src/domain/events/health_metrics.py`.

Active event types:

- `biometrics.logged`
- `lifestyle_metric.logged`
- `symptom.logged`

Currently emitted by tools:

- `event_capture.actions.log_biometrics` emits `biometrics.logged`.
- `event_capture.actions.log_lifestyle_metric` emits `lifestyle_metric.logged`.
- `event_capture.actions.log_symptom` emits `symptom.logged` only for non-safety-blocked symptoms.

High-risk symptoms must not emit `symptom.logged` until safety validation exists.
