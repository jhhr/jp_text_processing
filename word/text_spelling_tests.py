"""Cases for `text_spelling`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/word/text_spelling_tests.py

What `word_highlight` then finds with a respelled word is in `word_highlight_tests.py`.
"""

import re

import pytest

from .text_spelling import spelled_as_in_text, whole_number_pattern

RESPELLING_CASES = [
    pytest.param(
        "七[なな]つ",
        "海賊[かいぞく]は ７[なな]つの 海[うみ]を",
        "７[なな]つ",
        id="number - a numeral for a full-width digit",
    ),
    pytest.param(
        " 五[ご]",
        "一部[いちぶ]には 5 mを 越[こ]える",
        " 5[ご]",
        id="number - a numeral for a half-width digit",
    ),
    pytest.param(
        " 二十[にじゅう]",
        "直径[ちょっけい]２０ ｃｍ[せんち]",
        " ２０[にじゅう]",
        id="number - two numerals for two digits",
    ),
    pytest.param(
        " 百十九番[ひゃくじゅうきゅうばん]",
        "火事[かじ]です。１１９ 番[ばん]に",
        " １１９番[ひゃくじゅうきゅうばん]",
        id="number - three numerals for three digits, a kanji after them",
    ),
    pytest.param(
        "第一[だいいち]",
        "第[だい]２の平坦[へいたん]部[ぶ]は、 第[だい]１の",
        "第１[だいいち]",
        id="number - a numeral after a kanji",
    ),
    pytest.param(
        " 千[せん]",
        "胆石[たんせき]。 １０００[せん]<k> 居[い]る 内[うち]</k>",
        " １０００[せん]",
        id="number - a unit for a digit and its zeros",
    ),
    pytest.param(
        "零点[れいてん]",
        "また ０点[れいてん]を 取[と]った",
        "０点[れいてん]",
        id="number - zero",
    ),
    # 万 and the units above it are written out after digits as well, so the numerals before
    # one are a number of their own; the whole of it in digits is the same number too
    pytest.param(
        " 一万円[いちまんえん]",
        "日給[にっきゅう]1 万[まん] 円[えん]だ",
        " 1万円[いちまんえん]",
        id="number - the numeral before 万 for a digit",
    ),
    pytest.param(
        " 一万円[いちまんえん]",
        "日給[にっきゅう]１００００ 円[えん]だ",
        " １００００円[いちまんえん]",
        id="number - a numeral and 万 for the digits of the whole number",
    ),
    pytest.param(
        "二千万[にせんまん]",
        "人口[じんこう]は２０００ 万[まん]だ",
        "２０００万[にせんまん]",
        id="number - the numerals before 万 for their digits",
    ),
    # A number is all of its numerals and all of its digits
    pytest.param(
        " 十[じゅう]",
        "直径[ちょっけい]２０ ｃｍ[せんち]",
        " 十[じゅう]",
        id="number - a numeral is not the digits of a number it is part of",
    ),
    pytest.param(
        " 二十[にじゅう]",
        "２ 階[かい]と１０ 階[かい]",
        " 二十[にじゅう]",
        id="number - the numerals of one number are not two numbers",
    ),
    pytest.param(
        " 一[いち]",
        "明朝[みょうちょう]１０ 時[じ]から",
        " 一[いち]",
        id="number - a numeral is not a digit of a longer number",
    ),
    pytest.param(
        " 三[さん]",
        "高[たか]さは３，７７６メートル",
        " 三[さん]",
        id="number - a numeral is not a digit before a separator",
    ),
    pytest.param(
        " 六[ろく]",
        "約[やく]7.6 兆[ちょう] 円[えん]",
        " 六[ろく]",
        id="number - a numeral is not a digit after a decimal point",
    ),
    pytest.param(
        "二千円[にせんえん]",
        "２ 千[せん] 円[えん]",
        "二千円[にせんえん]",
        id="number - the numeral before 千 is not a number of its own",
    ),
    # The other way round: digits in the word, which stay when the text has the number in
    # digits of either width
    pytest.param(
        "20日[はつか]",
        "来月[らいげつ]の 二十日[はつか]に",
        "二十日[はつか]",
        id="number - digits for numerals",
    ),
    pytest.param(
        " 2[に]",
        "二十[にじゅう] 回[かい]",
        " 2[に]",
        id="number - a digit is not a numeral of a longer number",
    ),
    pytest.param(
        " 2[に]ちゃんねる",
        "２ちゃんねると 二[に]ちゃんねる",
        " 2[に]ちゃんねる",
        id="number - digits stay where the text has the number in digits too",
    ),
    # What is not text is not searched for numbers, and what is no number is left alone
    pytest.param(
        " 一[いち]",
        '<font size="1"> 第[だい]２</font>',
        " 一[いち]",
        id="number - a digit inside a tag is not the text's",
    ),
    pytest.param(
        "食[た]べる",
        "７[なな]つも 食[た]べた",
        "食[た]べる",
        id="number - a word without a number",
    ),
    pytest.param(
        "七[なな]つ",
        "七[なな]つの 海[うみ]",
        "七[なな]つ",
        id="number - a text without digits",
    ),
    # Degenerate: more digits than there are units to write them with are no number here. The
    # point is that they are not converted, which takes long and gives nothing.
    pytest.param(
        " 一[いち]",
        "1" * 400,
        " 一[いち]",
        id="number - a run of digits too long to be a number",
    ),
    pytest.param(
        "駄駄[だだ]",
        "そんなに<k> 駄々[だだ]</k>を<k> 捏[こ]ねる 物[もん]</k>じゃない。",
        "駄々[だだ]",
        id="repeated kanji - written twice for 々",
    ),
    pytest.param(
        " 民主々義[みんしゅしゅぎ]",
        " 民主[みんしゅ]主義[しゅぎ]に<k> 就[つ]いて</k>",
        " 民主主義[みんしゅしゅぎ]",
        id="repeated kanji - 々 for the kanji again, across the text's brackets",
    ),
    pytest.param(
        "主々[しゅしゅ]",
        "主[しゅ] 主[しゅ]",
        "主主[しゅしゅ]",
        id="repeated kanji - 々 for the kanji again, across the text's space",
    ),
    pytest.param(
        "時々[ときどき]",
        "時[とき]が 経[た]つ",
        "時々[ときどき]",
        id="repeated kanji - a text with the kanji once",
    ),
    pytest.param(
        " 百十九番[ひゃくじゅうきゅうばん]",
        "１１９ 番[ばん]の 人々[ひとびと]",
        " １１９番[ひゃくじゅうきゅうばん]",
        id="repeated kanji - a word without one",
    ),
]


@pytest.mark.parametrize("word, text, expected", RESPELLING_CASES)
def test_spelled_as_in_text(word: str, text: str, expected: str):
    assert spelled_as_in_text(word, text) == expected


# What a piece of the word is found as, in a text of candidates separated by spaces
PATTERN_CASES = [
    pytest.param("１", "１ １０ 1 11 ２１", ["１", "1"], id="a digit, in either width"),
    pytest.param("20", "１２０ ２０ 20 ２００", ["２０", "20"], id="two digits"),
    pytest.param("第２", "第２ 第２０ 第2", ["第２", "第2"], id="a digit after a kanji"),
    pytest.param("3", "３，７７６ 7.3 ３", ["３"], id="a digit beside a separator"),
    pytest.param("1.5", "1.5 11.5 1.55 1x5", ["1.5"], id="a number with a decimal point"),
    pytest.param("何か", "何か 何[か]", ["何か"], id="no number"),
]


@pytest.mark.parametrize("word_part, text, expected", PATTERN_CASES)
def test_whole_number_pattern(word_part: str, text: str, expected: list[str]):
    assert re.findall(whole_number_pattern(word_part), text) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
