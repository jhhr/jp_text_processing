from .check_word_reading_type import WordReadingType, check_word_reading_type

try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger


def test(
    test_name: str,
    word: str,
    expected: WordReadingType = None,
    ignore_fail: bool = False,
    debug: bool = False,
):
    """Run tests for the check_word_reading_type function.
    Args:
        test_name: Name of the test case.
    """
    logger = Logger("debug") if debug else Logger("error")
    result = check_word_reading_type(word, logger=logger)
    if debug:
        print("\n\n")
    try:
        assert result == expected
    except AssertionError:
        if ignore_fail:
            return
        # Re-run with logging enabled to see what went wrong
        check_word_reading_type(word, logger=Logger("debug"))
        print(f"""\033[91m{test_name}
\033[93mExpected: {expected}
\033[92mGot:      {result}
\033[0m""")
        # Stop testing here
        exit(0)


def main():
    # test each tag type, on/kun/juk with 1) single and 2) multiple tags, with a) no ending kana,
    # b) okurigana, c) with non-okuri ending kana and d) both okurigana and non-okuri ending kana
    # for a total of 6 tests per tag type

    # kunyomi single tag
    test(
        test_name="kunyomi only, single tag, no ending kana",
        word="<kun>山[やま]</kun>",
        expected="kun",
    )
    test(
        test_name="kunyomi only, single tag, with okurigana",
        word="<kun>帰[かえ]</kun><oku>る</oku>",
        expected="kun",
    )
    test(
        test_name="kunyomi only, single tag, with non-okuri ending kana",
        word="<kun>既[すで]</kun>に",
        expected="kun",
    )
    test(
        test_name="kunyomi only, single tag, with okurigana and non-okuri ending kana",
        word="<kun>走[はし]</kun><oku>り</oku>だす",
        expected="kun",
    )

    # Kunyomi multi-tag
    test(
        test_name="kunyomi only, multi-tag, no ending kana",
        word="<kun>山[やま]</kun><kun>田[だ]</kun>",
        expected="kun",
    )
    test(
        test_name="kunyomi only, multi-tag, with non-okuri ending kana",
        word="<kun>山[やま]</kun><kun>田[だ]</kun>さん",
        expected="kun",
    )
    test(
        test_name="kunyomi only, multi-tag, with okurigana",
        word="<kun>日[ひ]</kun><kun>帰[がえ]</kun><oku>り</oku>",
        expected="kun",
    )
    test(
        test_name="kunyomi only, multi-tag, with okurigana and non-okuri ending kana",
        word="<kun>日[ひ]</kun><kun>帰[がえ]</kun><oku>り</oku>に",
        expected="kun",
    )

    # onyomi single tag
    test(
        test_name="onyomi only, single tag, no ending kana",
        word="<on> 分[ぶん]</on>",
        expected="on",
    )
    test(
        test_name="onyomi only, single tag, with okurigana",
        word="<on> 博[はく]</on><oku>す</oku>",
        expected="on",
    )
    test(
        test_name="onyomi only, single tag, with non-okuri ending kana",
        word="<on> 単[たん]</on>に",
        expected="on",
    )
    test(
        test_name="onyomi only, single tag, with okurigana and non-okuri ending kana",
        word="<on> 博[はく]</on><oku>す</oku>で",
        expected="on",
    )

    # onyomi multi-tag
    test(
        test_name="onyomi only, multi tag, no ending kana",
        word="<on>学[がっ]</on><on>校[こう]</on>",
        expected="on",
    )
    test(
        test_name="onyomi only, multi tag, with non-okuri ending kana",
        word="<on>学[がっ]</on><on>校[こう]</on>に",
        expected="on",
    )
    test(
        test_name="onyomi only, multi tag, with okurigana",
        word="<on> 茶[ちゃ]</on><on> 化[か]</on><oku>す</oku>",
        expected="on",
    )
    test(
        test_name="onyomi only, multi tag, with okurigana and non-okuri ending kana",
        word="<on> 茶[ちゃ]</on><on> 化[か]</on><oku>す</oku>から",
        expected="on",
    )
    # jukujikun single tag
    test(
        test_name="jukujikun only, single tag, no ending kana",
        word="<juk> 頁[ページ]</juk>",
        expected="juk",
    )
    test(
        test_name="jukujikun only, single tag, with okurigana",
        word="<juk> 勃[た]</juk><oku>つ</oku>",
        expected="juk",
    )
    test(
        test_name="jukujikun only, single tag, with non-okuri ending kana",
        word="<juk> 実[げ]</juk>に",
        expected="juk",
    )
    test(
        test_name="jukujikun only, single tag, with okurigana and non-okuri ending kana",
        word="<juk> 勃[た]</juk><oku>ち</oku>も",
        expected="juk",
    )
    # jukujikun multi-tag
    test(
        test_name="jukujikun only, multi tag, no ending kana",
        word="<juk>今[きょ]</juk><juk>日[う]</juk>",
        expected="juk",
    )
    test(
        test_name="jukujikun only, multi tag, with non-okuri ending kana",
        word="<juk>今[きょ]</juk><juk>日[う]</juk>は",
        expected="juk",
    )
    test(
        test_name="jukujikun only, multi tag, with okurigana",
        word="<juk> 躊[ため]</juk><juk> 躇[ら]</juk><oku>い</oku>",
        expected="juk",
    )
    test(
        test_name="jukujikun only, multi tag, with okurigana and non-okuri ending kana",
        word="<juk> 躊[ため]</juk><juk> 躇[ら]</juk><oku>い</oku>が",
        expected="juk",
    )
    # mixed reading
    test(
        test_name="mixed reading, on and kun tags, no ending kana",
        word="<kun> 丸[まる]</kun><on> 損[ぞん]</on>",
        expected="mix",
    )
    test(
        test_name="mixed reading, on and kun tags, with okurigana",
        word="<on> 不[ふ]</on><kun> 向[む]</kun><oku>き</oku>",
        expected="mix",
    )
    test(
        test_name="mixed reading, on and kun tags, with non-okuri ending kana",
        word="<kun> 若[わか]</kun><on> 死[じ]</on>に",
        expected="mix",
    )
    test(
        test_name="mixed reading, on and kun tags, with okurigana and non-okuri ending kana",
        word="<on> 開[かい]</on><kun> 始[はじ]</kun><oku>め</oku>で",
        expected="mix",
    )
    print("\n\033[92mAll tests passed\033[0m")


if __name__ == "__main__":
    main()
