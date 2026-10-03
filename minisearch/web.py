"""A small multi-page web UI, served with the standard library only."""
import html
import json
import os
import random
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from .answer import best_answer
from .crawl import fetch_json
from .index import InvertedIndex
from .live import live_search
from .sample import SAMPLE_DOCS
from .tokenizer import stem, tokenize

STATIC = Path(__file__).parent / "static"
PAL = [("#7c3aed", "#ec4899"), ("#0ea5e9", "#19d3a2"), ("#ff8a3d", "#ffd23f"),
       ("#ec4899", "#ff8a3d"), ("#19d3a2", "#38bdf8")]
CHIPS = ["black hole", "indian cuisine", "ancient egypt", "neural network",
         "monsoon", "photosynthesis", "chess", "search engine"]
_WORD = re.compile(r"[A-Za-z0-9]+")
esc = html.escape

HERO_SVG = (
    '<svg viewBox="0 0 260 220" aria-hidden="true"><circle cx="70" cy="50" r="22" fill="#ffd23f"/>'
    '<circle cx="215" cy="170" r="16" fill="#19d3a2"/><circle cx="210" cy="40" r="7" fill="#fff"/>'
    '<circle cx="36" cy="150" r="6" fill="#fff"/><circle cx="116" cy="108" r="58" fill="rgba(255,255,255,.25)" '
    'stroke="#fff" stroke-width="12"/><path d="M158 150l52 52" stroke="#fff" stroke-width="16" stroke-linecap="round"/>'
    '<path d="M92 100a30 30 0 0 1 28-26" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round"/></svg>'
)


def snippet(text: str, qterms: set, width: int = 190) -> str:
    text = " ".join(text.split())
    pos = next((m.start() for m in _WORD.finditer(text) if stem(m.group().lower()) in qterms), 0)
    start = max(0, pos - 50)
    if start:
        start = text.rfind(" ", 0, start) + 1
    chunk = text[start:start + width]
    return ("…" if start else "") + chunk + ("…" if start + width < len(text) else "")


def highlight(chunk: str, qterms: set) -> str:
    out, last = [], 0
    for m in _WORD.finditer(chunk):
        out.append(esc(chunk[last:m.start()]))
        word = m.group()
        out.append(f"<mark>{esc(word)}</mark>" if stem(word.lower()) in qterms else esc(word))
        last = m.end()
    out.append(esc(chunk[last:]))
    return "".join(out)


def layout(title: str, body: str) -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)}</title>"
        '<link rel="stylesheet" href="/static/style.css"></head><body>'
        '<nav><a class="logo" href="/">mini<b>search</b></a><div>'
        '<a href="/">Search</a><a href="/random">Random</a><a href="/how-it-works">How it works</a></div></nav>'
        f"{body}"
        "<footer>Articles and images from Wikipedia (CC BY-SA). "
        "Ranked by an inverted index and BM25 built from scratch.</footer></body></html>"
    )


def search_box(q: str = "") -> str:
    return (
        '<form class="sbox" action="/search" role="search">'
        f'<input name="q" value="{esc(q, quote=True)}" placeholder="Search articles…" aria-label="Search" autofocus>'
        "<button>Search</button></form>"
    )


