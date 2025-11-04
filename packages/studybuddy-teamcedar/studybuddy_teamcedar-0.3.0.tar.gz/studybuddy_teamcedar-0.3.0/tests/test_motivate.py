from studybuddy import motivate

def test_motivate_returns_string():
    assert isinstance(motivate("genuine"), str)

def test_motivate_styles():
    sarcastic = motivate("sarcastic", seed=1)
    genuine = motivate("genuine", seed=1)
    assert sarcastic != genuine

def test_motivate_deterministic():
    a = motivate("sarcastic", seed=2)
    b = motivate("sarcastic", seed=2)
    assert a == b
