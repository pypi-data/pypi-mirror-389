import re
from studybuddy import core

def test_roast_default_behavior():
    msg = core.roast(seed=0)
    assert isinstance(msg, str)
    assert any(word in msg.lower() for word in ["code", "bugs", "algorithm", "variable"])

def test_roast_low_intensity():
    msg = core.roast(intensity=2, seed=1)
    assert msg.lower().startswith("gently speaking")
    assert msg == msg.lower()  # lowercased for gentle tone

def test_roast_high_intensity():
    msg = core.roast(intensity=9, seed=2)
    assert msg.isupper() or msg.endswith("🔥")
