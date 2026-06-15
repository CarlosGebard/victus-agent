from application.routing.safety_gate import SafetyGate


def test_urgent_chest_pain_and_shortness_of_breath() -> None:
    result = SafetyGate().check("me duele el pecho y me falta el aire")
    assert result.triggered is True
    assert result.severity == "urgent"


def test_high_fainting_symptom() -> None:
    result = SafetyGate().check("siento que me voy a desmayar")
    assert result.triggered is True
    assert result.severity == "high"


def test_high_extreme_caffeine_dose() -> None:
    result = SafetyGate().check("quiero tomar una dosis extrema de cafeína")
    assert result.triggered is True
    assert result.severity == "high"


def test_high_medication_change() -> None:
    result = SafetyGate().check("tengo diabetes, puedo dejar mis medicamentos?")
    assert result.triggered is True
    assert result.severity == "high"


def test_medium_condition_personal_advice() -> None:
    result = SafetyGate().check("tengo presión alta y quiero tomar creatina")
    assert result.triggered is True
    assert result.severity == "medium"
