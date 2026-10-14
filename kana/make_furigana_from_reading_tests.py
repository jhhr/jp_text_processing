"""Cases for `make_furigana_from_reading`, which writes a word's reading over its kanji, with
pytest from `anki_shared/`:

    python -m pytest jp_text_processing/kana/make_furigana_from_reading_tests.py

The function only puts the reading in a bracket after the word and has `kana_highlight` split
it, so the split itself is tested in the suites of the passes that make it. What these pin is the
result as a caller gets it, which is what match_words_to_notes writes into a note's
vocab-furigana.

A case that is known to fail gets `marks=pytest.mark.xfail(reason="...", strict=True)` in its
`pytest.param`. None of the cases below need it today.
"""

import pytest

from .make_furigana_from_reading import make_furigana_from_reading

CASES = [
    # --- the okurigana between two kanji fits the reading in more than one place -----------
    # 好 reads すき as well as す, and the き after it was given to it as both: 好[すき]き 嫌[ら]い.
    pytest.param(
        "好き嫌い",
        "すききらい",
        " 好[す]き 嫌[きら]い",
        id="好き嫌い, whose き the reading of 嫌 opens with",
    ),
    pytest.param(
        "指し示す",
        "さししめす",
        " 指[さ]し 示[しめ]す",
        id="指し示す, whose し the reading of 示 opens with",
    ),
    pytest.param(
        "お笑い芸人",
        "おわらいげいにん",
        "お 笑[わら]い 芸人[げいにん]",
        id="お笑い芸人, whose い the reading of 芸人 opens with",
    ),
    pytest.param(
        "物の怪",
        "もののけ",
        " 物[もの]の 怪[け]",
        id="物の怪, whose の the reading of 物 ends with",
    ),
    # --- words whose okurigana fits one place, or whose reading repeats --------------------
    pytest.param("好き", "すき", " 好[す]き", id="好き"),
    pytest.param("好き好き", "すきずき", " 好[す]き 好[ず]き", id="好き好き"),
    pytest.param("書き切る", "かききる", " 書[か]き 切[き]る", id="書き切る"),
    pytest.param("磨き切る", "みがききる", " 磨[みが]き 切[き]る", id="磨き切る"),
    pytest.param("焼き切る", "やききる", " 焼[や]き 切[き]る", id="焼き切る"),
    pytest.param("引き抜き", "ひきぬき", " 引[ひ]き 抜[ぬ]き", id="引き抜き"),
    pytest.param("書き書き", "かきかき", " 書[か]き 書[か]き", id="書き書き"),
    pytest.param("見る見る", "みるみる", " 見[み]る 見[み]る", id="見る見る"),
    pytest.param("泣き明かし", "なきあかし", " 泣[な]き 明[あ]かし", id="泣き明かし"),
    pytest.param("行き来", "いきき", " 行[い]き 来[き]", id="行き来"),
    pytest.param("聞き手", "ききて", " 聞[き]き 手[て]", id="聞き手"),
]


@pytest.mark.parametrize("word, reading, expected", CASES)
def test_make_furigana_from_reading(word: str, reading: str, expected: str):
    """The reading written over `word` comes out as `expected`."""
    assert make_furigana_from_reading(word, reading) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
