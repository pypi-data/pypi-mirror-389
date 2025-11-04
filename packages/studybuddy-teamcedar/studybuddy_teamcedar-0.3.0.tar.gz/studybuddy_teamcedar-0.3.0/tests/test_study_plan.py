from studybuddy import study_plan

def test_study_plan_list():
    assert isinstance(study_plan(2), list)

def test_study_plan_length():
    assert len(study_plan(4)) == 4

def test_study_plan_deterministic():
    a = study_plan(3, "high", seed=5)
    b = study_plan(3, "high", seed=5)
    assert a == b
