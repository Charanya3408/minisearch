"""Measure the inverted index against scanning every document."""
import argparse
import heapq
import json
import random
import time
from collections import Counter
from pathlib import Path

from .index import InvertedIndex
from .tokenizer import tokenize


def load_docs() -> list[dict]:
    for name in ("data/articles_large.json", "data/articles.json"):
        path = Path(name)
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    raise SystemExit("No corpus found. Run: python -m minisearch.crawl --random 3000")


def make_queries(index: InvertedIndex, count: int, seed: int = 1) -> list[str]:
    """Two random words from a random document, so every query has real matches."""
    rng, ids, queries = random.Random(seed), sorted(index.docs), []
    for _ in range(count * 20):
        tokens = tokenize(index.docs[rng.choice(ids)]["text"])
        if len(tokens) >= 3:
            queries.append(" ".join(rng.sample(tokens, 2)))
        if len(queries) == count:
            break
    return queries


def scan_search(index: InvertedIndex, forward: dict, query: str, k: int = 10):
    """Baseline: visit every document and score it (same BM25 formula, no inverted lookup)."""
    terms = set(tokenize(query))
    idf = {t: index.idf(t) for t in terms}
    avgdl, scores = index.avg_doc_len, []
    for doc_id, counts in forward.items():
        norm = 1 - index.b + index.b * index.doc_len[doc_id] / avgdl
        score = 0.0
        for t in terms:
            tf = counts.get(t, 0)
            if tf:
                score += idf[t] * tf * (index.k1 + 1) / (tf + index.k1 * norm)
        if score:
            scores.append((doc_id, score))
    return heapq.nsmallest(k, scores, key=lambda kv: (-kv[1], kv[0]))


def run(docs: list[dict], sizes: list[int], n_queries: int = 200, k: int = 10) -> list[dict]:
    rows = []
    for size in sizes:
        subset = docs[:size]
        t0 = time.perf_counter()
        index = InvertedIndex()
        for d in subset:
            index.add_document(d["id"], d["text"], d["title"])
        build_ms = (time.perf_counter() - t0) * 1000
        forward = {d["id"]: Counter(tokenize(d["text"])) for d in subset}  # prepared outside the timing
        queries = make_queries(index, n_queries)

        t0 = time.perf_counter()
        fast = [index.search(q, k, phrase=False) for q in queries]
        index_ms = (time.perf_counter() - t0) * 1000 / len(queries)
        t0 = time.perf_counter()
        slow = [scan_search(index, forward, q, k) for q in queries]
        scan_ms = (time.perf_counter() - t0) * 1000 / len(queries)

        mismatches = sum([d for d, _ in a] != [d for d, _ in b] for a, b in zip(fast, slow))
        rows.append({"docs": len(subset), "queries": len(queries), "build_ms": build_ms,
                     "index_ms": index_ms, "scan_ms": scan_ms,
                     "speedup": scan_ms / index_ms if index_ms else float("inf"), "mismatches": mismatches})
    return rows


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Benchmark the index against a full scan.")
    parser.add_argument("--queries", type=int, default=200)
    parser.add_argument("--sizes", type=int, nargs="+", default=[100, 500, 1000, 2000, 4000])
    args = parser.parse_args(argv)
    docs = load_docs()
    sizes = sorted({s for s in args.sizes if s <= len(docs)} | {len(docs)})
    rows = run(docs, sizes, args.queries)
    print(f"\nTop-10 BM25, {rows[0]['queries']} two-word queries per size (phrase bonus off for a fair comparison)\n")
    print("| Documents | Index (ms/query) | Full scan (ms/query) | Speedup | Index build (ms) |")
    print("|---:|---:|---:|---:|---:|")
    for r in rows:
        print(f"| {r['docs']} | {r['index_ms']:.3f} | {r['scan_ms']:.3f} | {r['speedup']:.0f}x | {r['build_ms']:.0f} |")
    bad = sum(r["mismatches"] for r in rows)
    print(f"\nResult agreement: {'identical top-10 lists in every query' if not bad else f'{bad} queries differed'}")


if __name__ == "__main__":
    main()
