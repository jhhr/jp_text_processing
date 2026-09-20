"""Cases for `number_to_kanji`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/kanji/number_to_kanji_tests.py

Pass `--log-cli-level=debug` to see what a case logged; pytest captures the package logger on
its own, so nothing here has to turn logging on.

A case's id is the input string, which is what `-k` needs to select one; the inputs whose
whitespace would not show in an id are `(empty)`, `(space)` and `(padded 12)`.
"""

import pytest

from .number_to_kanji import number_to_kanji


CASES = [
    # non-parseable cases return as is
    pytest.param("", "", id="(empty)"),
    pytest.param(" ", " ", id="(space)"),
    pytest.param("abc", "abc", id="abc"),
    pytest.param("123abc", "123abc", id="123abc"),
    pytest.param("１２３あえいおう", "１２３あえいおう", id="１２３あえいおう"),
    pytest.param("123-456", "123-456", id="123-456"),
    # Already in kanji, basically same as non-parseable cases
    pytest.param("億", "億", id="億"),
    pytest.param("零", "零", id="零"),
    pytest.param("万", "万", id="万"),
    pytest.param("一十", "一十", id="一十"),
    pytest.param("二", "二", id="二"),
    pytest.param("三十", "三十", id="三十"),
    pytest.param("四", "四", id="四"),
    pytest.param("五", "五", id="五"),
    pytest.param("六千", "六千", id="六千"),
    pytest.param("七", "七", id="七"),
    pytest.param("八", "八", id="八"),
    pytest.param("九", "九", id="九"),
    pytest.param("十", "十", id="十"),
    pytest.param("３百", "３百", id="３百"),
    pytest.param("千", "千", id="千"),
    pytest.param("0", "零", id="0"),
    pytest.param("０", "零", id="０"),
    pytest.param("1", "一", id="1"),
    pytest.param("１", "一", id="１"),
    pytest.param("2", "二", id="2"),
    pytest.param("２", "二", id="２"),
    pytest.param("3", "三", id="3"),
    pytest.param("３", "三", id="３"),
    pytest.param("4", "四", id="4"),
    pytest.param("４", "四", id="４"),
    pytest.param("5", "五", id="5"),
    pytest.param("５", "五", id="５"),
    pytest.param("6", "六", id="6"),
    pytest.param("６", "六", id="６"),
    pytest.param("7", "七", id="7"),
    pytest.param("７", "七", id="７"),
    pytest.param("8", "八", id="8"),
    pytest.param("８", "八", id="８"),
    pytest.param("9", "九", id="9"),
    pytest.param("９", "九", id="９"),
    pytest.param("10", "十", id="10"),
    pytest.param("１０", "十", id="１０"),
    pytest.param("11", "十一", id="11"),
    pytest.param("１１", "十一", id="１１"),
    # surrounding whitespace is stripped before parsing
    pytest.param(" 12 ", "十二", id="(padded 12)"),
    pytest.param("20", "二十", id="20"),
    pytest.param("２０", "二十", id="２０"),
    pytest.param("21", "二十一", id="21"),
    pytest.param("２１", "二十一", id="２１"),
    pytest.param("30", "三十", id="30"),
    pytest.param("３０", "三十", id="３０"),
    pytest.param("100", "百", id="100"),
    pytest.param("１００", "百", id="１００"),
    pytest.param("123", "百二十三", id="123"),
    pytest.param("１２３", "百二十三", id="１２３"),
    pytest.param("4567", "四千五百六十七", id="4567"),
    pytest.param("４５６７", "四千五百六十七", id="４５６７"),
    pytest.param("89012", "八万九千十二", id="89012"),
    pytest.param("８９０１２", "八万九千十二", id="８９０１２"),
    pytest.param("1000", "千", id="1000"),
    pytest.param("１０００", "千", id="１０００"),
    pytest.param("1200", "千二百", id="1200"),
    pytest.param("11200", "一万千二百", id="11200"),
    # 一 is kept in front of 万 and above, dropped in front of 十/百/千
    pytest.param("10000", "一万", id="10000"),
    pytest.param("１００００", "一万", id="１００００"),
    pytest.param("10001", "一万一", id="10001"),
    pytest.param("１０００１", "一万一", id="１０００１"),
    pytest.param("100000", "十万", id="100000"),
    pytest.param("1000000", "百万", id="1000000"),
    pytest.param("１００００００", "百万", id="１００００００"),
    # a 千 that tops a 万-group keeps its 一: 一千万, not 千万, and it does so whatever else
    # that group holds
    pytest.param("10000000", "一千万", id="10000000"),
    pytest.param("１０００００００", "一千万", id="１０００００００"),
    pytest.param("12000000", "一千二百万", id="12000000"),
    pytest.param("1203000000000000", "一千二百三兆", id="1203000000000000"),
    pytest.param("100000000", "一億", id="100000000"),
    pytest.param("１００００００００", "一億", id="１００００００００"),
    pytest.param("100000000000", "一千億", id="100000000000"),
    pytest.param("1000000000000", "一兆", id="1000000000000"),
    pytest.param("10000000000000000", "一京", id="10000000000000000"),
    pytest.param("1234000000", "十二億三千四百万", id="1234000000"),
    pytest.param("１２３４００００００", "十二億三千四百万", id="１２３４００００００"),
    pytest.param("1234567890", "十二億三千四百五十六万七千八百九十", id="1234567890"),
    pytest.param("１２３４５６７８９０", "十二億三千四百五十六万七千八百九十", id="１２３４５６７８９０"),
    pytest.param("10000400000060000003", "一千京四百兆六千万三", id="10000400000060000003"),
    pytest.param("１００００４００００００６００００００３", "一千京四百兆六千万三", id="１００００４００００００６００００００３"),
    pytest.param("一二三四五六七八九", "一二三四五六七八九", id="一二三四五六七八九"),
]


@pytest.mark.parametrize("num_str, expected", CASES)
def test_number_to_kanji(num_str: str, expected: str):
    assert number_to_kanji(num_str) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
