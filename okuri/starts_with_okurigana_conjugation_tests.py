"""Cases for `starts_with_okurigana_conjugation`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/okuri/starts_with_okurigana_conjugation_tests.py

Pass `--log-cli-level=debug` to see what a case logged; pytest captures the package logger on
its own, so nothing here has to turn logging on.

A case's id is `kanji[kanji_reading]kanji_okurigana + kana_text`, the arguments it is called
with. The expected value is the whole `OkuriResults`:
`(okurigana, rest, result, part_of_speech)`.

A case that is known to fail gets `marks=pytest.mark.xfail(reason="...", strict=True)` in its
`pytest.param`: strict so an unexpected pass fails the run and the reason gets dropped. None of
the cases below need it today.
"""

import pytest

from .starts_with_okurigana_conjugation import starts_with_okurigana_conjugation

CASES = [
    # full okuri tests
    pytest.param(
        "かったら",
        "い",
        "無",
        "な",
        ("かったら", "", "full_okuri", "adj-i"),
        id="無[な]い + かったら",
    ),
    pytest.param(
        "ったか",
        "る",
        "去",
        "さ",
        ("った", "か", "full_okuri", "v5r"),
        id="去[さ]る + ったか",
    ),
    pytest.param(
        "ないで",
        "る",
        "在",
        "あ",
        ("ないで", "", "full_okuri", "v5r-i"),
        id="在[あ]る + ないで",
    ),
    pytest.param(
        "んでくれ",
        "ぬ",
        "死",
        "し",
        ("んで", "くれ", "full_okuri", "v5n"),
        id="死[し]ぬ + んでくれ",
    ),
    pytest.param(
        "くない",
        "きい",
        "大",
        "おお",
        ("くない", "", "full_okuri", "adj-i"),
        id="大[おお]きい + くない",
    ),
    pytest.param(
        "くないよ",
        "さい",
        "小",
        "ちい",
        ("くない", "よ", "full_okuri", "adj-i"),
        id="小[ちい]さい + くないよ",
    ),
    pytest.param(
        "している",
        "る",
        "為",
        "す",
        ("して", "いる", "full_okuri", "vs-i"),
        id="為[す]る + している",
    ),
    pytest.param(
        "させられた",
        "る",
        "為",
        "す",
        ("させられた", "", "full_okuri", "vs-i"),
        id="為[す]る + させられた",
    ),
    pytest.param(
        "せずに",
        "る",
        "為",
        "す",
        ("せず", "に", "full_okuri", "vs-i"),
        id="為[す]る + せずに",
    ),
    pytest.param(
        "してた",
        "する",
        "動",
        "どう",
        # suru verbs should be vs-s but that's difficult to detect
        # When actually dealing with suru verbs, part_of_speech should be provided to the function
        # to get the correct okuri progression
        ("してた", "", "full_okuri", "vs-i"),
        id="動[どう]する + してた",
    ),
    pytest.param(
        "いでる",
        "ぐ",
        "泳",
        "およ",
        ("いで", "る", "full_okuri", "v5g"),
        id="泳[およ]ぐ + いでる",
    ),
    pytest.param(
        "いです",
        "い",
        "良",
        "よ",
        ("い", "です", "full_okuri", "adj-i"),
        id="良[よ]い + いです",
    ),
    pytest.param(
        "つ",
        "つ",
        "待",
        "ま",
        ("つ", "", "full_okuri", "v5t"),
        id="待[ま]つ + つ",
    ),
    pytest.param(
        "いてたか",
        "く",
        "聞",
        "き",
        ("いて", "たか", "full_okuri", "v5k"),
        id="聞[き]く + いてたか",
    ),
    pytest.param(
        "たい",
        "る",
        "見",
        "み",
        ("たい", "", "full_okuri", "v1"),
        id="見[み]る + たい",
    ),
    pytest.param(
        "った",
        "る",
        "去",
        "さ",
        ("った", "", "full_okuri", "v5r"),
        id="去[さ]る + った",
    ),
    # partial okuri tests
    pytest.param(
        # 聞[き]い is only the start of 聞[き]いて/聞[き]いた, the text ends mid-conjugation
        "い",
        "く",
        "聞",
        "き",
        ("い", "", "partial_okuri", "v5k"),
        id="聞[き]く + い",
    ),
    pytest.param(
        # 泳[およ]ぐ takes いで/いだ, so た is not a continuation and 泳[およ]い is left partial
        "いた",
        "ぐ",
        "泳",
        "およ",
        ("い", "た", "partial_okuri", "v5g"),
        id="泳[およ]ぐ + いた",
    ),
    # empty okuri tests
    pytest.param(
        # 恥[は]ずかしげな is an i-adjective, not na-adjective!
        "げな",
        "ずかしい",
        "恥",
        "は",
        ("", "げな", "empty_okuri", "adj-i"),
        id="恥[は]ずかしい + げな",
    ),
    # no okuri tests
    pytest.param(
        # only an i-adjective stem can stand bare; 見方 is the noun 見 plus かた, not 見る
        # with an empty conjugation
        "かた",
        "る",
        "見",
        "み",
        ("", "かた", "no_okuri", None),
        id="見[み]る + かた",
    ),
    pytest.param(
        "こむ",
        "む",
        "読",
        "よ",
        ("", "こむ", "no_okuri", None),
        id="読[よ]む + こむ",
    ),
]


@pytest.mark.parametrize("kana_text, kanji_okurigana, kanji, kanji_reading, expected", CASES)
def test_starts_with_okurigana_conjugation(
    kana_text: str,
    kanji_okurigana: str,
    kanji: str,
    kanji_reading: str,
    expected: tuple[str, str, str, str],
):
    result = starts_with_okurigana_conjugation(kana_text, kanji_okurigana, kanji, kanji_reading)
    assert tuple(result) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
