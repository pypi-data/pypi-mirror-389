from studybuddy import core

def test_study_playlist_default():
    pl = core.study_playlist(seed=0)
    assert isinstance(pl, list)
    assert len(pl) == 3

def test_study_playlist_chill_mode():
    pl = core.study_playlist(mood="chill", n=2, seed=1)
    assert all("chill" in p.lower() or "relax" in p.lower() for p in pl)

def test_study_playlist_length_matches_request():
    pl = core.study_playlist(n=5, seed=2)
    assert len(pl) == 5
