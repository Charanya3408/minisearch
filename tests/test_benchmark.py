import random

from minisearch.benchmark import run


def synthetic_docs(n=60, seed=3):
    rng = random.Random(seed)
    vocab = [f"word{i}" for i in range(80)]
    return [{"id": str(i), "title": f"d{i}", "text": " ".join(rng.choices(vocab, k=40))} for i in range(n)]


def test_index_and_scan_return_identical_results():
    rows = run(synthetic_docs(), sizes=[20, 60], n_queries=25)
    assert [r["docs"] for r in rows] == [20, 60]
    assert all(r["mismatches"] == 0 for r in rows)
    assert all(r["index_ms"] > 0 and r["scan_ms"] > 0 for r in rows)
