from minisearch.live import live_search, search_url
from minisearch.web import Site

PAYLOAD = {"query": {"pages": {
    "9": {"pageid": 9, "title": "Quokka", "index": 1,
          "extract": "The quokka is a small marsupial about the size of a domestic cat. It lives on islands off Western Australia.",
          "thumbnail": {"source": "https://upload.wikimedia.org/q.jpg"}},
    "8": {"pageid": 8, "title": "Marsupial", "index": 2,
          "extract": "Marsupials are mammals that carry their young in a pouch. Most live in Australia and nearby islands."},
}}}


def test_live_search_orders_by_rank_and_strips_question_words():
    urls = []

    def fake(url):
        urls.append(url)
        return PAYLOAD

    docs = live_search("what is a quokka", fetch=fake)
    assert [d["title"] for d in docs] == ["Quokka", "Marsupial"]
    assert "gsrsearch=quokka" in urls[0]
    assert "generator=search" in search_url("x")


def test_live_search_returns_empty_when_offline():
    def broken(url):
        raise OSError("offline")

    assert live_search("anything", fetch=broken) == []


def test_results_fall_back_to_live_wikipedia():
    site = Site.load("missing.json", live=True)
    site.fetch = lambda url: PAYLOAD
    page = site.results("what is a quokka")
    assert "looked up live" in page
    assert "small marsupial" in page
    assert "https://en.wikipedia.org/wiki/Quokka" in page
    assert "More from Wikipedia" in page


def test_local_answer_does_not_trigger_live_lookup():
    site = Site.load("missing.json", live=True)

    def boom(url):
        raise AssertionError("should not call Wikipedia")

    site.fetch = boom
    page = site.results("inverted index search engines scanning documents")
    assert "From your index" in page


def test_offline_shows_friendly_empty_page():
    site = Site.load("missing.json", live=True)

    def broken(url):
        raise OSError("offline")

    site.fetch = broken
    assert "No results" in site.results("zzzzqqqq")
