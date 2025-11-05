from studybuddy import core

def test_break_idea_default():
    idea = core.break_idea(seed=0)
    assert "break" in idea.lower()
    assert any(word in idea.lower() for word in ["stretch", "minute"])

def test_break_idea_long():
    idea = core.break_idea(minutes=10, activity="walk", seed=1)
    assert "extended" in idea.lower()
    assert "walk" in idea.lower()

def test_break_invalid_activity_defaults_to_stretch():
    idea = core.break_idea(activity="invalid", seed=2)
    assert "stretch" in idea.lower()
