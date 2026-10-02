import threading
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import urlopen

from minisearch.web import Site, make_server


def start():
    server = make_server(Site.load("missing.json", live=False), 0)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def get(url):
    try:
        with urlopen(url) as r:
            return r.status, r.read().decode()
    except HTTPError as e:
        return e.code, e.read().decode()


def test_pages_render():
    server, base = start()
    try:
        assert "minisearch" in get(base + "/")[1]
        status, body = get(base + "/search?q=" + quote("inverted index"))
        assert status == 200 and "Inverted index" in body and "<mark>" in body
        assert get(base + "/doc/bm25")[0] == 200
        assert get(base + "/how-it-works")[0] == 200
        assert get(base + "/random")[0] == 200
        assert get(base + "/static/style.css")[0] == 200
    finally:
        server.shutdown()


def test_unknown_pages_404_and_no_results():
    server, base = start()
    try:
        assert get(base + "/nope")[0] == 404
        assert get(base + "/doc/missing")[0] == 404
        assert "No results" in get(base + "/search?q=zzzzqqqq")[1]
    finally:
        server.shutdown()


def test_query_is_escaped():
    server, base = start()
    try:
        body = get(base + "/search?q=" + quote("<script>alert(1)</script>"))[1]
        assert "<script>alert(1)" not in body
    finally:
        server.shutdown()
