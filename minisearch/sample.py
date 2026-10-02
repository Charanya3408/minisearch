"""A tiny built-in corpus so the engine can be tried without any setup."""

SAMPLE_DOCS = [
    ("python-lists", "Python lists",
     "Python lists are ordered, mutable collections. You can append items, slice lists, and sort them in place."),
    ("python-dicts", "Python dictionaries",
     "A Python dictionary maps keys to values using a hash table. Lookups, inserts and deletes take constant time on average."),
    ("inverted-index", "Inverted index",
     "An inverted index maps each term to the documents that contain it. Search engines use inverted indexes to answer queries without scanning every document."),
    ("bm25", "BM25 ranking",
     "BM25 is a ranking function that scores documents by term frequency and inverse document frequency. It also normalises for document length so long documents do not win unfairly."),
    ("binary-search", "Binary search",
     "Binary search finds an item in a sorted array by repeatedly halving the search range. It runs in logarithmic time."),
    ("hash-tables", "Hash tables",
     "Hash tables store keys in buckets chosen by a hash function. Collisions are handled by chaining or open addressing."),
    ("sourdough", "Sourdough bread",
     "Sourdough bread rises using a fermented starter instead of commercial yeast. The long fermentation gives it a tangy flavour."),
    ("monsoon", "The monsoon",
     "The monsoon brings heavy rain to the Indian subcontinent between June and September. Farmers plan their sowing around it."),
    ("jupiter", "Jupiter",
     "Jupiter is the largest planet in the solar system. Its Great Red Spot is a storm larger than Earth."),
    ("heaps", "Heaps",
     "A heap is a tree based structure that returns the smallest or largest item quickly. Search engines use a heap to keep the top results while scanning scores."),
]
