"""Cases for `normalize_word`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/word/word_normalizer_tests.py

Pass `--log-cli-level=debug` to see what a case logged; pytest captures the package logger on
its own, so nothing here has to turn logging on.

A case's id says what shape the word arrives in. Most words arrive in ordinary furigana syntax
and have to come back as the very string they were given, so the cases that change nothing are
as much the point as the ones that do.
"""

import pytest

from .word_normalizer import normalize_word

CASES = [
    # --- ordinary words come back as they were given ---------------------------------------
    pytest.param("食[た]べる", "食[た]べる", id="ordinary - a verb with its okurigana"),
    pytest.param("日本語[にほんご]", "日本語[にほんご]", id="ordinary - one kanji run"),
    pytest.param("たれこみ", "たれこみ", id="ordinary - a kana word"),
    pytest.param("魚市場", "魚市場", id="ordinary - kanji with no furigana"),
    # The space that marks where a word's kanji start is furigana syntax, not noise
    pytest.param(" 上[あ]げる", " 上[あ]げる", id="ordinary - the space before the word stays"),
    pytest.param(
        "滅多[めった]  斬[き]り",
        "滅多[めった]  斬[き]り",
        id="ordinary - two spaces between the runs",
    ),
    # --- what is not the word is taken off it ----------------------------------------------
    pytest.param("ざくざく ", "ざくざく", id="noise - a space after a kana word"),
    pytest.param("素面[しらふ] ", "素面[しらふ]", id="noise - a space after the last bracket"),
    pytest.param("素面[しらふ]&nbsp;", "素面[しらふ]", id="noise - a non-breaking space entity"),
    pytest.param("素面[しらふ]\u00a0", "素面[しらふ]", id="noise - a non-breaking space"),
    pytest.param(" 幾[いく]つ[ ]か", " 幾[いく]つか", id="noise - a bracket holding only a space"),
    pytest.param("幾[いく]つ[]か", "幾[いく]つか", id="noise - an empty bracket"),
    pytest.param(
        "少[すこ]し<k> 宛[ずつ]</k>",
        "少[すこ]し 宛[ずつ]",
        id="noise - a tag around part of the word",
    ),
    pytest.param(
        '<span class="x">素面[しらふ]</span>',
        "素面[しらふ]",
        id="noise - a tag with attributes around the word",
    ),
    # Degenerate: a word of nothing but noise. The point is that the search is never handed an
    # empty word, so it comes back as it was given.
    pytest.param("<k></k>", "<k></k>", id="noise - nothing but a tag is left as it is"),
    pytest.param("[ ]", "[ ]", id="noise - nothing but an empty bracket is left as it is"),
    # --- one bracket after the whole expression --------------------------------------------
    # The bracket stands after kana, so it cannot be the reading of a kanji run. It spells the
    # expression instead: the kana as themselves, and what lies between them is the reading of
    # each kanji run.
    pytest.param(
        "言う迄も無く[いうまでもなく]",
        "言[い]う 迄[まで]も 無[な]く",
        id="whole bracket - kana between and after the kanji",
    ),
    pytest.param("神ゲー[かみげー]", "神[かみ]ゲー", id="whole bracket - a katakana word after"),
    pytest.param("ピリ付く[ぴりつく]", "ピリ 付[つ]く", id="whole bracket - katakana before"),
    pytest.param(
        "垂レ込ミ[たれこみ]", "垂[た]レ 込[こ]ミ", id="whole bracket - katakana okurigana"
    ),
    pytest.param("兄ィ[あにぃ]", "兄[あに]ィ", id="whole bracket - a small kana after the kanji"),
    pytest.param(
        "神ゲー[カミゲー]", "神[カミ]ゲー", id="whole bracket - a katakana reading stays katakana"
    ),
    pytest.param(
        "四の五の言う[しのごのいう]",
        "四[し]の 五[ご]の 言[い]う",
        id="whole bracket - the same kana twice in the word",
    ),
    # The reading has to be spelled to its end, so of the two い only the last is the okurigana
    pytest.param(
        "勿体無い[もったいない]",
        "勿体無[もったいな]い",
        id="whole bracket - the okurigana occurs inside the reading too",
    ),
    # 物[も]の 怪[のけ] spells it as well, and neither kanji lists such a reading
    pytest.param(
        "物の怪[もののけ]",
        "物[もの]の 怪[け]",
        id="whole bracket - two cuts, the kanji's readings choose",
    ),
    # With one way to spell it there is nothing to choose, whatever the kanji list
    pytest.param(
        "限リ限リ[ぎりぎり]",
        "限[ぎ]リ 限[ぎ]リ",
        id="whole bracket - one cut, a reading the kanji does not list",
    ),
    pytest.param(
        "鴨が葱を背負って来る[かもがねぎをしょってくる]",
        "鴨[かも]が 葱[ねぎ]を 背負[しょ]って 来[く]る",
        id="whole bracket - one cut, a jukujikun run in it",
    ),
    # With no kanji in the word the bracket has nothing to read and only repeats the kana
    pytest.param("ベタ[べた]", "ベタ", id="whole bracket - kana alone"),
    # --- a bracket that reads the kana before its kanji too --------------------------------
    pytest.param("スペイン 語[すぺいんご]", "スペイン 語[ご]", id="kana before - a katakana word"),
    pytest.param(
        "スペイン 語圏[すぺいんごけん]",
        "スペイン 語圏[ごけん]",
        id="kana before - a run of two kanji",
    ),
    pytest.param("に 対[にたい]して", "に 対[たい]して", id="kana before - a particle"),
    pytest.param("さん 付[さんづ]け", "さん 付[づ]け", id="kana before - a rendaku reading"),
    pytest.param("お 先[おさき]に", "お 先[さき]に", id="kana before - an honorific"),
    pytest.param(
        "スペイン 語[スペインゴ]", "スペイン 語[ゴ]", id="kana before - a katakana reading stays"
    ),
    # That a reading opens with the kana before the kanji proves nothing on its own; the traps
    # okuri/okurigana_mix_cleaning_replacer.py records for texts are there for words too.
    pytest.param(
        "か 家族[かぞく]", "か 家族[かぞく]", id="kana before - the kanji read the whole bracket"
    ),
    pytest.param("お 金[かね]", "お 金[かね]", id="kana before - the bracket leaves the kana out"),
    pytest.param(
        "お 土産[おみやげ]",
        "お 土産[おみやげ]",
        id="kana before - the kanji list neither reading, so the word is left alone",
    ),
    # --- a bracket that reads kanji before its own run too ---------------------------------
    pytest.param(
        "聞き 耳[ききみみ]を 立[た]てる",
        "聞[き]き 耳[みみ]を 立[た]てる",
        id="kanji before - one kanji and its okurigana",
    ),
    pytest.param(
        "口は 災[くちはわざわ]いの 元[もと]",
        "口[くち]は 災[わざわ]いの 元[もと]",
        id="kanji before - the bracket after it is an ordinary one",
    ),
    pytest.param(
        "目と鼻の 先[めとはなのさき]",
        "目[め]と 鼻[はな]の 先[さき]",
        id="kanji before - the last bracket reads the whole expression",
    ),
    pytest.param(
        "醜い家鴨の 子[みにくいあひるのこ]",
        "醜[みにく]い 家鴨[あひる]の 子[こ]",
        id="kanji before - a jukujikun run among them",
    ),
    # No kana stands between the two runs, so only the kanji's readings say where to cut
    pytest.param(
        "阪神・ 淡路大震災[はんしんあわじだいしんさい]",
        "阪神[はんしん]・ 淡路大震災[あわじだいしんさい]",
        id="kanji before - across a splitter dot, which stays",
    ),
    # A word may have furigana on some kanji only. A kanji without a reading is given one only
    # when a later bracket spells the kana between them, which is what shows it reads so far.
    pytest.param(
        "総[そう]勃ち", "総[そう]勃ち", id="kanji without a reading - no bracket after it"
    ),
    pytest.param(
        "彼の 物[もの]", "彼の 物[もの]", id="kanji without a reading - the bracket reads its own"
    ),
    # --- brackets cut at the wrong occurrence of a kana ------------------------------------
    # The brackets and the kana around them spell the reading in order, but the kanji read
    # nothing of it as it is cut. Cut at another occurrence of the kana, they read all of it.
    pytest.param(" 長[ながいあ]い 間[だ]", " 長[なが]い 間[あいだ]", id="wrong cut - two runs"),
    pytest.param(
        "甲の薬は 乙[こう]の 毒[くすりはおつのどく]",
        "甲[こう]の 薬[くすり]は 乙[おつ]の 毒[どく]",
        id="wrong cut - with kanji that were given no reading",
    ),
    pytest.param(
        "鵜の 目鷹[う]の 目[めたかのめ]",
        "鵜[う]の 目鷹[めたか]の 目[め]",
        id="wrong cut - a run of two kanji in it",
    ),
    pytest.param(
        " 思[おもい]い 至[た]る",
        " 思[おも]い 至[いた]る",
        id="wrong cut - the kana is in a bracket too",
    ),
    pytest.param(
        " 翻[ひ]る[がえる]",
        " 翻[ひるがえ]る",
        id="wrong cut - a second bracket after the okurigana goes on with the reading",
    ),
    pytest.param(
        "飲[の]み水[みず]",
        "飲[の]み水[みず]",
        id="wrong cut - another cut spells it too, but the kanji read the one written",
    ),
    pytest.param(
        "昨日[きのう]の 夜[よる]",
        "昨日[きのう]の 夜[よる]",
        id="wrong cut - a jukujikun run is not re-cut for a reading that is no better",
    ),
    # Without a kana between two brackets nothing says the readings were cut wrongly
    pytest.param(
        "何[なん]遍[べん]",
        "何[なん]遍[べん]",
        id="wrong cut - two runs with only a bracket between",
    ),
    pytest.param(
        "襤褸[ぼろ] 襤褸[ぼろ]",
        "襤褸[ぼろ] 襤褸[ぼろ]",
        id="wrong cut - two jukujikun runs with only a bracket between",
    ),
    # --- words that cannot be re-cut come back as they were given --------------------------
    pytest.param(
        "ちょっかいを出す[ちょっかいだす]",
        "ちょっかいを出す[ちょっかいだす]",
        id="left alone - the reading does not spell the word's kana",
    ),
    pytest.param(
        "過ち[あやま]",
        "過ち[あやま]",
        id="left alone - a bracket after the okurigana it leaves out",
    ),
    pytest.param(
        "万葉集[まんようしゅ]",
        "万葉集[まんようしゅ]",
        id="left alone - a wrong reading, nothing to cut",
    ),
    pytest.param(" 曝[曝]える", " 曝[曝]える", id="left alone - kanji in the bracket"),
    pytest.param(
        "四Ｋ[よんけー]", "四Ｋ[よんけー]", id="left alone - Latin letters, which no kana spells"
    ),
    pytest.param(
        "C 言語[げんご]",
        "C 言語[げんご]",
        id="left alone - Latin letters beside an ordinary bracket",
    ),
    pytest.param(
        "ヘレン・ケラー", "ヘレン・ケラー", id="left alone - a splitter dot in a kana word"
    ),
    # Degenerate: more of a word than a misplaced bracket explains. The point is that it comes
    # back, and without the search for a cut running away.
    pytest.param(
        "漢あ" * 40 + "[" + "かんあ" * 40 + "]",
        "漢あ" * 40 + "[" + "かんあ" * 40 + "]",
        id="left alone - more runs than an expression has",
    ),
    pytest.param(
        "阪 神 淡 路 大 震 災[はんしんあわじだいしんさい]",
        "阪 神 淡 路 大 震 災[はんしんあわじだいしんさい]",
        id="left alone - more ways to cut than a misplaced bracket leaves",
    ),
]


@pytest.mark.parametrize("word, expected", CASES)
def test_normalize_word(word: str, expected: str):
    # No text, so that the word alone decides what comes back
    assert normalize_word(word, "") == expected


# A sentence can carry the same misplaced bracket as the word, and then only the word as it was
# given matches it.
TEXT_CASES = [
    pytest.param(
        "電子メール[でんしめーる]",
        "ファックスか 電子メール[でんしめーる]で 送[おく]る",
        "電子メール[でんしめーる]",
        id="the text is written with the word's own bracket - not cut again",
    ),
    pytest.param(
        "電子メール[でんしめーる]",
        "ファックスか 電子[でんし]メールで 送[おく]る",
        "電子[でんし]メール",
        id="the text is written with an ordinary bracket - cut again",
    ),
    pytest.param(
        "電子メール[でんしめーる] ",
        "ファックスか 電子メール[でんしめーる] で 送[おく]る",
        "電子メール[でんしめーる]",
        id="the text is written with the word's own bracket - noise still comes off",
    ),
]


@pytest.mark.parametrize("word, text, expected", TEXT_CASES)
def test_normalize_word_for_a_text(word: str, text: str, expected: str):
    assert normalize_word(word, text) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