class Site:
    def __init__(self, docs: list[dict], sample: bool = False, live: bool = True, fetch=None):
        self.index = InvertedIndex()
        self.meta = {}
        self.sample = sample
        self.live = live
        self.fetch = fetch or (lambda url: fetch_json(url, 8))
        self.cache: dict[str, list[dict]] = {}
        for d in docs:
            self.index.add_document(d["id"], d["text"], d["title"])
            self.meta[d["id"]] = d

    @classmethod
    def load(cls, path: str | None = None, live: bool = True) -> "Site":
        names = [path] if path else ["data/articles_large.json", "data/articles.json"]
        p = next((Path(n) for n in names if Path(n).exists()), None)
        if p is not None:
            return cls(json.loads(p.read_text(encoding="utf-8")), live=live)
        docs = [{"id": i, "title": t, "text": x, "thumb": "", "url": ""} for i, t, x in SAMPLE_DOCS]
        return cls(docs, sample=True, live=live)

    def visual(self, doc_id: str) -> str:
        return self.tile(self.meta[doc_id])

    def tile(self, d: dict) -> str:
        if d.get("thumb"):
            return f'<img src="{esc(d["thumb"], quote=True)}" alt="" loading="lazy" referrerpolicy="no-referrer">'
        c1, c2 = PAL[sum(map(ord, str(d["id"]))) % len(PAL)]
        return f'<div class="ph" style="background:linear-gradient(135deg,{c1},{c2})">{esc(d["title"][:1])}</div>'

    def chips(self) -> str:
        links = [f'<a href="/search?q={quote(c)}">{esc(c)}</a>' for c in CHIPS if self.index.search(c, 1)]
        return '<div class="chips"><span>Try</span>' + "".join(links) + "</div>"

    def card(self, doc_id: str) -> str:
        d = self.meta[doc_id]
        blurb = esc(" ".join(d["text"].split())[:90])
        return (f'<a class="card" href="/doc/{quote(doc_id)}">{self.visual(doc_id)}'
                f'<div class="tx"><h3>{esc(d["title"])}</h3><p>{blurb}…</p></div></a>')

    def home(self) -> str:
        ids = random.Random(7).sample(sorted(self.meta), min(8, len(self.meta)))
        cards = "".join(self.card(i) for i in ids)
        note = ""
        if self.sample:
            note = '<p class="note">Showing the 10 built-in sample documents. Run <code>python -m minisearch.crawl</code> for real articles.</p>'
        body = (
            '<main><section class="hero"><div><h1>Search anything.<br>Ranked by BM25.</h1>'
            f"<p>{len(self.index)} articles in the local index. Anything else is looked up on Wikipedia live.</p>{search_box()}</div>"
            f"{HERO_SVG}</section>{note}{self.chips()}<h2>Explore</h2><div class=\"grid\">{cards}</div></main>"
        )
        return layout("minisearch", body)

    def live_lookup(self, q: str) -> list[dict]:
        if q not in self.cache:
            self.cache[q] = live_search(q, fetch=self.fetch)
        return self.cache[q]

    def live_row(self, d: dict, qterms: set) -> str:
        snip = highlight(snippet(d["text"], qterms), qterms)
        return (f'<a class="res" href="{esc(d["url"], quote=True)}" target="_blank" rel="noopener">{self.tile(d)}'
                f'<div><span class="badge">Wikipedia</span><h3>{esc(d["title"])}</h3><p>{snip}</p></div></a>')

    def answer_box(self, ans, qterms: set) -> str:
        if not ans:
            return ""
        ext = ' target="_blank" rel="noopener"' if ans.get("external") else ""
        return ('<section class="answer"><span class="tag">Answer</span>'
                f'<p>{highlight(ans["sentence"], qterms)}</p>'
                f'<a href="{esc(ans["href"], quote=True)}"{ext}>{esc(ans["note"])}: {esc(ans["title"])}</a>'
                '<small>Picked from an article, not generated. It can be incomplete.</small></section>')

    def results(self, q: str) -> str:
        qterms = set(tokenize(q))
        t0 = time.perf_counter()
        hits = self.index.search(q, k=20)
        ms = (time.perf_counter() - t0) * 1000
        ans = best_answer(self.index, q)
        if ans:
            ans.update(href=f"/doc/{quote(ans['doc_id'])}", note="From your index")
        live = []
        if self.live and (ans is None or len(hits) < 5):
            live = self.live_lookup(q)
            if ans is None and live:
                temp = InvertedIndex()
                for d in live:
                    temp.add_document(d["id"], d["text"], d["title"])
                found = best_answer(temp, q)
                if found:
                    url = next(d["url"] for d in live if d["id"] == found["doc_id"])
                    ans = {**found, "href": url, "note": "From Wikipedia, looked up live", "external": True}
        rows = []
        for doc_id, score in hits:
            d = self.meta[doc_id]
            snip = highlight(snippet(d["text"], qterms), qterms)
            rows.append(
                f'<a class="res" href="/doc/{quote(doc_id)}">{self.visual(doc_id)}'
                f'<div><span class="score">{score:.2f}</span><h3>{esc(d["title"])}</h3><p>{snip}</p></div></a>')
        extra = [d for d in live if d["id"] not in self.meta]
        if hits or extra or ans:
            head = f'<p class="meta">{len(hits)} results in {ms:.2f} ms from your index'
            head += (f", plus {len(extra)} from Wikipedia" if extra else "") + "</p>"
            more = ""
            if extra:
                more = '<h2 class="sec">More from Wikipedia <small>looked up live</small></h2>'
                more += "".join(self.live_row(d, qterms) for d in extra)
            content = head + self.answer_box(ans, qterms) + "".join(rows) + more
        else:
            content = (f'<div class="empty"><h2>No results for “{esc(q)}”</h2>'
                       f'<p>Check the spelling or try a broader word. Live Wikipedia lookup needs an internet connection.</p>{self.chips()}</div>')
        return layout(f"{q} - minisearch", f'<main><div class="top">{search_box(q)}</div>{content}</main>')

    def article(self, doc_id: str):
        d = self.meta.get(doc_id)
        if d is None:
            return None
        paras = "".join(f"<p>{esc(p)}</p>" for p in d["text"].split("\n") if p.strip())
        related = [i for i, _ in self.index.search(d["text"][:300], k=5) if i != doc_id][:4]
        cards = "".join(self.card(i) for i in related)
        link = ""
        if d.get("url"):
            link = f'<a class="ext" href="{esc(d["url"], quote=True)}" target="_blank" rel="noopener">Read the full article on Wikipedia</a>'
        body = (
            f'<main><div class="top">{search_box()}</div><div class="ahero">{self.visual(doc_id)}</div>'
            f'<article class="art"><h1>{esc(d["title"])}</h1>{paras}{link}</article>'
            f'<h2>Related</h2><div class="grid">{cards}</div></main>'
        )
        return layout(f'{d["title"]} - minisearch', body)

    def about(self) -> str:
        idx = self.index
        postings = sum(len(p) for p in idx.postings.values())
        stats = (f'<div class="stats"><span><b>{len(idx)}</b> documents</span><span><b>{len(idx.postings)}</b> unique terms</span>'
                 f'<span><b>{postings}</b> postings</span><span><b>{idx.avg_doc_len:.0f}</b> avg terms per doc</span></div>')
        sample_text = "Searching the Indian monsoons quickly"
        toks = "".join(f"<code>{esc(t)}</code>" for t in tokenize(sample_text))
        steps = [
            ("#7c3aed", "#ec4899", "1. Tokenize", "Lowercase, split into words, drop filler words, trim endings so lists and list match."),
            ("#0ea5e9", "#19d3a2", "2. Index", "For every word, remember which documents contain it and how often. Like the index at the back of a book."),
            ("#ff8a3d", "#ec4899", "3. Rank", "BM25 scores each match: rarer words count more, repeats count less and less, long documents are not favoured. Exact phrases get a bonus."),
            ("#19d3a2", "#38bdf8", "4. Top results", "A heap keeps just the best few instead of sorting every match."),
        ]
        cards = "".join(
            f'<div class="step" style="background:linear-gradient(135deg,{a},{b})"><h3>{esc(t)}</h3><p>{esc(x)}</p></div>'
            for a, b, t, x in steps)
        body = (
            '<main><section class="hero"><div><h1>How it works</h1>'
            f"<p>No search library. Four ideas, all written from scratch.</p></div>{HERO_SVG}</section>"
            f'<div class="steps">{cards}</div><h2>This index</h2>{stats}'
            f'<h2>Tokenizer demo</h2><p class="demo">“{esc(sample_text)}” becomes {toks}</p></main>'
        )
        return layout("How it works - minisearch", body)

    def random_id(self) -> str:
        return random.choice(sorted(self.meta))


