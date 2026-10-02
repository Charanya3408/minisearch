"""Pick the sentence that best answers a query. Extractive: it quotes, it never invents."""
import re

from .tokenizer import tokenize

_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def sentences(text: str) -> list[str]:
    parts = _SENTENCE.split(" ".join(text.split()))
    return [p.strip() for p in parts if len(p.strip()) > 20]


def best_answer(index, query: str, top_docs: int = 5, min_coverage: float = 0.6):
    """Return {sentence, doc_id, title} or None.

    A sentence qualifies only if it contains enough of the query's weight
    (rare words count more). Phrase matches, definition-style opening
    sentences and higher-ranked articles score better.
    """
    terms = set(tokenize(query))
    if not terms:
        return None
    total = sum(index.idf(t) for t in terms)  # unknown words keep this high, so no answer
    phrase = " ".join(tokenize(query))
    best, best_score = None, 0.0
    for rank, (doc_id, _) in enumerate(index.search(query, k=top_docs)):
        for i, sentence in enumerate(sentences(index.docs[doc_id]["text"])):
            tokens = tokenize(sentence)
            coverage = sum(index.idf(t) for t in terms & set(tokens)) / total
            if coverage < min_coverage:
                continue
            score = coverage - 0.05 * rank - len(sentence) / 5000
            score += 0.15 if i == 0 else 0
            score += 0.25 if len(terms) > 1 and phrase in " ".join(tokens) else 0
            if score > best_score:
                best, best_score = {"sentence": sentence, "doc_id": doc_id, "title": index.docs[doc_id]["title"]}, score
    return best
