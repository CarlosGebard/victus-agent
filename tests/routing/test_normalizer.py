from victus_routing.normalizer import normalize_text


def test_normalize_text_lowercases_strips_whitespace_and_accents() -> None:
    assert normalize_text("  Qué   DICE   la evidéncia?  ") == "que dice la evidencia?"
