from minisearch.tokenizer import stem, tokenize


def test_lowercases_and_splits_on_punctuation():
    assert tokenize("Hello, World! 2026") == ["hello", "world", "2026"]


def test_drops_stopwords():
    assert tokenize("the cat is on the mat") == ["cat", "mat"]


def test_plural_and_verb_forms_match():
    assert stem("lists") == "list"
    assert stem("studies") == "study"
    assert stem("searching") == "search"
    assert stem("jumped") == "jump"


def test_short_and_special_words_are_left_alone():
    assert stem("bus") == "bus"
    assert stem("class") == "class"
    assert stem("string") == "string"


def test_empty_text():
    assert tokenize("") == []
    assert tokenize("   ...  ") == []
