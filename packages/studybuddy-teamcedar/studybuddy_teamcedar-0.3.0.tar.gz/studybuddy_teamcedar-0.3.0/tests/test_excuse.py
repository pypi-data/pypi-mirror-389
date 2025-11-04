from studybuddy import excuse

def test_excuse_type():
    assert isinstance(excuse("homework"), str)

def test_excuse_reason_variation():
    a = excuse("exam", seed=1)
    b = excuse("homework", seed=1)
    assert a != b

def test_excuse_deterministic():
    a = excuse("late", seed=3)
    b = excuse("late", seed=3)
    assert a == b
