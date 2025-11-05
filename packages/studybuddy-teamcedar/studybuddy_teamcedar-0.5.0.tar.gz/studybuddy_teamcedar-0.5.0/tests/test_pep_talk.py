from studybuddy import core

def test_pep_talk_default():
    msg = core.pep_talk(name="Kylie", goal="finish this project", seed=0)
    assert "Kylie" in msg
    assert "finish this project" in msg

def test_pep_talk_funny():
    msg = core.pep_talk(name="Alex", goal="ace the exam", theme="funny", seed=1)
    assert "Alex" in msg
    assert "ace the exam" in msg

def test_pep_talk_tough_love():
    msg = core.pep_talk(name="Sam", goal="study 2 hours", theme="tough_love", seed=2)
    assert "Sam" in msg
    assert "study 2 hours" in msg
