from __future__ import annotations

import re

from application.routing.models import SafetyGateResult
from application.routing.normalizer import normalize_text


class SafetyGate:
    """Deterministic Spanish/English safety gate that runs before embeddings."""

    def __init__(self) -> None:
        self._urgent_patterns = [
            (re.compile(r"\b(chest pain|pain in my chest|me duele el pecho|dolor de pecho)\b"), "urgent cardiopulmonary symptom"),
            (re.compile(r"\b(shortness of breath|can't breathe|cannot breathe|me falta el aire|falta de aire)\b"), "urgent respiratory symptom"),
            (re.compile(r"\b(suicid|kill myself|hurt myself|self harm|autolesion|quitarme la vida|suicidar)\w*\b"), "self-harm language"),
        ]
        self._high_patterns = [
            (re.compile(r"\b(faint|fainting|pass out|desmayar|desmayo|voy a desmayar|severe dizziness|mareo severo)\b"), "fainting or severe dizziness risk"),
            (re.compile(r"\b(extreme dose|dangerous dose|overdose|dosis extrema|sobredosis)\b.*\b(caffeine|cafeina|supplement|suplemento)\b"), "unsafe extreme dosing"),
            (re.compile(r"\b(caffeine|cafeina|supplement|suplemento)\b.*\b(extreme dose|dangerous dose|overdose|dosis extrema|sobredosis)\b"), "unsafe extreme dosing"),
            (re.compile(r"\b(diabetes|hypertension|hipertension|presion alta)\b.*\b(stop|quit|leave|dejar|suspender)\b.*\b(medication|medicine|medications|medicamentos|medicina)\b"), "risky medication change request"),
        ]
        self._medium_patterns = [
            (re.compile(r"\b(diabetes|hypertension|hipertension|presion alta|heart disease|cardiopatia)\b.*\b(can i|puedo|should i|deberia)\b"), "medical condition with personal advice request"),
            (re.compile(r"\b(can i|puedo|should i|deberia)\b.*\b(diabetes|hypertension|hipertension|presion alta|heart disease|cardiopatia)\b"), "medical condition with personal advice request"),
            (re.compile(r"\b(diabetes|hypertension|hipertension|presion alta|heart disease|cardiopatia)\b.*\b(take|use|tomar|usar)\b.*\b(creatine|creatina|caffeine|cafeina|supplement|suplemento)\b"), "medical condition with supplement advice request"),
        ]

    def check(self, text: str) -> SafetyGateResult:
        normalized = normalize_text(text)

        urgent_reasons = [reason for pattern, reason in self._urgent_patterns if pattern.search(normalized)]
        if urgent_reasons:
            return SafetyGateResult(triggered=True, reason=", ".join(sorted(set(urgent_reasons))), severity="urgent")

        for pattern, reason in self._high_patterns:
            if pattern.search(normalized):
                return SafetyGateResult(triggered=True, reason=reason, severity="high")

        for pattern, reason in self._medium_patterns:
            if pattern.search(normalized):
                return SafetyGateResult(triggered=True, reason=reason, severity="medium")

        return SafetyGateResult(triggered=False, severity="none")
