import sys

from .word_highlight import word_highlight

try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger  # type: ignore[no-redef]


def test(
    test_name: str,
    text: str,
    word: str,
    expected: str = None,
    ignore_fail: bool = False,
    debug: bool = False,
):
    """Run tests for the word_highlight function.
    Args:
        test_name: Name of the test case.
    """
    logger = Logger("debug") if debug else Logger("error")
    try:
        result = word_highlight(text, word, logger=logger)
        if debug:
            print("\n\n")
        assert result == expected
    except AssertionError:
        if ignore_fail:
            return
        # Re-run with logging enabled to see what went wrong
        word_highlight(text, word, logger=Logger("debug"))
        # Highlight the diff between the expected and the result
        print(f"""\033[91m{test_name}
\033[93mExpected: {expected}
\033[92mGot:      {result}
\033[0m""")
        # Stop testing here
        sys.exit(0)
    except Exception as e:
        # rerun test with logger enabled to see what went wrong
        print(f"""\033[91mTest "{test_name}" raised an exception: {e}\033[0m""")
        raise e


def main():
    test(
        test_name="Non-inflected noun in middle of text",
        text="私[わたし]は 日本語[にほんご]を 勉強[べんきょう]しています。",
        word="日本語[にほんご]",
        expected="私[わたし]は<b> 日本語[にほんご]</b>を 勉強[べんきょう]しています。",
    )
    test(
        test_name="Non-inflected noun at beginning of text",
        text="家[いえ]で 居[い]る",
        word="家[いえ]",
        expected="<b>家[いえ]</b>で 居[い]る",
    )
    test(
        test_name="Verb inflection ている /1",
        text="私は 食[た]べている",
        word="食[た]べる",
        expected="私は<b> 食[た]べている</b>",
    )
    test(
        test_name="Verb inflection させる /1",
        text="食[た]べさせるな!",
        word="食[た]べる",
        expected="<b>食[た]べさせる</b>な!",
    )
    test(
        test_name="Kana only verb inflection /1",
        text="いじめないで！",
        word="いじめる",
        expected="<b>いじめないで</b>！",
        ignore_fail=True,
    )
    test(
        test_name="Verb inflection juku word /1",
        text="聴牌[テンパ]ってた",
        word="聴牌[テンパ]る",
        expected="<b>聴牌[テンパ]ってた</b>",
    )
    test(
        test_name="Adjective inflection /1",
        text="これ、 大[おお]きすぎない？",
        word="大[おお]きい",
        expected="これ、<b> 大[おお]き</b>すぎない？",
    )
    test(
        test_name="Adjective inflection /2",
        text="安[やす]くて 良[い]いな～",
        word="安[やす]い",
        expected="<b>安[やす]くて</b> 良[い]いな～",
    )
    test(
        test_name="Adjective inflection /3",
        text="高[たか]いでも 良[よ]かろう",
        word="良[よ]い",
        expected="高[たか]いでも<b> 良[よ]かろう</b>",
    )
    test(
        test_name="Adjective inflection with な /1",
        text="早読[はやよ]みするぜ",
        word="早[はや]い",
        expected="<b>早[はや]</b> 読[よ]みするぜ",
    )
    test(
        test_name="Furigana is in katakana /1",
        text="垂[タ]レ 込[コ]ミがあった",
        word="垂[た]れ 込[こ]み",
        expected="<b>垂[タ]レ 込[コ]ミ</b>があった",
    )
    test(
        test_name="Katakana word /1",
        text="タレコミがあった",
        word="たれこみ",
        expected="<b>タレコミ</b>があった",
    )
    test(
        test_name="Furigana is colloquial /1",
        text="無[ねえ]な",
        word="無[ない]",
        expected="<b>無[ねえ]な</b>",
        ignore_fail=True,
    )
    print("\n\033[92mTests passed\033[0m")


if __name__ == "__main__":
    main()
