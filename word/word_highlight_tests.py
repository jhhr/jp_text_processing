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
    except Exception:
        # rerun test with logger enabled to see what went wrong
        print(f"""\033[91mTest "{test_name}" raised an exception.\033[0m""")
        try:
            word_highlight(text, word, logger=Logger("debug"))
        except Exception as e:
            raise e


def main():
    test(
        test_name="Crash test - empty text",
        word="何[なに]",
        text="",
        expected="",
    )
    test(
        test_name="Crash test - None text",
        word="何[なに]",
        text=None,
        expected=None,
    )
    test(
        test_name="Crash test - empty word",
        word="",
        text="何[なに]を しています か？",
        expected="何[なに]を しています か？",
    )
    test(
        test_name="Crash test - None word",
        word=None,
        text="何[なに]を しています か？",
        expected="何[なに]を しています か？",
    )
    test(
        test_name="Crash test - word is just whitespace",
        word="   ",
        text="何[なに]を しています か？",
        expected="何[なに]を しています か？",
    )
    test(
        test_name="Furigana - non-inflected noun in middle of text",
        word="日本語[にほんご]",
        text="私[わたし]は 日本語[にほんご]を 勉強[べんきょう]しています。",
        expected="私[わたし]は<b> 日本語[にほんご]</b>を 勉強[べんきょう]しています。",
    )
    test(
        test_name="Furigana - non-inflected single-kanji noun",
        word="家[いえ]",
        text="家[いえ]で 居[い]る",
        expected="<b>家[いえ]</b>で 居[い]る",
    )
    test(
        test_name="Furigana - non-inflected multi-kanji noun",
        word="魚市場[うおいちば]",
        text="この 魚[さかな]は 魚市場[うおいちば]で 買[か]った",
        expected="この 魚[さかな]は<b> 魚市場[うおいちば]</b>で 買[か]った",
    )
    test(
        test_name="Furigana - non-inflected repeater noun",
        # Also missing furigana for one word to test that it still works
        word="人々[ひとびと]",
        text="彼[かれ]は 人々[ひとびと]の 中で 目立[めだ]つ",
        expected="彼[かれ]は<b> 人々[ひとびと]</b>の 中で 目立[めだ]つ",
    )
    test(
        test_name="Furigana - non-inflected multi-kanji noun where word is split in text",
        word="魚市場[うおいちば]",
        text="<k> 此[こ]の</k> 魚[さかな]は 魚[うお]市場[いちば]で 買[か]いました。",
        # Will change the original text structure slightly by merging the furigana parts
        expected="<k> 此[こ]の</k> 魚[さかな]は<b> 魚市場[うおいちば]</b>で 買[か]いました。",
    )
    test(
        test_name=(
            "Furigana - non-inflected single-kanji noun as part of larger word in text, left side"
        ),
        word="魚[うお]",
        text="この 魚[さかな]は 魚市場[うおいちば]で 買[か]った",
        expected="この 魚[さかな]は<b> 魚[うお]</b> 市場[いちば]で 買[か]った",
    )
    test(
        test_name=(
            "Furigana - non-inflected multi-kanji noun as part of larger word in text, right side"
        ),
        word="時間[じかん]",
        text="労働時間[ろうどうじかん]を 減[へ]らしたい",
        expected="労働[ろうどう]<b> 時間[じかん]</b>を 減[へ]らしたい",
    )
    test(
        test_name=(
            "Furigana - non-inflected multi-kanji noun as part of larger word in text, middle"
        ),
        word="専用[せんよう]",
        text="バイクを 自転車専用道路[じてんしゃせんようどうろ]で 走[はし]らせる",
        expected="バイクを 自転車[じてんしゃ]<b> 専用[せんよう]</b> 道路[どうろ]で 走[はし]らせる",
    )
    test(
        test_name="Furigana - inflected verb as part of larger verb in text",
        word="付[つ]ける",
        text="彼女[かのじょ]への 伝言[でんごん]を 言付[ことづ]けた</k>の。",
        expected="彼女[かのじょ]への 伝言[でんごん]を 言[こと]<b> 付[づ]けた</b></k>の。",
    )
    test(
        test_name="Furigana - verb inflection ている /1",
        word="食[た]べる",
        text="私は 食[た]べている",
        expected="私は<b> 食[た]べている</b>",
    )
    test(
        test_name="Furigana - verb inflection させる /1",
        word="食[た]べる",
        text="食[た]べさせるな!",
        expected="<b>食[た]べさせる</b>な!",
    )
    test(
        test_name="Furigana - verb inflection juku word /1",
        word="聴牌[テンパ]る",
        text="聴牌[テンパ]ってた",
        expected="<b>聴牌[テンパ]ってた</b>",
    )
    test(
        test_name="Furigana - adjective inflection /1",
        word="大[おお]きい",
        text="これ、 大[おお]きすぎない？",
        expected="これ、<b> 大[おお]き</b>すぎない？",
    )
    test(
        test_name="Furigana - adjective inflection /2",
        word="安[やす]い",
        text="安[やす]くて 良[い]いな～",
        expected="<b>安[やす]くて</b> 良[い]いな～",
    )
    test(
        test_name="Furigana - adjective inflection /3",
        word="良[よ]い",
        text="高[たか]いでも 良[よ]かろう",
        expected="高[たか]いでも<b> 良[よ]かろう</b>",
    )
    test(
        test_name="Furigana - adjective inflection with な /1",
        word="早[はや]い",
        text="早読[はやよ]みするぜ",
        expected="<b>早[はや]</b> 読[よ]みするぜ",
    )
    test(
        test_name="Furigana is in katakana in text, word in hiragana",
        word="垂[た]れ 込[こ]み",
        text="垂[タ]レ 込[コ]ミがあった、オイ！",
        expected="<b>垂[タ]レ 込[コ]ミ</b>があった、オイ！",
    )
    test(
        test_name="Furigana is in hiragana in text, word in katakana",
        word="垂[タ]レ 込[コ]ミ",
        text="垂[た]れ 込[こ]みがあった",
        expected="<b>垂[た]れ 込[こ]み</b>があった",
    )
    test(
        test_name="Furigana - multi-kanji noun with okuri in middle /1",
        word="髪[かみ]の 毛[け]",
        text="彼女[かのじょ]の 髪[かみ]の 毛[け]は 長[なが]い",
        expected="彼女[かのじょ]の<b> 髪[かみ]の 毛[け]</b>は 長[なが]い",
    )
    test(
        test_name="Furigana - multi-kanji noun with okuri in middle /2",
        word="飲[の]ん 兵衛[べえ]",
        text="彼[かれ]は 飲[の]ん 兵衛[べえ]だ",
        expected="彼[かれ]は<b> 飲[の]ん 兵衛[べえ]</b>だ",
    )
    test(
        test_name="Furigana - word occurs more than once, simple match",
        word="彼[かれ]",
        text="彼[かれ]は 走[はし]った。彼[かれ]は 速[はや]い。",
        expected="<b>彼[かれ]</b>は 走[はし]った。<b> 彼[かれ]</b>は 速[はや]い。",
    )
    test(
        test_name="Furigana - word occurs more than once, inflected match",
        word="走[はし]る",
        text="彼[かれ]は 走[はし]った。 彼[かれ]の 走[はし]り 方[かた]は 速[はや]い。",
        expected="彼[かれ]は<b> 走[はし]った</b>。 彼[かれ]の<b> 走[はし]り</b> 方[かた]は 速[はや]い。",
    )
    test(
        test_name="Furigana is colloquial /1",
        # Needs some kind of exception handling, can only work when furigana are used
        word="無[ない]",
        text="無[ねえ]な",
        expected="<b>無[ねえ]な</b>",
        ignore_fail=True,
    )
    test(
        test_name="No furigana with kanji - single-kanji noun multiple occurrences",
        word="家",
        text="家で居る、家出はしない",
        expected="<b>家</b>で居る、<b>家</b>出はしない",
    )
    test(
        test_name="No furigana with kanji - multi-kanji noun",
        word="魚市場",
        text="この魚は魚市場で買った",
        expected="この魚は<b>魚市場</b>で買った",
    )
    test(
        test_name="No furigana with kanji - multi-kanji noun with okuri in middle /1",
        word="髪の毛",
        text="彼女の髪の毛は長い",
        expected="彼女の<b>髪の毛</b>は長い",
    )
    test(
        test_name="No furigana with kanji - multi-kanji noun with okuri in middle /2",
        word="飲ん兵衛",
        text="彼は飲ん兵衛だ",
        expected="彼は<b>飲ん兵衛</b>だ",
    )
    test(
        test_name="No furigana with kanji - verb inflection /1",
        word="食べる",
        text="彼は食べている",
        expected="彼は<b>食べている</b>",
    )
    test(
        test_name="No furigana with kanji - verb inflection /2",
        word="苛めめる",
        text="苛めなくていれないのか、お 前は？",
        expected="<b>苛めなくて</b>いれないのか、お 前は？",
    )
    test(
        test_name="No furigana with kanji - adjective inflection /1",
        word="美味しい",
        text="このケーキ、美味しくない？",
        expected="このケーキ、<b>美味しくない</b>？",
    )
    test(
        test_name="No furigana with kanji - adjective inflection /2",
        word="美味しい",
        text="このケーキって、美味しくなくて 残念だったな！",
        expected="このケーキって、<b>美味しくなくて</b> 残念だったな！",
    )
    # Mixing in katakana with the kana-only tests below to ensure conversion back to hiragana works
    test(
        test_name="Kana only - katakana word in text, word in hiragana",
        word="たれこみ",
        text="タレコミがあった",
        expected="<b>タレコミ</b>があった",
    )
    test(
        test_name="Kana only - hiragana word in text, word in katakana",
        word="タレコミ",
        text="たれこみがあった",
        expected="<b>たれこみ</b>があった",
    )
    test(
        test_name="Kana only - katakana in word and text",
        word="マスターページョン",
        text=(
            "<k>此[こん]な</k> 見[み]たら 観客[かんきゃく] 座[すわ]ってるのに 総[そう]"
            " 勃[た]ちでスタンティングオペレーションじゃなくてマスターページョン始[はじ]まっちゃうね。"
        ),
        expected=(
            "<k>此[こん]な</k> 見[み]たら 観客[かんきゃく] 座[すわ]ってるのに 総[そう]"
            " 勃[た]ちでスタンティングオペレーションじゃなくて<b>マスターページョン</b>始[はじ]"
            "まっちゃうね。"
        ),
    )
    test(
        test_name="Kana only - verb inflection /2",
        word="いじめる",
        text="いじめなくていれないのか、お 前[オマエ]は？",
        expected="<b>いじめなくて</b>いれないのか、お 前[オマエ]は？",
    )
    test(
        test_name="Kana only - adjective inflection /1",
        word="おいしい",
        text="このケーキ、おいしくない？",
        expected="このケーキ、<b>おいしくない</b>？",
    )
    test(
        test_name="Kana only - adjective inflection /2",
        word="おいしい",
        text="このケーキって、おいしくなくて 残念[ザンねん]だったな！",
        expected="このケーキって、<b>おいしくなくて</b> 残念[ザンねん]だったな！",
    )
    test(
        test_name="Shouldn't crash with mixture of furigana and non-furigana in word",
        word="総[そう]勃ち",
        text="こんな 見[み]たら 観客[かんきゃく] 座[すわ]ってるのに 総[そう]勃ち だよ",
        # Unable to highlight correctly, but at least shouldn't crash
        expected="こんな 見[み]たら 観客[かんきゃく] 座[すわ]ってるのに<b> 総[そう]勃</b>ち だよ",
    )
    print("\n\033[92mTests passed\033[0m")


if __name__ == "__main__":
    main()
