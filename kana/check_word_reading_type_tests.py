"""Cases for `check_word_reading_type`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/kana/check_word_reading_type_tests.py

Pass `--log-cli-level=debug` to see what the function logged for a case; pytest captures the
package logger on its own, so nothing here has to turn logging on.

A case that is known to fail gets `marks=pytest.mark.xfail(reason="...", strict=True)` in its
`pytest.param`: strict so an unexpected pass fails the run and the reason gets dropped. None
of the cases below need it today.
"""

import pytest

from .check_word_reading_type import WordReadingType, check_word_reading_type

# Each tag type, on/kun/juk, with 1) a single and 2) multiple tags, and a) no ending kana,
# b) okurigana, c) non-okuri ending kana and d) both — six cases per tag type.
CASES = [
    # kunyomi single tag
    pytest.param("<kun>山[やま]</kun>", "kun", id="kunyomi only, single tag, no ending kana"),
    pytest.param(
        "<kun>帰[かえ]</kun><oku>る</oku>",
        "kun",
        id="kunyomi only, single tag, with okurigana",
    ),
    pytest.param(
        "<kun>既[すで]</kun>に",
        "kun",
        id="kunyomi only, single tag, with non-okuri ending kana",
    ),
    pytest.param(
        "<kun>走[はし]</kun><oku>り</oku>だす",
        "kun",
        id="kunyomi only, single tag, with okurigana and non-okuri ending kana",
    ),
    # Kunyomi multi-tag
    pytest.param(
        "<kun>山[やま]</kun><kun>田[だ]</kun>",
        "kun",
        id="kunyomi only, multi-tag, no ending kana",
    ),
    pytest.param(
        "<kun>山[やま]</kun><kun>田[だ]</kun>さん",
        "kun",
        id="kunyomi only, multi-tag, with non-okuri ending kana",
    ),
    pytest.param(
        "<kun>日[ひ]</kun><kun>帰[がえ]</kun><oku>り</oku>",
        "kun",
        id="kunyomi only, multi-tag, with okurigana",
    ),
    pytest.param(
        "<kun>日[ひ]</kun><kun>帰[がえ]</kun><oku>り</oku>に",
        "kun",
        id="kunyomi only, multi-tag, with okurigana and non-okuri ending kana",
    ),
    # onyomi single tag
    pytest.param("<on> 分[ぶん]</on>", "on", id="onyomi only, single tag, no ending kana"),
    pytest.param(
        "<on> 博[はく]</on><oku>す</oku>",
        "on",
        id="onyomi only, single tag, with okurigana",
    ),
    pytest.param(
        "<on> 単[たん]</on>に",
        "on",
        id="onyomi only, single tag, with non-okuri ending kana",
    ),
    pytest.param(
        "<on> 博[はく]</on><oku>す</oku>で",
        "on",
        id="onyomi only, single tag, with okurigana and non-okuri ending kana",
    ),
    # onyomi multi-tag
    pytest.param(
        "<on>学[がっ]</on><on>校[こう]</on>",
        "on",
        id="onyomi only, multi tag, no ending kana",
    ),
    pytest.param(
        "<on>学[がっ]</on><on>校[こう]</on>に",
        "on",
        id="onyomi only, multi tag, with non-okuri ending kana",
    ),
    pytest.param(
        "<on> 茶[ちゃ]</on><on> 化[か]</on><oku>す</oku>",
        "on",
        id="onyomi only, multi tag, with okurigana",
    ),
    pytest.param(
        "<on> 茶[ちゃ]</on><on> 化[か]</on><oku>す</oku>から",
        "on",
        id="onyomi only, multi tag, with okurigana and non-okuri ending kana",
    ),
    # jukujikun single tag
    pytest.param("<juk> 頁[ページ]</juk>", "juk", id="jukujikun only, single tag, no ending kana"),
    pytest.param(
        "<juk> 勃[た]</juk><oku>つ</oku>",
        "juk",
        id="jukujikun only, single tag, with okurigana",
    ),
    pytest.param(
        "<juk> 実[げ]</juk>に",
        "juk",
        id="jukujikun only, single tag, with non-okuri ending kana",
    ),
    pytest.param(
        "<juk> 勃[た]</juk><oku>ち</oku>も",
        "juk",
        id="jukujikun only, single tag, with okurigana and non-okuri ending kana",
    ),
    # jukujikun multi-tag
    pytest.param(
        "<juk>今[きょ]</juk><juk>日[う]</juk>",
        "juk",
        id="jukujikun only, multi tag, no ending kana",
    ),
    pytest.param(
        "<juk>今[きょ]</juk><juk>日[う]</juk>は",
        "juk",
        id="jukujikun only, multi tag, with non-okuri ending kana",
    ),
    pytest.param(
        "<juk> 躊[ため]</juk><juk> 躇[ら]</juk><oku>い</oku>",
        "juk",
        id="jukujikun only, multi tag, with okurigana",
    ),
    pytest.param(
        "<juk> 躊[ため]</juk><juk> 躇[ら]</juk><oku>い</oku>が",
        "juk",
        id="jukujikun only, multi tag, with okurigana and non-okuri ending kana",
    ),
    # mixed reading
    pytest.param(
        "<kun> 丸[まる]</kun><on> 損[ぞん]</on>",
        "mix",
        id="mixed reading, on and kun tags, no ending kana",
    ),
    pytest.param(
        "<on> 不[ふ]</on><kun> 向[む]</kun><oku>き</oku>",
        "mix",
        id="mixed reading, on and kun tags, with okurigana",
    ),
    pytest.param(
        "<kun> 若[わか]</kun><on> 死[じ]</on>に",
        "mix",
        id="mixed reading, on and kun tags, with non-okuri ending kana",
    ),
    pytest.param(
        "<on> 開[かい]</on><kun> 始[はじ]</kun><oku>め</oku>で",
        "mix",
        id="mixed reading, on and kun tags, with okurigana and non-okuri ending kana",
    ),
]


@pytest.mark.parametrize("word, expected", CASES)
def test_check_word_reading_type(word: str, expected: WordReadingType):
    assert check_word_reading_type(word) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
