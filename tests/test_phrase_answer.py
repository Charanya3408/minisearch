from minisearch import InvertedIndex
from minisearch.answer import best_answer, sentences


def phrase_corpus():
    index = InvertedIndex()
    index.add_document("apart", "black black black filler hole hole hole", "Apart")
    index.add_document("phrase", "a black hole is a dense object", "Phrase")
    index.add_document("filler", "cooking dinner recipes tonight", "Filler")
    return index


def test_phrase_beats_scattered_words():
    index = phrase_corpus()
    assert index.search("black hole", phrase=True)[0][0] == "phrase"
    assert index.phrase_count("phrase", ["black", "hole"]) == 1
    assert index.phrase_count("apart", ["black", "hole"]) == 0
    assert index.search("black hole", phrase=False)[0][0] == "apart"  # without the bonus, repeats win


def test_phrase_order_matters():
    index = phrase_corpus()
    assert index.phrase_count("phrase", ["hole", "black"]) == 0


def test_phrase_survives_save_and_load(tmp_path):
    index = phrase_corpus()
    path = tmp_path / "i.json"
    index.save(str(path))
    assert InvertedIndex.load(str(path)).search("black hole")[0][0] == "phrase"


def answer_index():
    index = InvertedIndex()
    index.add_document("bh", "A black hole is a region of space where gravity is extreme. Light cannot escape it.", "Black hole")
    index.add_document("jup", "Jupiter is the largest planet in the solar system. It has a Great Red Spot.", "Jupiter")
    index.add_document("tea", "Tea is a drink made from leaves. It is popular in India.", "Tea")
    return index


def test_answer_for_a_question():
    ans = best_answer(answer_index(), "what is a black hole")
    assert ans["doc_id"] == "bh"
    assert ans["sentence"].startswith("A black hole is")


def test_no_answer_when_corpus_does_not_cover_it():
    assert best_answer(answer_index(), "blockchain consensus") is None
    assert best_answer(answer_index(), "black hole zzzzqq") is None
    assert best_answer(answer_index(), "what is the") is None


def test_sentence_splitter_ignores_tiny_fragments():
    assert sentences("Short. This one is long enough to keep. Ok.") == ["This one is long enough to keep."]
