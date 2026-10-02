# minisearch

A search engine built from scratch in Python: tokenizer, inverted index, and
BM25 ranking, with no search libraries. Standard library only.

![CI](https://github.com/Charanya3408/minisearch/actions/workflows/ci.yml/badge.svg)

## How it works

1. **Tokenize**: lowercase, split on non-alphanumerics, drop stopwords, apply a small suffix stemmer.
2. **Index**: for every term, store which documents contain it and how often (the inverted index).
3. **Rank**: score each candidate document with BM25 (term frequency, inverse document frequency, length normalisation).
4. **Top-k**: keep the best results with a heap instead of sorting every match.

## Try it

    python3 -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    python -m minisearch "search engine ranking"
    python -m minisearch --dir path/to/your/notes "your query"

## Tests

    python -m pytest -v

## Limitations

- The stemmer is naive (not Porter); it will mis-stem some words.
- No phrase queries, no typo tolerance, no stored positions yet.
- The index lives in memory and is saved as JSON.

## Web UI

    python -m minisearch.crawl     # downloads ~110 Wikipedia article intros and thumbnails
    python -m minisearch.web       # opens at http://127.0.0.1:8000

Pages: search home, ranked results with highlighted snippets, article view with related
articles, and a "How it works" page with live index statistics. The server uses only the
standard library. Article text and images come from Wikipedia (CC BY-SA).

## Data
Article text in data/articles.json comes from Wikipedia (CC BY-SA 4.0).
