"""Cases for `reading_highlight`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/word/reading_highlight_tests.py

Pass `--log-cli-level=debug` to see what a case logged; pytest captures the package logger on
its own, so nothing here has to turn logging on.

Three lists, one per step of the module: how a text is read into atoms, what two spellings of
one reading have in common, and what `highlight_by_reading` makes of a text on its own. What
`word_highlight` does with the module behind the as-written search is in
`word_highlight_tests.py`, under "Reading -".
"""

import pytest

from .reading_highlight import (
    Atom,
    SpellingEvidence,
    compare_spellings,
    highlight_by_reading,
    read_atoms,
)

# What the text is cut into and how each piece reads: `[(written, reading), ...]`.
ATOM_CASES = [
    pytest.param(
        "見[み]つかる",
        [("見", "み"), ("つ", "つ"), ("か", "か"), ("る", "る")],
        id="a kanji with its reading, then kana",
    ),
    pytest.param(
        "お 金[かね]が",
        [("お", "お"), ("金", "かね"), ("が", "が")],
        id="the space before a furigana word is no piece of its own",
    ),
    pytest.param(
        "は し",
        [("は", "は"), ("し", "し")],
        id="a space between kana is not read",
    ),
    pytest.param(
        "聴牌[テンパ]ってた",
        [("聴牌", "てんぱ"), ("っ", "っ"), ("て", "て"), ("た", "た")],
        id="a katakana reading reads as hiragana",
    ),
    pytest.param(
        "Ｔシャツ",
        [("Ｔ", "t"), ("シ", "し"), ("ャ", "ゃ"), ("ツ", "つ")],
        id="width, case and kana type are folded in the reading, not in what is written",
    ),
    pytest.param(
        "2人[ふたり]",
        [("2人", "ふたり")],
        id="a digit is part of the kanji run its reading covers",
    ),
    pytest.param(
        "食べる",
        [("食", "食"), ("べ", "べ"), ("る", "る")],
        id="a kanji without a reading reads as itself",
    ),
    pytest.param(
        "バツ[sound:batsu.mp3]",
        [("バ", "ば"), ("ツ", "つ"), ("[sound:batsu.mp3]", "[sound:batsu.mp3]")],
        id="a bracket that follows no kanji is one piece that reads as nothing else does",
    ),
    # Degenerate: an empty bracket says nothing about its kanji, so the kanji is as good as
    # bare and the bracket is kept whole. The point is that it is not read as a reading.
    pytest.param(
        "罰[]が",
        [("罰", "罰"), ("[]", "[]"), ("が", "が")],
        id="an empty bracket is no reading",
    ),
]


@pytest.mark.parametrize("text, expected", ATOM_CASES)
def test_read_atoms(text: str, expected: list[tuple[str, str]]):
    assert [(atom.written, atom.reading) for atom in read_atoms(text)] == expected


def test_atoms_know_where_they_are_in_the_text():
    # The span is what gets wrapped in <b>, so it holds the space furigana syntax puts before
    # the kanji and the bracket after them.
    assert read_atoms("が 見[み]つ") == [
        Atom(written="が", reading="が", start=0, end=1),
        Atom(written="見", reading="み", start=1, end=6),
        Atom(written="つ", reading="つ", start=6, end=7),
    ]


# Two spellings of one reading: `(shared_kanji, shared_kana, word_kanji_as_kana,
# text_kanji_as_kana)`, or None where they cannot be the same word.
SPELLING_CASES = [
    pytest.param(
        "見付[みつ]か",
        "見[み]つか",
        SpellingEvidence(1, 1, False, False),
        id="one of two kanji in kana on the other side",
    ),
    pytest.param(
        "微風[そよかぜ]",
        "そよ 風[かぜ]",
        SpellingEvidence(1, 0, False, False),
        id="the first of two kanji in kana on the other side",
    ),
    pytest.param(
        "有様[ありさま]",
        "有[あ]り 様[さま]",
        SpellingEvidence(2, 0, False, False),
        id="okurigana inside the bracket on one side",
    ),
    pytest.param(
        "住[すま]居[い]",
        "住[す]まい",
        SpellingEvidence(1, 0, True, False),
        id="a kanji's reading that the other side ends in kana, and a kanji in kana",
    ),
    pytest.param(
        "お 詫[わ]び",
        "御[お] 詫[わ]び",
        SpellingEvidence(1, 1, False, True),
        id="a kanji shared, another the word has in kana",
    ),
    pytest.param(
        "罰[ばつ]",
        "バツ",
        SpellingEvidence(0, 0, True, False),
        id="the word's kanji in kana, nothing shared",
    ),
    pytest.param(
        "若[も]しも",
        "もしも",
        SpellingEvidence(0, 2, True, False),
        id="the word's kanji in kana, its kana shared",
    ),
    pytest.param(
        "べき",
        "可[べ]き",
        SpellingEvidence(0, 1, False, True),
        id="the text's kanji in kana in the word",
    ),
    pytest.param(
        "ビール",
        "麦酒[ビール]",
        SpellingEvidence(0, 0, False, True),
        id="the whole word a reading in the text",
    ),
    pytest.param(
        "其[そ]のまま",
        "その 儘[まま]",
        SpellingEvidence(0, 1, True, True),
        id="each side has a kanji the other has in kana",
    ),
    pytest.param(
        "CD",
        "ＣＤ",
        SpellingEvidence(0, 2, False, False),
        id="written alike but for the width",
    ),
    pytest.param(
        "紬[つむぎ]",
        "紡[つむ]ぎ",
        None,
        id="another kanji with the same reading",
    ),
    pytest.param(
        "見付[みつ]か",
        "見[み]着[つ]か",
        None,
        id="one kanji the same, the other another kanji",
    ),
    pytest.param(
        "見[み]る",
        "見[み]た",
        None,
        id="not the same reading",
    ),
    pytest.param(
        "御存[ごぞん]じ",
        "御[ご] 存知[ぞんじ]",
        SpellingEvidence(2, 0, False, False),
        id="brackets that end at different places are compared over both",
    ),
]


