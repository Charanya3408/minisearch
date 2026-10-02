import pytest

from minisearch import InvertedIndex


def make_index():
    index = InvertedIndex()
    index.add_document("a", "python python python tutorial")
    index.add_document("b", "python and cooking recipes for dinner tonight")
    index.add_document("c", "cooking cooking dinner")
    return index


def test_finds_matching_documents_only():
    results = make_index().search("python")
    assert {doc_id for doc_id, _ in results} == {"a", "b"}


def test_more_occurrences_rank_higher():
    ids = [doc_id for doc_id, _ in make_index().search("python")]
    assert ids[0] == "a"


def test_unknown_term_returns_nothing():
    assert make_index().search("zebra") == []


def test_query_of_only_stopwords_returns_nothing():
    assert make_index().search("the and of") == []


def test_rare_terms_outweigh_common_terms():
    index = InvertedIndex()
    index.add_document("1", "python guide")
    index.add_document("2", "python guide")
    index.add_document("3", "python guide quokka")
    assert index.idf("quokka") > index.idf("python")
    assert index.search("python quokka")[0][0] == "3"


def test_shorter_document_wins_on_equal_term_frequency():
    index = InvertedIndex()
    index.add_document("short", "search engines")
    index.add_document("long", "search " + "filler " * 40)
    assert index.search("search")[0][0] == "short"


def test_term_frequency_saturates():
    index = InvertedIndex()
    index.add_document("one", "bm25 " + "x " * 9)
    index.add_document("ten", "bm25 " * 10)
    index.add_document("twenty", "bm25 " * 20)
    index.add_document("other", "unrelated words here " * 3)
    scores = dict(index.search("bm25"))
    # doubling the count from 10 to 20 adds less than going from 1 to 10
    assert scores["twenty"] - scores["ten"] < scores["ten"] - scores["one"]


def test_top_k_limits_results():
    index = InvertedIndex()
    for i in range(20):
        index.add_document(str(i), "common word")
    assert len(index.search("common", k=5)) == 5


def test_ties_break_by_doc_id():
    index = InvertedIndex()
    index.add_document("b", "same text")
    index.add_document("a", "same text")
    assert [d for d, _ in index.search("same")] == ["a", "b"]


def test_duplicate_id_rejected():
    index = InvertedIndex()
    index.add_document("a", "text")
    with pytest.raises(ValueError):
        index.add_document("a", "other")


def test_save_and_load_roundtrip(tmp_path):
    index = make_index()
    path = tmp_path / "index.json"
    index.save(str(path))
    loaded = InvertedIndex.load(str(path))
    assert loaded.search("python cooking") == index.search("python cooking")
    assert len(loaded) == len(index)
