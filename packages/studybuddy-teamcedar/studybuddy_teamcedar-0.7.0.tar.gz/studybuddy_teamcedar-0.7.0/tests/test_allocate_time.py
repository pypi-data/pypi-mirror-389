import studybuddy as s


def test_allocate_sum_and_min_chunk():
    topics = {"algo": 3, "db": 2, "net": 1}
    alloc = s.allocate_time(topics, total_minutes=125, min_chunk=5)
    assert sum(alloc.values()) == 125
    assert all(v % 5 == 0 for v in alloc.values())
    assert set(alloc) == set(topics)


def test_allocate_respects_weights():
    topics = {"hard": 5, "easy": 1}
    alloc = s.allocate_time(topics, total_minutes=60, min_chunk=5)
    assert alloc["hard"] > alloc["easy"]


def test_allocate_edge_cases():
    assert s.allocate_time({}, 50) == {}
    alloc = s.allocate_time({"one": 0}, 0)
    assert alloc["one"] == 0
