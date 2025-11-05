from studybuddy import affirmation, challenge

def test_affirmation_returns_string():
    result = affirmation(seed=1)
    assert isinstance(result, str)
    assert len(result) > 0

def test_affirmation_repeatable_with_seed():
    result1 = affirmation(seed=42)
    result2 = affirmation(seed=42)
    assert result1 == result2 


def test_affirmation_varies_without_seed():
    result1 = affirmation()
    result2 = affirmation()
    assert result1 != result2 

def test_challenge_returns_string():
    result = challenge(seed=2)
    assert isinstance(result, str)
    assert "Study" in result or "Quiz" in result or "pages" in result


def test_challenge_repeatable_with_seed():
    result1 = challenge(seed=10)
    result2 = challenge(seed=10)
    assert result1 == result2


def test_challenge_is_deterministic():
    """Ensure challenge() gives consistent output for the same seed."""
    r1 = challenge(seed=7)
    r2 = challenge(seed=7)
    assert r1 == r2