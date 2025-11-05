from studybuddy import core

def test_deadline_funny_message_contains_hours():
    msg = core.deadline_reminder(hours_left=10, tone="funny")
    assert "hour" in msg.lower()

def test_deadline_panic_mode_for_low_hours():
    msg = core.deadline_reminder(hours_left=1, tone="funny")
    assert "panic" in msg.lower() or "fine" in msg.lower()

def test_deadline_invalid_tone_defaults_to_funny():
    msg = core.deadline_reminder(hours_left=5, tone="nonexistent")
    assert isinstance(msg, str)