class Handler(BaseHTTPRequestHandler):
    site: Site = None

    def reply(self, status: int, body: bytes, ctype: str = "text/html; charset=utf-8", extra=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def page(self, status: int, text: str):
        self.reply(status, text.encode("utf-8"))

    def do_GET(self):
        url = urlparse(self.path)
        path, qs = url.path, parse_qs(url.query)
        site = self.site
        if path == "/":
            self.page(200, site.home())
        elif path == "/search":
            q = (qs.get("q") or [""])[0].strip()[:200]
            self.page(200, site.results(q) if q else site.home())
        elif path.startswith("/doc/"):
            text = site.article(unquote(path[5:]))
            if text is None:
                self.not_found()
            else:
                self.page(200, text)
        elif path == "/how-it-works":
            self.page(200, site.about())
        elif path == "/random":
            self.reply(302, b"", extra={"Location": "/doc/" + quote(site.random_id())})
        elif path == "/static/style.css":
            self.reply(200, (STATIC / "style.css").read_bytes(), "text/css; charset=utf-8")
        else:
            self.not_found()

    def not_found(self):
        body = '<main><div class="empty"><h2>Page not found</h2><p>That page does not exist.</p><a class="ext" href="/">Back to search</a></div></main>'
        self.page(404, layout("Not found - minisearch", body))

    def log_message(self, fmt, *args):
        pass


def make_server(site: Site, port: int = 8000, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    handler = type("SiteHandler", (Handler,), {"site": site})
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    site = Site.load()
    hosted = "PORT" in os.environ  # hosting services set PORT and need 0.0.0.0
    port = int(os.environ.get("PORT", 8000))
    server = make_server(site, port, "0.0.0.0" if hosted else "127.0.0.1")
    print(f"minisearch: {len(site.index)} documents. Open http://127.0.0.1:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
