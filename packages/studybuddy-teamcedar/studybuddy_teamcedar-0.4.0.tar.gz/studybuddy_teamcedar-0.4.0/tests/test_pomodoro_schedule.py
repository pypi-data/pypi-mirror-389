from studybuddy import core

def test_pomodoro_basic_structure():
    sched = core.pomodoro_schedule(sessions=2, work_minutes=25, break_minutes=5)
    assert sched[0].startswith("Session 1")
    assert sched[-1].startswith("🎉")

def test_pomodoro_includes_breaks():
    sched = core.pomodoro_schedule(sessions=3)
    assert any("Short break" in s for s in sched)

def test_pomodoro_long_break_every_four_sessions():
    sched = core.pomodoro_schedule(sessions=8)
    assert any("Long break" in s for s in sched)
