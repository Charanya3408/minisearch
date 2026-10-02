from minisearch.crawl import crawl, parse_pages

PAYLOAD = {"query": {"pages": {
    "1": {"pageid": 1, "title": "Black hole", "extract": "A black hole is a region of spacetime where gravity is so strong that nothing escapes.",
          "thumbnail": {"source": "https://upload.wikimedia.org/x.jpg"}},
    "2": {"pageid": 2, "title": "Nothing here", "missing": ""},
    "3": {"pageid": 3, "title": "Stub", "extract": "Too short."},
}}}


def test_parse_keeps_good_pages_only():
    docs = parse_pages(PAYLOAD)
    assert len(docs) == 1
    assert docs[0]["title"] == "Black hole"
    assert docs[0]["thumb"].endswith("x.jpg")
    assert docs[0]["url"].endswith("/Black_hole")


def test_crawl_batches_and_dedupes():
    calls = []

    def fake_fetch(url):
        calls.append(url)
        return PAYLOAD

    docs = crawl(["A", "B"], fetch=fake_fetch, pause=0, size=1)
    assert len(calls) == 2
    assert len(docs) == 1