@pytest.mark.parametrize("word, text, expected", SPELLING_CASES)
def test_compare_spellings(word: str, text: str, expected: SpellingEvidence | None):
    assert compare_spellings(read_atoms(word), read_atoms(text)) == expected


# `highlight_by_reading` by itself. `word_highlight` only asks it where the word as written
# was found nowhere, so some of these texts never reach it in use; they are here to pin what
# the reading search does and does not take for the word.
HIGHLIGHT_CASES = [
    pytest.param(
        "鍵[かぎ]が 見[み]つからない",
        "見付[みつ]かる",
        "鍵[かぎ]が<b> 見[み]つからない</b>",
        id="a shared kanji, inflected",
    ),
    # The okurigana check is given the stem as the text spells it and then as the word does.
    # なかった after と言ったら is an auxiliary to MeCab, which the check does not take for an
    # ending of the word's own; 無かった is the adjective.
    pytest.param(
        "歩[ある]き<k> 難[にく]い 事[こと]</k>と 言[い]ったらなかった。",
        "と 言[い]ったら 無[な]い",
        "歩[ある]き<k> 難[にく]い 事[こと]</k><b>と 言[い]ったらなかった</b>。",
        id="a shared kanji, the inflection read in the word's spelling of the stem",
    ),
    # The stem is the word where the okurigana check finds no inflection after it, as it is
    # for a word found as written (大[おお]き of 大きすぎない).
    pytest.param(
        "彼[かれ]は 浅[あさ]ましすぎる。",
        "浅間[あさま]しい",
        "彼[かれ]は<b> 浅[あさ]まし</b>すぎる。",
        id="a shared kanji, the stem alone where what follows is not its inflection",
    ),
    pytest.param(
        "その 儘[まま]で",
        "其[そ]のまま",
        "その 儘[まま]で",
        id="each side has a kanji the other has in kana and none is shared: not taken",
    ),
    pytest.param(
        "この 家[いえ]は",
        "いえ",
        "この 家[いえ]は",
        id="a kana word is not a reading in a bracket",
    ),
    pytest.param(
        "はしをわたる",
        "はしる",
        "はしをわたる",
        id="a kana verb's stem written as the word writes it is the kana path's business",
    ),
    pytest.param(
        "<k> 棲[す]んでいます</k>か。",
        "住[す]む",
        "<k> 棲[す]んでいます</k>か。",
        id="the kana of a stem in another word's ending",
    ),
    pytest.param(
        "<span>バツ</span>が 三[みっ]つ",
        "<i>罰[ばつ]</i>",
        "<span><b>バツ</b></span>が 三[みっ]つ",
        id="tags in the word are not read, tags in the text stay",
    ),
    pytest.param(
        "ヘレン・ケラーは",
        "ヘレン・ケラー",
        "<b>ヘレン・ケラー</b>は",
        id="a splitter dot is not read on either side",
    ),
    pytest.param(
        "バツが[sound:batsu.mp3] 三[みっ]つ",
        "罰[ばつ]",
        "<b>バツ</b>が[sound:batsu.mp3] 三[みっ]つ",
        id="a sound tag is in nobody's way",
    ),
    pytest.param(
        "バツが[sound:batsu.mp3] 三[みっ]つ",
        "[sound:batsu.mp3]",
        "バツが[sound:batsu.mp3] 三[みっ]つ",
        id="a word that is a bracket and no text is not looked for",
    ),
    pytest.param(
        "",
        "罰[ばつ]",
        "",
        id="empty text",
    ),
    pytest.param(
        "バツが 三[みっ]つ",
        "",
        "バツが 三[みっ]つ",
        id="empty word",
    ),
]


@pytest.mark.parametrize("text, word, expected", HIGHLIGHT_CASES)
def test_highlight_by_reading(text: str, word: str, expected: str):
    assert highlight_by_reading(text, word) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
