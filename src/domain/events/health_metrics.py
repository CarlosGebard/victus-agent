from __future__ import annotations

from typing import Literal

from domain.events.base import ContractModel, Severity

BiometricType = Literal["weight", "height", "sleep", "steps", "body_fat", "waist", "other"]
BiometricSource = Literal["manual", "wearable", "import"]


class BiometricMeasurement(ContractModel):
    type: BiometricType
    value: float
    unit: str


class BiometricsLoggedPayload(ContractModel):
    measurement_id: str
    measured_at: str
    measurements: list[BiometricMeasurement]
    source: BiometricSource


class LifestyleMetricLoggedPayload(ContractModel):
    metric_id: str
    occurred_at: str
    metric: Literal["sleep_duration", "water_intake", "steps", "stress", "energy", "hunger"]
    value: float | str | None = None
    unit: str | None = None
    raw_value_text: str | None = None
    source: Literal["manual", "wearable", "import"]


class SymptomLoggedPayload(ContractModel):
    symptom_id: str
    occurred_at: str
    label: str
    severity: Severity | None = None
    duration: str | None = None
    notes: str | None = None
    safety_checked: bool
