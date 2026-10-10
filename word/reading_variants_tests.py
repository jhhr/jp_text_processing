"""Cases for `reading_agreement`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/word/reading_variants_tests.py

A case is one kanji of a word, the reading the word gives it, whether it begins the word, and
the reading a text has on the same kanji; its id says which rule of the module it is about.
The cases that have to come out as "none" matter as much as the others: each is a pair that
looks like a sound change and is two words.
"""

import pytest

from .reading_variants import WordKanjiReading, reading_agreement

CASES = [
    pytest.param("腰", "こし", True, "こし", "same", id="the same kana"),
    pytest.param("腰", "こし", True, "ごし", "sound_change", id="rendaku in the text"),
    pytest.param("学", "がく", True, "がっ", "sound_change", id="a small っ in the text"),
    pytest.param("人", "じん", True, "ひと", "none", id="another reading of the kanji"),
    pytest.param("付", "ず", False, "づ", "same", id="ず written づ"),
    pytest.param("付", "づ", False, "ず", "same", id="づ written ず"),
    pytest.param("地", "じ", True, "ぢ", "same", id="じ written ぢ"),
    # Rendaku the other way round
    pytest.param("殺", "ごろ", False, "ころ", "rendaku_undone", id="the word's rendaku undone"),
    pytest.param("深", "ぶか", False, "ふか", "rendaku_undone", id="the word's rendaku undone /2"),
    pytest.param("繰", "ぐ", False, "く", "rendaku_undone", id="rendaku undone in one kana"),
    pytest.param("顔", "がお", True, "かお", "none", id="a word that begins voiced"),
    pytest.param("口", "ぐち", True, "くち", "none", id="a word that begins voiced /2"),
    pytest.param("降", "ごう", True, "こう", "none", id="a word that begins voiced, onyomi"),
    pytest.param("見", "げん", False, "けん", "none", id="a voiced reading the kanji lists"),
    pytest.param("示", "じ", False, "し", "none", id="a voiced reading the kanji lists /2"),
    pytest.param("伏", "ぶく", False, "ふく", "none", id="a voiced reading the kanji lists /3"),
    # The ち of an onyomi against じ is not in the rendaku table, and 中 lists ジュウ besides
    pytest.param("中", "じゅう", False, "ちゅう", "none", id="じゅう is not ちゅう voiced"),
    pytest.param("中", "ちゅう", False, "じゅう", "none", id="ちゅう is not voiced to じゅう"),
    pytest.param("端", "はし", True, "はじ", "none", id="voicing after the first kana"),
    # A stem said two ways
    pytest.param("良", "よ", True, "い", "other_stem", id="よい said いい"),
    pytest.param("良", "い", True, "よ", "other_stem", id="いい said よい"),
    pytest.param("行", "い", False, "ゆ", "other_stem", id="いく said ゆく"),
    pytest.param("言", "い", True, "ゆ", "other_stem", id="いう said ゆう"),
    pytest.param("得", "え", True, "う", "other_stem", id="える said うる"),
    pytest.param("歪", "いが", True, "ゆが", "other_stem", id="いがむ said ゆがむ"),
    pytest.param("甘", "あま", True, "うま", "none", id="あまい and うまい are two words"),
    pytest.param("居", "い", True, "お", "none", id="いる and おる are two verbs"),
    pytest.param("出", "で", True, "だ", "none", id="でる and だす are two verbs"),
    pytest.param("入", "い", True, "ゆ", "none", id="a pair the kanji does not list"),
    pytest.param("捌", "は", True, "さば", "none", id="stems that only share an okurigana"),
    # Degenerate: nothing to compare is no agreement, and the point is not raising
    pytest.param("人", "", True, "ひと", "none", id="no reading in the word"),
    pytest.param("人", "ひと", True, "", "none", id="no reading in the text"),
    pytest.param("々", "びと", False, "ひと", "rendaku_undone", id="a kanji not in the data"),
]


@pytest.mark.parametrize("kanji, word_reading, begins_word, text_reading, expected", CASES)
def test_reading_agreement(
    kanji: str, word_reading: str, begins_word: bool, text_reading: str, expected: str
):
    word_kanji = WordKanjiReading(kanji=kanji, reading=word_reading, begins_word=begins_word)
    assert reading_agreement(word_kanji, text_reading) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
