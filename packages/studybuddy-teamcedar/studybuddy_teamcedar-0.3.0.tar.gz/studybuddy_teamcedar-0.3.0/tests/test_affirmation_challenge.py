from studybuddy import affirmation, challenge

def test_affirmation_returns_string():
    result = affirmation(seed=1)
    assert isinstance(result, str)
    assert len(result) > 0

def test_challenge_returns_string():
    result = challenge(seed=2)
    assert isinstance(result, str)
    assert "Study" in result or "Quiz" in result or "pages" in result