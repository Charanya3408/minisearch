"""Inverted index with BM25 ranking, written from scratch."""
import heapq
import json
import math
from collections import defaultdict

from .tokenizer import tokenize


class InvertedIndex:
    def __init__(self, k1: float = 1.5, b: float = 0.75, phrase_boost: float = 0.75):
        self.k1 = k1  # how quickly repeated terms stop adding score
        self.b = b    # how strongly long documents are penalised
        self.phrase_boost = phrase_boost  # bonus when query words appear side by side
        self.positions: dict[str, dict[str, list[int]]] = defaultdict(dict)  # term -> {doc_id: [positions]}
        self.postings: dict[str, dict[str, int]] = defaultdict(dict)  # term -> {doc_id: tf}
        self.doc_len: dict[str, int] = {}
        self.docs: dict[str, dict[str, str]] = {}
        self._total_len = 0

    def __len__(self) -> int:
        return len(self.doc_len)

    @property
    def avg_doc_len(self) -> float:
        return self._total_len / len(self.doc_len) if self.doc_len else 0.0

    def add_document(self, doc_id: str, text: str, title: str = "") -> None:
        if doc_id in self.doc_len:
            raise ValueError(f"duplicate document id: {doc_id}")
        tokens = tokenize(text)
        self.doc_len[doc_id] = len(tokens)
        self._total_len += len(tokens)
        self.docs[doc_id] = {"title": title or doc_id, "text": text}
        by_term: dict[str, list[int]] = defaultdict(list)
        for pos, term in enumerate(tokens):
            by_term[term].append(pos)
        for term, plist in by_term.items():
            self.postings[term][doc_id] = len(plist)
            self.positions[term][doc_id] = plist

    def idf(self, term: str) -> float:
        """Rare terms score higher. The +1 keeps the value positive."""
        n = len(self.postings.get(term, ()))
        total = len(self.doc_len)
        return math.log(1 + (total - n + 0.5) / (n + 0.5))

    def phrase_count(self, doc_id: str, terms: list[str]) -> int:
        """How many times the terms appear next to each other, in order."""
        first = self.positions.get(terms[0], {}).get(doc_id)
        if not first:
            return 0
        rest = []
        for term in terms[1:]:
            found = self.positions.get(term, {}).get(doc_id)
            if not found:
                return 0
            rest.append(set(found))
        return sum(all(start + i + 1 in r for i, r in enumerate(rest)) for start in first)

    def search(self, query: str, k: int = 10, phrase: bool = True) -> list[tuple[str, float]]:
        """Return the top k (doc_id, score) pairs. Only documents that share
        a term with the query are ever touched, which is the point of the index."""
        scores: dict[str, float] = defaultdict(float)
        avgdl = self.avg_doc_len
        tokens = tokenize(query)
        for term in set(tokens):
            posting = self.postings.get(term)
            if not posting:
                continue
            idf = self.idf(term)
            for doc_id, tf in posting.items():
                norm = 1 - self.b + self.b * self.doc_len[doc_id] / avgdl
                scores[doc_id] += idf * tf * (self.k1 + 1) / (tf + self.k1 * norm)
        if phrase and len(tokens) > 1 and all(t in self.postings for t in set(tokens)):
            bonus = self.phrase_boost * sum(self.idf(t) for t in set(tokens))
            for doc_id in scores:
                if self.phrase_count(doc_id, tokens):
                    scores[doc_id] += bonus
        # Heap-based top-k: O(n log k) instead of sorting every match.
        return heapq.nsmallest(k, scores.items(), key=lambda kv: (-kv[1], kv[0]))

    def save(self, path: str) -> None:
        data = {"k1": self.k1, "b": self.b, "phrase_boost": self.phrase_boost, "docs": self.docs,
                "doc_len": self.doc_len, "postings": self.postings, "positions": self.positions}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    @classmethod
    def load(cls, path: str) -> "InvertedIndex":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        index = cls(data["k1"], data["b"], data["phrase_boost"])
        index.docs = data["docs"]
        index.doc_len = data["doc_len"]
        index._total_len = sum(index.doc_len.values())
        index.postings = defaultdict(dict, data["postings"])
        index.positions = defaultdict(dict, data["positions"])
        return index
