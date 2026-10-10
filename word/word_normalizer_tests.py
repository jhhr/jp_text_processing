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
]


@pytest.mark.parametrize("word, expected", CASES)
def test_normalize_word(word: str, expected: str):
    assert normalize_word(word) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
