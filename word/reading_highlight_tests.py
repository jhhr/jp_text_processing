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


# Two spellings of one reading, or None where they cannot be the same word. The seven values
# are `SpellingEvidence`'s fields in order: shared_kanji, shared_kana, word_kanji_as_kana,
# text_kanji_as_kana, other_kana_type, starts_in_kana_for_kanji, ends_in_kana_for_kanji.
SPELLING_CASES = [
    pytest.param(
        "見付[みつ]か",
        "見[み]つか",
        SpellingEvidence(1, 1, False, False, False, False, False),
        id="one of two kanji in kana on the other side",
    ),
    pytest.param(
        "基付[もとづ]",
        "基[もと]づ",
        SpellingEvidence(1, 0, False, False, False, False, True),
        id="the second of two kanji in kana on the other side, at the end",
    ),
    pytest.param(
        "微風[そよかぜ]",
        "そよ 風[かぜ]",
        SpellingEvidence(1, 0, False, False, False, True, False),
        id="the first of two kanji in kana on the other side",
    ),
    pytest.param(
        "有様[ありさま]",
        "有[あ]り 様[さま]",
        SpellingEvidence(2, 0, False, False, False, False, False),
        id="okurigana inside the bracket on one side",
    ),
    pytest.param(
        "並[なみ]",
        "並[な]み",
        SpellingEvidence(1, 0, False, False, False, False, False),
        id="okurigana inside the bracket on one side, at the end: kana for no kanji",
    ),
    pytest.param(
        "住[すま]居[い]",
        "住[す]まい",
        SpellingEvidence(1, 0, True, False, False, False, True),
        id="a kanji's reading that the other side ends in kana, and a kanji in kana",
    ),
    pytest.param(
        "お 詫[わ]び",
        "御[お] 詫[わ]び",
        SpellingEvidence(1, 1, False, True, False, False, False),
        id="a kanji shared, another the word has in kana",
    ),
    pytest.param(
        "罰[ばつ]",
        "バツ",
        SpellingEvidence(0, 0, True, False, False, True, True),
        id="the word's kanji in kana, nothing shared",
    ),
    pytest.param(
        "若[も]しも",
        "もしも",
        SpellingEvidence(0, 2, True, False, False, True, False),
        id="the word's kanji in kana, its kana shared",
    ),
    pytest.param(
        "べき",
        "可[べ]き",
        SpellingEvidence(0, 1, False, True, False, False, False),
        id="the text's kanji in kana in the word",
    ),
    pytest.param(
        "ビール",
        "麦酒[ビール]",
        SpellingEvidence(0, 0, False, True, False, False, False),
        id="the whole word a reading in the text",
    ),
    pytest.param(
        "其[そ]のまま",
        "その 儘[まま]",
        SpellingEvidence(0, 1, True, True, False, True, False),
        id="each side has a kanji the other has in kana",
    ),
    pytest.param(
        "CD",
        "ＣＤ",
        SpellingEvidence(0, 2, False, False, False, False, False),
        id="written alike but for the width",
    ),
    pytest.param(
        "チーズ",
        "ちーず",
        SpellingEvidence(0, 1, False, False, True, False, False),
        id="the same kana in the other type are compatible and not shared",
    ),
    pytest.param(
        "豚[とん]カツ",
        "とんかつ",
        SpellingEvidence(0, 0, True, False, True, True, False),
        id="a kanji in kana and the word's kana in the other type",
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
        SpellingEvidence(2, 0, False, False, False, False, False),
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
    # The word may not be in the text at all, and then something else that reads like it
    # often is. These are places the rules were tightened against, each found by giving the
    # sentence of one note the word of another.
    pytest.param(
        "ちーずを 一切[ひとき]れ 下[くだ]さい。",
        "チーズ",
        "ちーずを 一切[ひとき]れ 下[くだ]さい。",
        id="not there: a kana word in the other kana is the as-written search's to find",
    ),
    pytest.param(
        "貫禄[かんろく]も 出[で]ちまって",
        "チ",
        "貫禄[かんろく]も 出[で]ちまって",
        id="not there: one katakana is not every hiragana that reads the same",
    ),
    pytest.param(
        "話[はなし]を<k> 捏[こ]ね 上[あ]げた</k>。",
        "値上[ねあ]げ",
        "話[はなし]を<k> 捏[こ]ね 上[あ]げた</k>。",
        id="not there: okurigana of the word before for the word's first kanji",
    ),
    pytest.param(
        "ボイラー 室[しつ]から 女[おんな]の 声[こえ]が<k> 為[し]た</k>。",
        "空[から]",
        "ボイラー 室[しつ]から 女[おんな]の 声[こえ]が<k> 為[し]た</k>。",
        id="not there: a particle of two kana",
    ),
    pytest.param(
        "阿呆[アホ] 見[み]たいな 面[ツラ]",
        "胎[たい]",
        "阿呆[アホ] 見[み]たいな 面[ツラ]",
        id="not there: an auxiliary of two kana",
    ),
    pytest.param(
        "お 使[つか]い 頂[いただ]けます。",
        "増[ま]す",
        "お 使[つか]い 頂[いただ]けます。",
        id="not there: an auxiliary that has the verb's kana for headword",
    ),
    pytest.param(
        "黄色[きいろ]と 緑[みどり]が 交[ま]じった 梨[なし]",
        "まじ",
        "黄色[きいろ]と 緑[みどり]が 交[ま]じった 梨[なし]",
        id="not there: two kana of a kana word in the stem of a verb in kanji",
    ),
    pytest.param(
        "友達[ともだち]を 出迎[でむか]えに 行[い]きました。",
        "イキる",
        "友達[ともだち]を 出迎[でむか]えに 行[い]きました。",
        id="not there: a kana verb's two-kana stem in another verb in kanji",
    ),
    pytest.param(
        "勉強[べんきょう]<k> 為[し]ていません</k>ね。",
        "照[て]る",
        "勉強[べんきょう]<k> 為[し]ていません</k>ね。",
        id="not there: a particle that is the kana of a verb's stem",
    ),
    pytest.param(
        "準備[じゅんび]に 愚図[ぐず]ついて、 結局[けっきょく] 遅[おく]れた。",
        "作[つく]る",
        "準備[じゅんび]に 愚図[ぐず]ついて、 結局[けっきょく] 遅[おく]れた。",
        id="not there: another verb whose headword is the kana of a verb's stem",
    ),
    # Kana the text has for the word's last kanji say nothing by themselves, and what comes
    # after them can make them another word's.
    pytest.param(
        "やっと 出[で]てくれた。",
        "出[で]て 来[く]る",
        "やっと 出[で]てくれた。",
        id="not there: another verb that begins as the word's last one does",
    ),
    pytest.param(
        "誰[だれ]も 見[み]ていなかった。",
        "見[み]て 行[い]く",
        "誰[だれ]も 見[み]ていなかった。",
        id="not there: another verb that begins as the word's last one does /2",
    ),
    pytest.param(
        "一口[ひとくち] 食[た]べてみせた。",
        "食[た]べて 見[み]る",
        "一口[ひとくち] 食[た]べてみせた。",
        id="not there: another verb that begins as the word's last one does /3",
    ),
    pytest.param(
        "手[て]まで 汚[よご]れた。",
        "手間[てま]",
        "手[て]まで 汚[よご]れた。",
        id="not there: a particle that begins as the word's last kanji reads",
    ),
    pytest.param(
        "手[て]まが 掛[か]かる。",
        "手間[てま]",
        "<b>手[て]ま</b>が 掛[か]かる。",
        id="the kana for the word's last kanji end where a token of MeCab's does",
    ),
    # The price of the stem guess not being asked: a verb MeCab does not know is not found
    # by its kana.
    pytest.param(
        "「<k> 否[いや]</k>テンパってた<k> 丈[だけ]</k>で…」",
        "聴牌[テンパ]る",
        "「<k> 否[いや]</k>テンパってた<k> 丈[だけ]</k>で…」",
        id="a verb MeCab does not know is not found in kana",
    ),
    # The headword of a token the text writes in kanji is not asked: the text gives that kanji
    # a reading of its own, here another verb's, and MeCab's headword for 行った is 行く or 行う
    # by what stands around it.
    pytest.param(
        "式[しき]を 行[おこな]った。",
        "行[い]く",
        "式[しき]を 行[おこな]った。",
        id="a headword is not asked where the text writes the token in kanji",
    ),
    pytest.param(
        "店[みせ]に 行[おこな]った。",
        "行[い]く",
        "店[みせ]に 行[おこな]った。",
        id="a headword is not asked where the text writes the token in kanji /2",
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
