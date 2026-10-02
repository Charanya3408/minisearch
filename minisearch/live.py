"""Look things up on Wikipedia when the local index cannot cover a query."""
import re
from urllib.parse import urlencode

from .crawl import API, fetch_json, parse_pages

_LEADING_QUESTION = re.compile(r"^(what|who|when|where|why|how)\s+(is|are|was|were|does|do|did|can)?\s*(a|an|the)?\s*", re.I)


def search_url(query: str, limit: int = 10) -> str:
    params = {
        "action": "query", "format": "json", "generator": "search", "gsrsearch": query,
        "gsrlimit": limit, "gsrnamespace": 0, "prop": "extracts|pageimages",
        "exintro": 1, "explaintext": 1, "exlimit": "max", "piprop": "thumbnail", "pithumbsize": 480,
    }
    return API + "?" + urlencode(params)


def live_search(query: str, limit: int = 10, fetch=lambda url: fetch_json(url, 8)) -> list[dict]:
    """Return Wikipedia's top articles for the query, best first. Returns [] if offline."""
    cleaned = _LEADING_QUESTION.sub("", query).strip() or query
    try:
        payload = fetch(search_url(cleaned, limit))
    except Exception:
        return []
    pages = payload.get("query", {}).get("pages", {})
    rank = {str(p["pageid"]): p.get("index", 999) for p in pages.values()}
    return sorted(parse_pages(payload), key=lambda d: rank.get(d["id"], 999))
