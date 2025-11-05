from studybuddy import study_tip

def test_study_tip_returns_string():
    assert isinstance(study_tip("math", "chaotic"), str)

def test_study_tip_fallback_category():
    assert " " in study_tip("unknown", "chaotic")

def test_study_tip_deterministic():
    a = study_tip("history", "lazy", seed=42)
    b = study_tip("history", "lazy", seed=42)
    assert a == b
