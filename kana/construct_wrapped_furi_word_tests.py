"""Cases for `construct_wrapped_furi_word`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/kana/construct_wrapped_furi_word_tests.py

Pass `--log-cli-level=debug` to see what a case logged; pytest captures the package logger on
its own, so nothing here has to turn logging on.

Every word is rendered in each of the six modes the function has — the three return types,
merged and unmerged — so a case is one word in one mode and its id reads `漢字-furigana merged`.
Each entry in `CASES` gives the word's wrap entries and its expected output per mode, keyed by
the mode's id.
"""

import pytest

from ..all_types.main_types import WrapMatchEntry, WrapTag
from .construct_wrapped_furi_word import FuriReconstruct, construct_wrapped_furi_word


def entry(
    kanji: str, tag: WrapTag, furigana: str, highlight: bool = False, is_num: bool = False
) -> WrapMatchEntry:
    """Shorthand for a test case's wrap entry, in the shape reconstruct_from_alignment builds."""
    return WrapMatchEntry(
        kanji=kanji, tag=tag, furigana=furigana, highlight=highlight, is_num=is_num
    )


MODES = [
    pytest.param("kana_only", "kana_only", False, id="kana_only"),
    pytest.param("kana_only merged", "kana_only", True, id="kana_only merged"),
    pytest.param("furigana", "furigana", False, id="furigana"),
    pytest.param("furikanji", "furikanji", False, id="furikanji"),
    pytest.param("furigana merged", "furigana", True, id="furigana merged"),
    pytest.param("furikanji merged", "furikanji", True, id="furikanji merged"),
]


CASES = [
    pytest.param(
        # one part highlighted, other not, no difference when merging
        [
            entry("漢", "on", "かん", highlight=True),
            entry("字", "on", "じ"),
        ],
        {
            "kana_only": "<b><on>かん</on></b><on>じ</on>",
            "kana_only merged": "<b><on>かん</on></b><on>じ</on>",
            "furigana": "<b><on> 漢[かん]</on></b><on> 字[じ]</on>",
            "furikanji": "<b><on> かん[漢]</on></b><on> じ[字]</on>",
            "furigana merged": "<b><on> 漢[かん]</on></b><on> 字[じ]</on>",
            "furikanji merged": "<b><on> かん[漢]</on></b><on> じ[字]</on>",
        },
        id="漢字",
    ),
    pytest.param(
        [
            entry("大", "juk", "おと"),
            entry("人", "juk", "な"),
        ],
        {
            "kana_only": "<juk>おと</juk><juk>な</juk>",
            "kana_only merged": "<juk>おとな</juk>",
            "furigana": "<juk> 大[おと]</juk><juk> 人[な]</juk>",
            "furikanji": "<juk> おと[大]</juk><juk> な[人]</juk>",
            "furigana merged": "<juk> 大人[おとな]</juk>",
            "furikanji merged": "<juk> おとな[大人]</juk>",
        },
        id="大人",
    ),
    pytest.param(
        # different tags, should not merge
        [
            entry("友", "kun", "とも"),
            entry("達", "on", "だち"),
        ],
        {
            "kana_only": "<kun>とも</kun><on>だち</on>",
            "kana_only merged": "<kun>とも</kun><on>だち</on>",
            "furigana": "<kun> 友[とも]</kun><on> 達[だち]</on>",
            "furikanji": "<kun> とも[友]</kun><on> だち[達]</on>",
            "furigana merged": "<kun> 友[とも]</kun><on> 達[だち]</on>",
            "furikanji merged": "<kun> とも[友]</kun><on> だち[達]</on>",
        },
        id="友達",
    ),
    pytest.param(
        # repeated kanji, one entry covering both characters
        [entry("悠々", "on", "ゆうゆう")],
        {
            "kana_only": "<on>ゆうゆう</on>",
            "kana_only merged": "<on>ゆうゆう</on>",
            "furigana": "<on> 悠々[ゆうゆう]</on>",
            "furikanji": "<on> ゆうゆう[悠々]</on>",
            "furigana merged": "<on> 悠々[ゆうゆう]</on>",
            "furikanji merged": "<on> ゆうゆう[悠々]</on>",
        },
        id="悠々",
    ),
    pytest.param(
        # both parts not highlighted and same tag, can get merged
        [
            entry("時", "on", "ジ"),
            entry("間", "on", "カン"),
        ],
        {
            "kana_only": "<on>ジ</on><on>カン</on>",
            "kana_only merged": "<on>ジカン</on>",
            "furigana": "<on> 時[ジ]</on><on> 間[カン]</on>",
            "furikanji": "<on> ジ[時]</on><on> カン[間]</on>",
            "furigana merged": "<on> 時間[ジカン]</on>",
            "furikanji merged": "<on> ジカン[時間]</on>",
        },
        id="時間",
    ),
    pytest.param(
        # three same tag parts, can get merged
        [
            entry("不", "on", "ふ"),
            entry("自", "on", "じ"),
            entry("然", "on", "ぜん"),
        ],
        {
            "kana_only": "<on>ふ</on><on>じ</on><on>ぜん</on>",
            "kana_only merged": "<on>ふじぜん</on>",
            "furigana": "<on> 不[ふ]</on><on> 自[じ]</on><on> 然[ぜん]</on>",
            "furikanji": "<on> ふ[不]</on><on> じ[自]</on><on> ぜん[然]</on>",
            "furigana merged": "<on> 不自然[ふじぜん]</on>",
            "furikanji merged": "<on> ふじぜん[不自然]</on>",
        },
        id="不自然",
    ),
    pytest.param(
        # a number block, always merged into one reading
        [
            entry("11", "on", "じゅういっ", is_num=True),
            entry("個", "on", "こ"),
        ],
        {
            "kana_only": "<on>じゅういっ</on><on>こ</on>",
            "kana_only merged": "<on>じゅういっこ</on>",
            "furigana": "<on> 11[じゅういっ]</on><on> 個[こ]</on>",
            "furikanji": "<on> じゅういっ[11]</on><on> こ[個]</on>",
            "furigana merged": "<on> 11個[じゅういっこ]</on>",
            "furikanji merged": "<on> じゅういっこ[11個]</on>",
        },
        id="11個",
    ),
    pytest.param(
        # a number block read with two tags, so the second entry carries no kanji of its
        # own; furigana and furikanji merge it into the block and tag the result <mix>
        [
            entry("40", "kun", "よん", is_num=True),
            entry("", "on", "じゅっ", is_num=True),
            entry("分", "on", "ぷん"),
        ],
        {
            "kana_only": "<kun>よん</kun><on>じゅっ</on><on>ぷん</on>",
            "kana_only merged": "<kun>よん</kun><on>じゅっぷん</on>",
            "furigana": "<mix> 40[よんじゅっ]</mix><on> 分[ぷん]</on>",
            "furikanji": "<mix> よんじゅっ[40]</mix><on> ぷん[分]</on>",
            "furigana merged": "<mix> 40[よんじゅっ]</mix><on> 分[ぷん]</on>",
            "furikanji merged": "<mix> よんじゅっ[40]</mix><on> ぷん[分]</on>",
        },
        id="40分",
    ),
]


@pytest.mark.parametrize("mode, return_type, merge_consecutive", MODES)
@pytest.mark.parametrize("entries, expected", CASES)
def test_construct_wrapped_furi_word(
    entries: list[WrapMatchEntry],
    expected: dict[str, str],
    mode: str,
    return_type: FuriReconstruct,
    merge_consecutive: bool,
):
    result = construct_wrapped_furi_word(entries, return_type, merge_consecutive)
    assert result == expected[mode]


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
