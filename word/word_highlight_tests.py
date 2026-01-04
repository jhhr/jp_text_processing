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
        text="彼女[かのじょ]への 伝言[でんごん]を 言付[ことづ]けたの。",
        expected="彼女[かのじょ]への 伝言[でんごん]を 言[こと]<b> 付[づ]けた</b>の。",
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
        test_name="Furigana - word is split by html tags in text /1",
        word="何[なん]でも 無[な]い",
        text=(
            "<div>「<k> 糞[クソ]</k><k> 程[ほど]</k><k> 詰[つま]らん</k>。<k> 何[なん]</k>でも<k>"
            " 無[な]い</k> 女[おんな]の 会話[かいわ]。」</div><div>「<k> 其[そ]れ</k>、"
            " 特大[とくだい]ブーメランじゃねぇ？」</div>"
        ),
        expected=(
            "<div>「<k> 糞[クソ]</k><k> 程[ほど]</k><k> 詰[つま]らん</k>。<b><k> 何[なん]</k>"
            "でも<k> 無[な]い</k></b> 女[おんな]の 会話[かいわ]。」</div><div>「<k> 其[そ]れ</k>、"
            " 特大[とくだい]ブーメランじゃねぇ？」</div>"
        ),
    )
    test(
        test_name="Furigana - word is split by html tags in text /2",
        word="花一匁[はないちもんめ]",
        text=(
            "<k> 此[こ]れ</k>ってなんか 花[はな]<k> 一匁[いちもんめ]</k>だっけ？<k>"
            " 彼[あれ]</k><k> 位[ぐらい]</k>の<k> 乗[ノリ]</k>？"
        ),
        expected=(
            "<k> 此[こ]れ</k>ってなんか<b> 花[はな]<k> 一匁[いちもんめ]</k></b>だっけ？<k>"
            " 彼[あれ]</k><k> 位[ぐらい]</k>の<k> 乗[ノリ]</k>？"
        ),
    )
    test(
        test_name="Furigana - word with repeater and okuri",
        word="嬉々[きき]として",
        text=(
            "通常[つうじょう]で<k> 有[あ]れば</k> 忌[い]み 嫌[きら]われる<k> 筈[はず]</k>の<k>"
            " 此[こ]れ</k>ら<k> 糞[クソ]</k>ゲーを 嬉々[きき]として 求[もと]める 者[もの]<k>"
            " 達[たち]</k>"
        ),
        expected=(
            "通常[つうじょう]で<k> 有[あ]れば</k> 忌[い]み 嫌[きら]われる<k> 筈[はず]</k>の<k>"
            " 此[こ]れ</k>ら<k> 糞[クソ]</k>ゲーを<b> 嬉々[きき]として</b> 求[もと]める 者[もの]<k>"
            " 達[たち]</k>"
        ),
    )
    test(
        test_name="Furigana - tags in text, inflectable word /1",
        word="火照[ほて]る",
        text=(
            "<k> 然[しか]し</k>... 今日[きょう]はマジで 暑[あつ]いな。 何[なに]か... 凄[すご]い..."
            " 身体[からだ]が 火照[ほて]る"
        ),
        expected=(
            "<k> 然[しか]し</k>... 今日[きょう]はマジで 暑[あつ]いな。 何[なに]か... 凄[すご]い..."
            " 身体[からだ]が<b> 火照[ほて]る</b>"
        ),
    )
    test(
        test_name="Furigana - tags in text, inflectable word /2",
        word="褒[ほ]める",
        text=(
            "《 咄嗟[とっさ]の 障壁[しょうへき]<k> 巧[うま]い</k>ね》<br><div>《<k> 御[お]</k>"
            " 褒[ほ]めの<k> 御[お]</k> 言葉[ことば]<k> 有難[ありがと]う</k><k>"
            " 御座[ござ]います</k>》</div>"
        ),
        expected=(
            "《 咄嗟[とっさ]の 障壁[しょうへき]<k> 巧[うま]い</k>ね》<br><div>《<k> 御[お]</k><b>"
            " 褒[ほ]め</b>の<k> 御[お]</k> 言葉[ことば]<k> 有難[ありがと]う</k><k>"
            " 御座[ござ]います</k>》</div>"
        ),
    )
    test(
        test_name="Furigana - tags in text, inflected verb /3",
        word="護[まも]る",
        text=(
            "<k> 其々[それぞれ]</k>の 戦[たたか]い 方[かた]で<k> 此[こ]れ</k>からも 共[とも]に"
            " 人々[ひとびと]を 護[まも]りましょう"
        ),
        expected=(
            "<k> 其々[それぞれ]</k>の 戦[たたか]い 方[かた]で<k> 此[こ]れ</k>からも 共[とも]に"
            " 人々[ひとびと]を<b> 護[まも]りましょう</b>"
        ),
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
    test(
        test_name="No furigana with kanji - word is split by html tags in text /1",
        word="何でも無い",
        text=(
            "<div>「<k>糞</k><k>程</k><k>詰らん</k>。<k>何</k>でも<k>無い</k>女の会話。"
            "」</div><div>「<k>其れ</k>、特大ブーメランじゃねぇ？」</div>"
        ),
        expected=(
            "<div>「<k>糞</k><k>程</k><k>詰らん</k>。<b><k>何</k>でも<k>無い</k></b>女の会話。"
            "」</div><div>「<k>其れ</k>、特大ブーメランじゃねぇ？」</div>"
        ),
    )
    test(
        test_name="No furigana with kanji - word is split by html tags in text /2",
        word="花一匁",
        text="<k>此れ</k>ってなんか花<k>一匁</k>だっけ？<k>彼</k><k>位</k>の<k>乗</k>？",
        expected="<k>此れ</k>ってなんか<b>花<k>一匁</k></b>だっけ？<k>彼</k><k>位</k>の<k>乗</k>？",
    )
    test(
        test_name="No furigana with kanji - word with repeater and okuri",
        word="嬉々として",
        text=(
            "通常で<k>有れば</k>忌み嫌われる<k>筈</k>の<k>"
            "此れ</k>ら<k>糞</k>ゲーを嬉々として求める者<k>"
            "達</k>"
        ),
        expected=(
            "通常で<k>有れば</k>忌み嫌われる<k>筈</k>の<k>"
            "此れ</k>ら<k>糞</k>ゲーを<b>嬉々として</b>求める者<k>"
            "達</k>"
        ),
    )
    test(
        test_name="No furigana with kanji - tags in text, inflectable word /1",
        word="火照る",
        text="<k>然し</k>...今日はマジで暑いな。何か...凄い...身体が火照る",
        expected="<k>然し</k>...今日はマジで暑いな。何か...凄い...身体が<b>火照る</b>",
    )
    test(
        test_name="No furigana with kanji - tags in text, inflectable word /2",
        word="褒める",
        text=(
            "《咄嗟の障壁<k>巧い</k>ね》<br><div>《<k>御</k>褒めの<k>御</k>言葉<k>有難う</k>"
            "<k>御座います</k>》</div>"
        ),
        expected=(
            "《咄嗟の障壁<k>巧い</k>ね》<br><div>《<k>御</k><b>褒め</b>の<k>御</k>言葉"
            "<k>有難う</k><k>御座います</k>》</div>"
        ),
    )
    test(
        test_name="No furigana with kanji - tags in text, inflected verb /3",
        word="護る",
        text="<k>其々</k>の戦い方で<k>此れ</k>からも共に人々を護りましょう",
        expected="<k>其々</k>の戦い方で<k>此れ</k>からも共に人々を<b>護りましょう</b>",
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
        test_name="Kana only - tags in text, inflectable word /1",
        word="めげる",
        text=(
            "<div>「でも 魔王[まおう] 城[じょう]の 辺[あた]りって<k> 滅茶苦茶[めちゃくちゃ]</k>"
            " 寒[さむ]いんだよね。 行[い]きたくないなぁ…。"
            "」</div>「もうめげ始[はじ]めている…」<br>"
        ),
        expected=(
            "<div>「でも 魔王[まおう] 城[じょう]の 辺[あた]りって<k> 滅茶苦茶[めちゃくちゃ]</k>"
            " 寒[さむ]いんだよね。 行[い]きたくないなぁ…。"
            "」</div>「もう<b>めげ</b>始[はじ]めている…」<br>"
        ),
    )
    test(
        test_name="Kana only - tags in text, inflectable word /2",
        word="ほめる",
        text=(
            "《 咄嗟[とっさ]の 障壁[しょうへき]<k> 巧[うま]い</k>ね》<br><div>《おほめの<k>"
            " 御[お]</k> 言葉[ことば]<k> 有難[ありがと]う</k><k> 御座[ござ]います</k>》</div>"
        ),
        expected=(
            "《 咄嗟[とっさ]の 障壁[しょうへき]<k> 巧[うま]い</k>ね》<br><div>《お<b>ほめ</b>の<k>"
            " 御[お]</k> 言葉[ことば]<k> 有難[ありがと]う</k><k> 御座[ござ]います</k>》</div>"
        ),
    )
    test(
        test_name="Kana only - tags in text, inflectable word /3",
        word="まもる",
        text=(
            "<k> 其々[それぞれ]</k>の 戦[たたか]い 方[かた]で<k> 此[こ]れ</k>からも 共[とも]に"
            " 人々[ひとびと]をまもりましょう"
        ),
        expected=(
            "<k> 其々[それぞれ]</k>の 戦[たたか]い 方[かた]で<k> 此[こ]れ</k>からも 共[とも]に"
            " 人々[ひとびと]を<b>まもりましょう</b>"
        ),
    )
    test(
        test_name="Shouldn't crash with mixture of furigana and non-furigana in word",
        word="総[そう]勃ち",
        text="こんな 見[み]たら 観客[かんきゃく] 座[すわ]ってるのに 総[そう]勃ち だよ",
        # Might not always highlight correctly, though this one does, but at least shouldn't crash
        expected="こんな 見[み]たら 観客[かんきゃく] 座[すわ]ってるのに<b> 総[そう]勃ち</b> だよ",
    )
    print("\n\033[92mTests passed\033[0m")


if __name__ == "__main__":
    main()
