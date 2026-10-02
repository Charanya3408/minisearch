import argparse
from pathlib import Path

from .index import InvertedIndex
from .sample import SAMPLE_DOCS


def build_index(folder: str | None) -> InvertedIndex:
    index = InvertedIndex()
    if folder:
        root = Path(folder)
        for path in sorted(root.rglob("*.txt")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            index.add_document(str(path.relative_to(root)), text, title=path.stem)
    else:
        for doc_id, title, text in SAMPLE_DOCS:
            index.add_document(doc_id, text, title)
    return index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="minisearch", description="Search a set of documents.")
    parser.add_argument("query", nargs="+", help="search words")
    parser.add_argument("--dir", help="folder of .txt files to index (default: built-in sample)")
    parser.add_argument("-k", type=int, default=5, help="number of results")
    args = parser.parse_args(argv)

    index = build_index(args.dir)
    results = index.search(" ".join(args.query), k=args.k)
    print(f"Indexed {len(index)} documents.")
    if not results:
        print("No results.")
        return 0
    for rank, (doc_id, score) in enumerate(results, 1):
        doc = index.docs[doc_id]
        preview = " ".join(doc["text"].split())[:100]
        print(f"{rank}. {doc['title']}  (score {score:.3f})")
        print(f"   {preview}")
    return 0
