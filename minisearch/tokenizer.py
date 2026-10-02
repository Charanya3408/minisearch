"""Turn raw text into index terms: lowercase, split, drop stopwords, stem."""
import re

STOPWORDS = frozenset(
    "a an and are as at be but by for if in into is it no not of on or such "
    "that the their then there these they this to was will with".split()
)
_TOKEN = re.compile(r"[a-z0-9]+")


def stem(word: str) -> str:
    """A deliberately small suffix stripper (not the Porter algorithm).

    It makes plurals and -ing / -ed forms match, and nothing more. Known
    weaknesses: it does not repair doubled consonants ("running" -> "runn")
    and it leaves "indexes" as "indexe".
    """
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 6 and word.endswith("ing"):
        return word[:-3]
    if len(word) > 4 and word.endswith("ed"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def tokenize(text: str) -> list[str]:
    return [stem(t) for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS]
