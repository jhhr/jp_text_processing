"""Cases for `reading_agreement` and `last_kanji_agreement`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/word/reading_variants_tests.py

A case is one kanji of a word, the reading the word gives it, whether it begins the word, and
the reading a text has on the same kanji; its id says which rule of the module it is about.
The cases that have to come out as "none" matter as much as the others: each is a pair that
looks like a sound change and is two words.

The cases for the word's last kanji also give the okurigana the word has after it and the kana
the text has after it.
"""

import pytest

from .reading_variants import WordKanjiReading, last_kanji_agreement, reading_agreement

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


LAST_KANJI_CASES = [
    pytest.param("食", "た", "べる", "た", "べた", "same", id="the same kana"),
    pytest.param("付", "つ", "ける", "づ", "けた", "sound_change", id="rendaku in the text"),
    pytest.param("良", "い", "い", "よ", "かった", "other_stem", id="いい said よかった"),
    # The two irregular verbs
    pytest.param("為", "す", "る", "し", "た", "inflected_stem", id="する as した"),
    pytest.param("為", "す", "る", "さ", "せる", "inflected_stem", id="する as させる"),
    pytest.param("為", "す", "る", "せ", "ず", "inflected_stem", id="する as せず"),
    pytest.param("来", "く", "る", "き", "ます", "inflected_stem", id="くる as きます"),
    pytest.param("来", "く", "る", "こ", "ない", "inflected_stem", id="くる as こない"),
    pytest.param("為", "な", "す", "し", "た", "none", id="なす is not した"),
    pytest.param("摩", "す", "る", "さ", "すった", "none", id="another する is not irregular"),
    pytest.param("繰", "く", "る", "き", "", "none", id="another くる is not irregular"),
    # The okurigana, or the start of it, inside the text's bracket
    pytest.param("溜", "た", "まる", "たま", "っている", "okurigana_moved", id="たま|っている"),
    pytest.param("行", "や", "り", "やり", "です", "okurigana_moved", id="はやり in one bracket"),
    pytest.param("向", "む", "こう", "むこ", "うに", "okurigana_moved", id="むこ|う"),
    pytest.param("引", "ひ", "く", "びき", "で", "okurigana_moved", id="the noun form, voiced"),
    pytest.param("切", "き", "る", "きっ", "", "okurigana_moved", id="the noun form, with っ"),
    pytest.param("突", "つ", "く", "つつ", "いている", "none", id="つつく is not つく"),
    pytest.param("疎", "おろ", "か", "おろそ", "か", "none", id="おろそか is not おろか"),
    pytest.param("何", "か", "なる", "かん", "に", "none", id="いかん is not いかなる"),
    # The end of the word's reading written after the kanji in the text
    pytest.param("錆", "さび", "る", "さ", "びてしまった", "okurigana_moved", id="さ|びて"),
    pytest.param("籠", "ごも", "る", "ご", "もった", "okurigana_moved", id="ご|もった"),
    pytest.param("装", "よそお", "う", "よそ", "います", "none", id="よそう is not よそおう"),
    pytest.param("合", "あわせ", "る", "あ", "った", "none", id="あう is not あわせる"),
    # Readings that are simply another word's
    pytest.param("出", "で", "る", "だ", "した", "none", id="だす is not でる"),
    pytest.param("潜", "もぐ", "る", "くぐ", "って", "none", id="くぐる is not もぐる"),
    pytest.param("行", "い", "く", "おこな", "った", "none", id="おこなう is not いく"),
    pytest.param("居", "い", "る", "お", "ります", "none", id="おる is not いる"),
    pytest.param("紡", "つむ", "ぎ", "ぼう", "", "none", id="an onyomi is not the kunyomi"),
]


@pytest.mark.parametrize(
    "kanji, word_reading, word_okurigana, text_reading, text_kana, expected", LAST_KANJI_CASES
)
def test_last_kanji_agreement(
    kanji: str,
    word_reading: str,
    word_okurigana: str,
    text_reading: str,
    text_kana: str,
    expected: str,
):
    word_kanji = WordKanjiReading(kanji=kanji, reading=word_reading, begins_word=True)
    assert last_kanji_agreement(word_kanji, word_okurigana, text_reading, text_kana) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
