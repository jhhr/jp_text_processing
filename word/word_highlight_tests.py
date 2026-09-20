"""Cases for `word_highlight`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/word/word_highlight_tests.py

Pass `--log-cli-level=debug` to see what a case logged; pytest captures the package logger on
its own, so nothing here has to turn logging on.

A case that is known to fail gets `marks=pytest.mark.xfail(reason="...", strict=True)` in its
`pytest.param`: strict so an unexpected pass fails the run and the reason gets dropped.
"""

import pytest

from .word_highlight import word_highlight

CASES = [
    pytest.param(
        "",
        "何[なに]",
        "",
        id="Crash test - empty text",
    ),
    pytest.param(
        None,
        "何[なに]",
        None,
        id="Crash test - None text",
    ),
    pytest.param(
        "何[なに]を しています か？",
        "",
        "何[なに]を しています か？",
        id="Crash test - empty word",
    ),
    pytest.param(
        "何[なに]を しています か？",
        None,
        "何[なに]を しています か？",
        id="Crash test - None word",
    ),
    pytest.param(
        "何[なに]を しています か？",
        "   ",
        "何[なに]を しています か？",
        id="Crash test - word is just whitespace",
    ),
    pytest.param(
        "これは犬です",
        "ね",
        "これは犬です",
        id="Crash test - one-kana word not in the text",
    ),
    pytest.param(
        "食べた",
        "る",
        "食べた",
        id="Crash test - one-kana word not in the text /2",
    ),
    pytest.param(
        "私[わたし]は 日本語[にほんご]を 勉強[べんきょう]しています。",
        "日本語[にほんご]",
        "私[わたし]は<b> 日本語[にほんご]</b>を 勉強[べんきょう]しています。",
        id="Furigana - non-inflected noun in middle of text",
    ),
    pytest.param(
        "家[いえ]で 居[い]る",
        "家[いえ]",
        "<b>家[いえ]</b>で 居[い]る",
        id="Furigana - non-inflected single-kanji noun",
    ),
    pytest.param(
        "この 魚[さかな]は 魚市場[うおいちば]で 買[か]った",
        "魚市場[うおいちば]",
        "この 魚[さかな]は<b> 魚市場[うおいちば]</b>で 買[か]った",
        id="Furigana - non-inflected multi-kanji noun",
    ),
    pytest.param(
        "彼[かれ]は 人々[ひとびと]の 中で 目立[めだ]つ",
        # Also missing furigana for one word to test that it still works
        "人々[ひとびと]",
        "彼[かれ]は<b> 人々[ひとびと]</b>の 中で 目立[めだ]つ",
        id="Furigana - non-inflected repeater noun",
    ),
    pytest.param(
        "<k> 此[こ]の</k> 魚[さかな]は 魚[うお]市場[いちば]で 買[か]いました。",
        "魚市場[うおいちば]",
        # Will change the original text structure slightly by merging the furigana parts
        "<k> 此[こ]の</k> 魚[さかな]は<b> 魚市場[うおいちば]</b>で 買[か]いました。",
        id="Furigana - non-inflected multi-kanji noun where word is split in text",
    ),
    pytest.param(
        "この 魚[さかな]は 魚市場[うおいちば]で 買[か]った",
        "魚[うお]",
        "この 魚[さかな]は<b> 魚[うお]</b> 市場[いちば]で 買[か]った",
        id="Furigana - non-inflected single-kanji noun as part of larger word in text, left side",
    ),
    pytest.param(
        "労働時間[ろうどうじかん]を 減[へ]らしたい",
        "時間[じかん]",
        "労働[ろうどう]<b> 時間[じかん]</b>を 減[へ]らしたい",
        id="Furigana - non-inflected multi-kanji noun as part of larger word in text, right side",
    ),
    pytest.param(
        "バイクを 自転車専用道路[じてんしゃせんようどうろ]で 走[はし]らせる",
        "専用[せんよう]",
        "バイクを 自転車[じてんしゃ]<b> 専用[せんよう]</b> 道路[どうろ]で 走[はし]らせる",
        id="Furigana - non-inflected multi-kanji noun as part of larger word in text, middle",
    ),
    pytest.param(
        "彼女[かのじょ]への 伝言[でんごん]を 言付[ことづ]けたの。",
        "付[つ]ける",
        "彼女[かのじょ]への 伝言[でんごん]を 言[こと]<b> 付[づ]けた</b>の。",
        id="Furigana - inflected verb as part of larger verb in text",
    ),
    pytest.param(
        "<k> 此[こ]の</k> 漢字[かんじ]を 字引[じびき]で 引[ひ]いてみて。",
        "引[ひ]く",
        "<k> 此[こ]の</k> 漢字[かんじ]を 字[じ]<b> 引[びき]</b>で<b> 引[ひ]いて</b>みて。",
        id="Furigana - inflected verb occurring in noun form and verb form in text",
    ),
    pytest.param(
        "私は 食[た]べている",
        "食[た]べる",
        "私は<b> 食[た]べている</b>",
        id="Furigana - verb inflection ている /1",
    ),
    pytest.param(
        "食[た]べさせるな!",
        "食[た]べる",
        "<b>食[た]べさせる</b>な!",
        id="Furigana - verb inflection させる /1",
    ),
    pytest.param(
        "聴牌[テンパ]ってた",
        "聴牌[テンパ]る",
        "<b>聴牌[テンパ]ってた</b>",
        id="Furigana - verb inflection juku word /1",
    ),
    pytest.param(
        "これ、 大[おお]きすぎない？",
        "大[おお]きい",
        "これ、<b> 大[おお]き</b>すぎない？",
        id="Furigana - adjective inflection /1",
    ),
    pytest.param(
        "安[やす]くて 良[い]いな～",
        "安[やす]い",
        "<b>安[やす]くて</b> 良[い]いな～",
        id="Furigana - adjective inflection /2",
    ),
    pytest.param(
        "高[たか]いでも 良[よ]かろう",
        "良[よ]い",
        "高[たか]いでも<b> 良[よ]かろう</b>",
        id="Furigana - adjective inflection /3",
    ),
    pytest.param(
        "早読[はやよ]みするぜ",
        "早[はや]い",
        "<b>早[はや]</b> 読[よ]みするぜ",
        id="Furigana - adjective inflection with な /1",
    ),
    pytest.param(
        "垂[タ]レ 込[コ]ミがあった、オイ！",
        "垂[た]れ 込[こ]み",
        "<b>垂[タ]レ 込[コ]ミ</b>があった、オイ！",
        id="Furigana is in katakana in text, word in hiragana",
    ),
    pytest.param(
        "垂[た]れ 込[こ]みがあった",
        "垂[タ]レ 込[コ]ミ",
        "<b>垂[た]れ 込[こ]み</b>があった",
        id="Furigana is in hiragana in text, word in katakana",
    ),
    pytest.param(
        "彼女[かのじょ]の 髪[かみ]の 毛[け]は 長[なが]い",
        "髪[かみ]の 毛[け]",
        "彼女[かのじょ]の<b> 髪[かみ]の 毛[け]</b>は 長[なが]い",
        id="Furigana - multi-kanji noun with okuri in middle /1",
    ),
    pytest.param(
        "彼[かれ]は 飲[の]ん 兵衛[べえ]だ",
        "飲[の]ん 兵衛[べえ]",
        "彼[かれ]は<b> 飲[の]ん 兵衛[べえ]</b>だ",
        id="Furigana - multi-kanji noun with okuri in middle /2",
    ),
    pytest.param(
        "彼[かれ]は 走[はし]った。彼[かれ]は 速[はや]い。",
        "彼[かれ]",
        "<b>彼[かれ]</b>は 走[はし]った。<b> 彼[かれ]</b>は 速[はや]い。",
        id="Furigana - word occurs more than once, simple match",
    ),
    pytest.param(
        "彼[かれ]は 走[はし]った。 彼[かれ]の 走[はし]り 方[かた]は 速[はや]い。",
        "走[はし]る",
        "彼[かれ]は<b> 走[はし]った</b>。 彼[かれ]の<b> 走[はし]り</b> 方[かた]は 速[はや]い。",
        id="Furigana - word occurs more than once, inflected match",
    ),
    pytest.param(
        (
            "<div>「<k> 糞[クソ]</k><k> 程[ほど]</k><k> 詰[つま]らん</k>。<k> 何[なん]</k>でも<k>"
            " 無[な]い</k> 女[おんな]の 会話[かいわ]。」</div><div>「<k> 其[そ]れ</k>、"
            " 特大[とくだい]ブーメランじゃねぇ？」</div>"
        ),
        "何[なん]でも 無[な]い",
        (
            "<div>「<k> 糞[クソ]</k><k> 程[ほど]</k><k> 詰[つま]らん</k>。<b><k> 何[なん]</k>"
            "でも<k> 無[な]い</k></b> 女[おんな]の 会話[かいわ]。」</div><div>「<k> 其[そ]れ</k>、"
            " 特大[とくだい]ブーメランじゃねぇ？」</div>"
        ),
        id="Furigana - word is split by html tags in text /1",
    ),
    pytest.param(
        (
            "<k> 此[こ]れ</k>ってなんか 花[はな]<k> 一匁[いちもんめ]</k>だっけ？<k>"
            " 彼[あれ]</k><k> 位[ぐらい]</k>の<k> 乗[ノリ]</k>？"
        ),
        "花一匁[はないちもんめ]",
        (
            "<k> 此[こ]れ</k>ってなんか<b> 花[はな]<k> 一匁[いちもんめ]</k></b>だっけ？<k>"
            " 彼[あれ]</k><k> 位[ぐらい]</k>の<k> 乗[ノリ]</k>？"
        ),
        id="Furigana - word is split by html tags in text /2",
    ),
    pytest.param(
        (
            "通常[つうじょう]で<k> 有[あ]れば</k> 忌[い]み 嫌[きら]われる<k> 筈[はず]</k>の<k>"
            " 此[こ]れ</k>ら<k> 糞[クソ]</k>ゲーを 嬉々[きき]として 求[もと]める 者[もの]<k>"
            " 達[たち]</k>"
        ),
        "嬉々[きき]として",
        (
            "通常[つうじょう]で<k> 有[あ]れば</k> 忌[い]み 嫌[きら]われる<k> 筈[はず]</k>の<k>"
            " 此[こ]れ</k>ら<k> 糞[クソ]</k>ゲーを<b> 嬉々[きき]として</b> 求[もと]める 者[もの]<k>"
            " 達[たち]</k>"
        ),
        id="Furigana - word with repeater and okuri",
    ),
    pytest.param(
        (
            "<k> 然[しか]し</k>... 今日[きょう]はマジで 暑[あつ]いな。 何[なに]か... 凄[すご]い..."
            " 身体[からだ]が 火照[ほて]る"
        ),
        "火照[ほて]る",
        (
            "<k> 然[しか]し</k>... 今日[きょう]はマジで 暑[あつ]いな。 何[なに]か... 凄[すご]い..."
            " 身体[からだ]が<b> 火照[ほて]る</b>"
        ),
        id="Furigana - tags in text, inflectable word /1",
    ),
    pytest.param(
        (
            "《 咄嗟[とっさ]の 障壁[しょうへき]<k> 巧[うま]い</k>ね》<br><div>《<k> 御[お]</k>"
            " 褒[ほ]めの<k> 御[お]</k> 言葉[ことば]<k> 有難[ありがと]う</k><k>"
            " 御座[ござ]います</k>》</div>"
        ),
        "褒[ほ]める",
        (
            "《 咄嗟[とっさ]の 障壁[しょうへき]<k> 巧[うま]い</k>ね》<br><div>《<k> 御[お]</k><b>"
            " 褒[ほ]め</b>の<k> 御[お]</k> 言葉[ことば]<k> 有難[ありがと]う</k><k>"
            " 御座[ござ]います</k>》</div>"
        ),
        id="Furigana - tags in text, inflectable word /2",
    ),
    pytest.param(
        (
            "<k> 其々[それぞれ]</k>の 戦[たたか]い 方[かた]で<k> 此[こ]れ</k>からも 共[とも]に"
            " 人々[ひとびと]を 護[まも]りましょう"
        ),
        "護[まも]る",
        (
            "<k> 其々[それぞれ]</k>の 戦[たたか]い 方[かた]で<k> 此[こ]れ</k>からも 共[とも]に"
            " 人々[ひとびと]を<b> 護[まも]りましょう</b>"
        ),
        id="Furigana - tags in text, inflected verb /3",
    ),
    pytest.param(
        (
            "<k> 止[や]めた</k> 方[ほう]が<k> 良[い]い</k>、 貴方[あなた]の 持[も]っている"
            " 十徳[じゅっとく]ナイフじゃ 私[わたし]には 勝[か]てない"
        ),
        "十徳[じゅっとく]ナイフ",
        (
            "<k> 止[や]めた</k> 方[ほう]が<k> 良[い]い</k>、 貴方[あなた]の 持[も]っている"
            "<b> 十徳[じゅっとく]ナイフ</b>じゃ 私[わたし]には 勝[か]てない"
        ),
        id="Furigana - combination of furigana word and katakana word",
    ),
    pytest.param(
        "塑像[そぞう]を 彫[ほ]りナイフで 彫[ほ]るのは 安[やす]いね。",
        "彫[ほ]りナイフ",
        "塑像[そぞう]を<b> 彫[ほ]りナイフ</b>で 彫[ほ]るのは 安[やす]いね。",
        id="Furigana - combination of furigana word with okurigana and katakana word",
    ),
    pytest.param(
        "及[およ]び 腰[ごし]",
        "腰[こし]",
        "及[およ]び <b>腰[ごし]</b>",
        id="Furigana - noun in rendaku form in text",
    ),
    pytest.param(
        "手紙[てがみ]を 書[か]いた",
        "手紙[てかみ]",
        "<b>手紙[てがみ]</b>を 書[か]いた",
        id="Furigana - multi-kanji noun with rendaku reading change",
    ),
    pytest.param(
        "及[およ]び 腰[ごし]",
        "及[およ]ぶ",
        "<b>及[およ]び</b> 腰[ごし]",
        id="Furigana - verb in noun form in text",
    ),
    pytest.param(
        "無[ねえ]な",
        # Needs some kind of exception handling, can only work when furigana are used
        "無[ない]",
        "<b>無[ねえ]な</b>",
        marks=pytest.mark.xfail(
            reason=(
                "無[ない] vs 無[ねえ] is a colloquial reading; matching it needs"
                " furigana-aware exception handling"
            ),
            strict=True,
        ),
        id="Furigana is colloquial /1",
    ),
    pytest.param(
        "幡ヶ谷[はたがや]で 待[ま]ち 合[あ]わせ",
        "幡ヶ谷[はたがや]",
        "<b>幡ヶ谷[はたがや]</b>で 待[ま]ち 合[あ]わせ",
        id="Furigana word containing ヶ in middle 1/",
    ),
    pytest.param(
        "一ヶ月[いっかげつ]で 仕上[しあ]げる",
        "一ヶ月[いっかげつ]",
        "<b>一ヶ月[いっかげつ]</b>で 仕上[しあ]げる",
        id="Furigana word containing ヶ in middle 2/",
    ),
    pytest.param(
        "一ヶ月[いっかげつ]で 仕上[しあ]げる",
        "ヶ月[かげつ]",
        "一[いっ]<b> ヶ月[かげつ]</b>で 仕上[しあ]げる",
        id="Furigana word containing ヶ in start 1/",
    ),
    pytest.param(
        "一ヵ月[いっかげつ]で 仕上[しあ]げる",
        "一ヵ月[いっかげつ]",
        "<b>一ヵ月[いっかげつ]</b>で 仕上[しあ]げる",
        id="Furigana word containing ヵ in middle 1/",
    ),
    pytest.param(
        "一ヵ月[いっかげつ]で 仕上[しあ]げる",
        "ヵ月[かげつ]",
        "一[いっ]<b> ヵ月[かげつ]</b>で 仕上[しあ]げる",
        id="Furigana word containing ヵ in start 1/",
    ),
    pytest.param(
        "私[わたし]への 報[ほう]・ 連[れん]・ 相[そう]を 行[おこな]っていただきます",
        "報連相[ほうれんそう]",
        "私[わたし]への<b> 報[ほう]・ 連[れん]・ 相[そう]</b>を 行[おこな]っていただきます",
        id="Furigana word split by ・ in text",
    ),
    pytest.param(
        "家で居る、家出はしない",
        "家",
        "<b>家</b>で居る、<b>家</b>出はしない",
        id="No furigana with kanji - single-kanji noun multiple occurrences",
    ),
    pytest.param(
        "この魚は魚市場で買った",
        "魚市場",
        "この魚は<b>魚市場</b>で買った",
        id="No furigana with kanji - multi-kanji noun",
    ),
    pytest.param(
        "彼女の髪の毛は長い",
        "髪の毛",
        "彼女の<b>髪の毛</b>は長い",
        id="No furigana with kanji - multi-kanji noun with okuri in middle /1",
    ),
    pytest.param(
        "彼は飲ん兵衛だ",
        "飲ん兵衛",
        "彼は<b>飲ん兵衛</b>だ",
        id="No furigana with kanji - multi-kanji noun with okuri in middle /2",
    ),
    pytest.param(
        "彼は食べている",
        "食べる",
        "彼は<b>食べている</b>",
        id="No furigana with kanji - verb inflection /1",
    ),
    pytest.param(
        "苛めなくていれないのか、お 前は？",
        "苛めめる",
        "<b>苛めなくて</b>いれないのか、お 前は？",
        id="No furigana with kanji - verb inflection /2",
    ),
    pytest.param(
        "<k>此の</k>漢字を字引で引いてみて。",
        "引く",
        "<k>此の</k>漢字を字<b>引</b>で<b>引いて</b>みて。",
        id="No furigana with kanji - inflected verb occurring in noun form and verb form in text",
    ),
    pytest.param(
        "このケーキ、美味しくない？",
        "美味しい",
        "このケーキ、<b>美味しくない</b>？",
        id="No furigana with kanji - adjective inflection /1",
    ),
    pytest.param(
        "このケーキって、美味しくなくて 残念だったな！",
        "美味しい",
        "このケーキって、<b>美味しくなくて</b> 残念だったな！",
        id="No furigana with kanji - adjective inflection /2",
    ),
    pytest.param(
        (
            "<div>「<k>糞</k><k>程</k><k>詰らん</k>。<k>何</k>でも<k>無い</k>女の会話。"
            "」</div><div>「<k>其れ</k>、特大ブーメランじゃねぇ？」</div>"
        ),
        "何でも無い",
        (
            "<div>「<k>糞</k><k>程</k><k>詰らん</k>。<b><k>何</k>でも<k>無い</k></b>女の会話。"
            "」</div><div>「<k>其れ</k>、特大ブーメランじゃねぇ？」</div>"
        ),
        id="No furigana with kanji - word is split by html tags in text /1",
    ),
    pytest.param(
        "<k>此れ</k>ってなんか花<k>一匁</k>だっけ？<k>彼</k><k>位</k>の<k>乗</k>？",
        "花一匁",
        "<k>此れ</k>ってなんか<b>花<k>一匁</k></b>だっけ？<k>彼</k><k>位</k>の<k>乗</k>？",
        id="No furigana with kanji - word is split by html tags in text /2",
    ),
    pytest.param(
        (
            "通常で<k>有れば</k>忌み嫌われる<k>筈</k>の<k>"
            "此れ</k>ら<k>糞</k>ゲーを嬉々として求める者<k>"
            "達</k>"
        ),
        "嬉々として",
        (
            "通常で<k>有れば</k>忌み嫌われる<k>筈</k>の<k>"
            "此れ</k>ら<k>糞</k>ゲーを<b>嬉々として</b>求める者<k>"
            "達</k>"
        ),
        id="No furigana with kanji - word with repeater and okuri",
    ),
    pytest.param(
        "<k>然し</k>...今日はマジで暑いな。何か...凄い...身体が火照る",
        "火照る",
        "<k>然し</k>...今日はマジで暑いな。何か...凄い...身体が<b>火照る</b>",
        id="No furigana with kanji - tags in text, inflectable word /1",
    ),
    pytest.param(
        (
            "《咄嗟の障壁<k>巧い</k>ね》<br><div>《<k>御</k>褒めの<k>御</k>言葉<k>有難う</k>"
            "<k>御座います</k>》</div>"
        ),
        "褒める",
        (
            "《咄嗟の障壁<k>巧い</k>ね》<br><div>《<k>御</k><b>褒め</b>の<k>御</k>言葉"
            "<k>有難う</k><k>御座います</k>》</div>"
        ),
        id="No furigana with kanji - tags in text, inflectable word /2",
    ),
    pytest.param(
        "及び腰",
        "及ぶ",
        "<b>及び</b>腰",
        id="No furigana with kanji - verb in noun form in text",
    ),
    pytest.param(
        "<k>其々</k>の戦い方で<k>此れ</k>からも共に人々を護りましょう",
        "護る",
        "<k>其々</k>の戦い方で<k>此れ</k>からも共に人々を<b>護りましょう</b>",
        id="No furigana with kanji - tags in text, inflected verb /3",
    ),
    pytest.param(
        "幡ヶ谷で待ち合わせ",
        "幡ヶ谷",
        "<b>幡ヶ谷</b>で待ち合わせ",
        id="No furigana with kanji - word containing ヶ 1/",
    ),
    pytest.param(
        "一ヶ月で仕上げる",
        "一ヶ月",
        "<b>一ヶ月</b>で仕上げる",
        id="No furigana with kanji - word containing ヶ 2/",
    ),
    pytest.param(
        "一ヵ月で仕上げる",
        "一ヵ月",
        "<b>一ヵ月</b>で仕上げる",
        id="No furigana with kanji - word containing ヵ 1/",
    ),
    pytest.param(
        "私への 報・ 連・ 相を 行っていただきます",
        "報連相",
        "私への<b> 報・ 連・ 相</b>を 行っていただきます",
        id="No furigana with kanji - word split by ・ in text",
    ),
    # Mixing in katakana with the kana-only tests below to ensure conversion back to hiragana works
    pytest.param(
        "タレコミがあった",
        "たれこみ",
        "<b>タレコミ</b>があった",
        id="Kana only - katakana word in text, word in hiragana",
    ),
    pytest.param(
        "たれこみがあった",
        "タレコミ",
        "<b>たれこみ</b>があった",
        id="Kana only - hiragana word in text, word in katakana",
    ),
    pytest.param(
        (
            "<k>此[こん]な</k> 見[み]たら 観客[かんきゃく] 座[すわ]ってるのに 総[そう]"
            " 勃[た]ちでスタンティングオペレーションじゃなくてマスターページョン始[はじ]まっちゃうね。"
        ),
        "マスターページョン",
        (
            "<k>此[こん]な</k> 見[み]たら 観客[かんきゃく] 座[すわ]ってるのに 総[そう]"
            " 勃[た]ちでスタンティングオペレーションじゃなくて<b>マスターページョン</b>始[はじ]"
            "まっちゃうね。"
        ),
        id="Kana only - katakana in word and text",
    ),
    pytest.param(
        "いじめなくていれないのか、お 前[オマエ]は？",
        "いじめる",
        "<b>いじめなくて</b>いれないのか、お 前[オマエ]は？",
        id="Kana only - verb inflection /2",
    ),
    pytest.param(
        "このケーキ、おいしくない？",
        "おいしい",
        "このケーキ、<b>おいしくない</b>？",
        id="Kana only - adjective inflection /1",
    ),
    pytest.param(
        "このケーキって、おいしくなくて 残念[ザンねん]だったな！",
        "おいしい",
        "このケーキって、<b>おいしくなくて</b> 残念[ザンねん]だったな！",
        id="Kana only - adjective inflection /2",
    ),
    pytest.param(
        (
            "<div>「でも魔王城の辺りって<k>滅茶苦茶</k>"
            "寒いんだよね。行きたくないなぁ…。"
            "」</div>「もうめげ始めている…」<br>"
        ),
        "めげる",
        (
            "<div>「でも魔王城の辺りって<k>滅茶苦茶</k>"
            "寒いんだよね。行きたくないなぁ…。"
            "」</div>「もう<b>めげ</b>始めている…」<br>"
        ),
        id="Kana only - kanji only & tags in text, inflectable word /1",
    ),
    pytest.param(
        (
            "《咄嗟の障壁<k>巧い</k>ね》<br><div>《おほめの<k>"
            "御</k>言葉<k>有難う</k><k>御座います</k>》</div>"
        ),
        "ほめる",
        (
            "《咄嗟の障壁<k>巧い</k>ね》<br><div>《お<b>ほめ</b>の<k>"
            "御</k>言葉<k>有難う</k><k>御座います</k>》</div>"
        ),
        id="Kana only - kanji only & tags in text, inflectable word /2",
    ),
    pytest.param(
        "<k>其々</k>の戦い方で<k>此れ</k>からも共に人々をまもりましょう",
        "まもる",
        "<k>其々</k>の戦い方で<k>此れ</k>からも共に人々を<b>まもりましょう</b>",
        id="Kana only - kanji only & tags in text, inflectable word /3",
    ),
    pytest.param(
        "「<k>彼の</k>はにかんだ笑顔が<k>如何</k>にも頭に残る」",
        "はにかむ",
        "「<k>彼の</k><b>はにかんだ</b>笑顔が<k>如何</k>にも頭に残る」",
        id="Kana only - kanji only & tags in text, inflectable word /4",
    ),
    pytest.param(
        "はしをわたる",
        "はしる",
        "はしをわたる",
        id="Kana only - noun spelling the word's stem is not the word",
    ),
    pytest.param(
        "あめがふる",
        "あめる",
        "あめがふる",
        id="Kana only - noun spelling the word's stem is not the word /2",
    ),
    pytest.param(
        "はしらないで歩く",
        "はしる",
        "<b>はしらないで</b>歩く",
        id="Kana only - the word itself still highlights when MeCab knows it",
    ),
    # Two occurrences with nothing between them: the token that ends the first highlight is
    # the one that begins the second, so it gets looked at as a beginning too.
    pytest.param(
        "はしってはしって",
        "はしる",
        "<b>はしって</b><b>はしって</b>",
        id="Kana only - two adjacent occurrences both highlight",
    ),
    pytest.param(
        "たべたたべた",
        "たべる",
        "<b>たべた</b><b>たべた</b>",
        id="Kana only - two adjacent occurrences both highlight /2",
    ),
    pytest.param(
        "はしって はしって",
        "はしる",
        "<b>はしって</b> <b>はしって</b>",
        id="Kana only - two occurrences separated by only a space both highlight",
    ),
    pytest.param(
        "それはバズったね",
        "バズる",
        "それは<b>バズった</b>ね",
        id="Kana only - stem MeCab parsed as a noun highlights when a conjugation follows",
    ),
    pytest.param(
        "それはバズらないね",
        "バズる",
        "それは<b>バズらない</b>ね",
        id="Kana only - stem parsed as a noun, conjugation spanning several tokens",
    ),
    pytest.param(
        "それはバズってるね",
        "バズる",
        "それは<b>バズって</b>るね",
        id="Kana only - stem parsed as a noun, conjugation ending inside a token",
    ),
    pytest.param(
        "それはバズった",
        "バズる",
        "それは<b>バズった</b>",
        id="Kana only - stem parsed as a noun, conjugation at the end of the text",
    ),
    pytest.param(
        "それはバズられたね",
        "バズる",
        "それは<b>バズられた</b>ね",
        id="Kana only - stem parsed as a noun, passive read as a verb of its own",
    ),
    pytest.param(
        "それはバズらせたね",
        "バズる",
        "それは<b>バズらせた</b>ね",
        id="Kana only - stem parsed as a noun, causative in the past",
    ),
    pytest.param(
        "それはバズらせないね",
        "バズる",
        "それは<b>バズらせない</b>ね",
        id="Kana only - stem parsed as a noun, causative negative",
    ),
    pytest.param(
        "それはバズらせられたね",
        "バズる",
        "それは<b>バズらせられた</b>ね",
        id="Kana only - stem parsed as a noun, causative passive in the past",
    ),
    pytest.param(
        "それはバズったね",
        "バズり",
        "それは<b>バズった</b>ね",
        id="Kana only - stem parsed as a noun, word given in noun form",
    ),
    pytest.param(
        "それはバズがすごいね",
        "バズる",
        "それはバズがすごいね",
        id="Kana only - a particle after the stem is not a conjugation",
    ),
    pytest.param(
        "それはバズらしいね",
        "バズる",
        "それはバズらしいね",
        id="Kana only - a non-verb auxiliary after the stem is not a conjugation",
    ),
    pytest.param(
        "きのうサボった",
        "サボる",
        "きのう<b>サボった</b>",
        id="Kana only - katakana-stem verb MeCab knows",
    ),
    pytest.param(
        "かれはサボっているよ",
        "サボる",
        "かれは<b>サボっている</b>よ",
        id="Kana only - katakana-stem verb MeCab knows, conjugation spanning several tokens",
    ),
    pytest.param(
        "サボらないでよ",
        "サボる",
        "<b>サボらないで</b>よ",
        id="Kana only - katakana-stem verb MeCab knows, negative form",
    ),
    pytest.param(
        "はしがある",
        "はしる",
        "はしがある",
        id="Kana only - noun spelling the word's stem is not the word /3",
    ),
    # A reading inside [...] is not the word occurring in the text, so neither the plain
    # search nor the mecab one may highlight inside a bracket.
    pytest.param(
        "この 家[いえ]は",
        "いえ",
        "この 家[いえ]は",
        id="Kana only - a kana word is not the reading in a bracket",
    ),
    pytest.param(
        "この 家[いえ]は いえ",
        "いえ",
        "この 家[いえ]は<b> いえ</b>",
        id="Kana only - a kana word in the text highlights, the same reading does not",
    ),
    pytest.param(
        "この 家[いえ]は いえた",
        "いえる",
        "この 家[いえ]は <b>いえた</b>",
        id="Kana only - an inflected kana word highlights, the same reading does not",
    ),
    pytest.param(
        (
            "<div>「でも 魔王[まおう] 城[じょう]の 辺[あた]りって<k> 滅茶苦茶[めちゃくちゃ]</k>"
            " 寒[さむ]いんだよね。 行[い]きたくないなぁ…。"
            "」</div>「もうめげ始[はじ]めている…」<br>"
        ),
        "めげる",
        (
            "<div>「でも 魔王[まおう] 城[じょう]の 辺[あた]りって<k> 滅茶苦茶[めちゃくちゃ]</k>"
            " 寒[さむ]いんだよね。 行[い]きたくないなぁ…。"
            "」</div>「もう<b>めげ</b>始[はじ]めている…」<br>"
        ),
        id="Kana only - furigana & tags in text, inflectable word /1",
    ),
    pytest.param(
        (
            "《 咄嗟[とっさ]の 障壁[しょうへき]<k> 巧[うま]い</k>ね》<br><div>《おほめの<k>"
            " 御[お]</k> 言葉[ことば]<k> 有難[ありがと]う</k><k> 御座[ござ]います</k>》</div>"
        ),
        "ほめる",
        (
            "《 咄嗟[とっさ]の 障壁[しょうへき]<k> 巧[うま]い</k>ね》<br><div>《お<b>ほめ</b>の<k>"
            " 御[お]</k> 言葉[ことば]<k> 有難[ありがと]う</k><k> 御座[ござ]います</k>》</div>"
        ),
        id="Kana only - furigana & tags in text, inflectable word /2",
    ),
    pytest.param(
        (
            "<k> 其々[それぞれ]</k>の 戦[たたか]い 方[かた]で<k> 此[こ]れ</k>からも 共[とも]に"
            " 人々[ひとびと]をまもりましょう"
        ),
        "まもる",
        (
            "<k> 其々[それぞれ]</k>の 戦[たたか]い 方[かた]で<k> 此[こ]れ</k>からも 共[とも]に"
            " 人々[ひとびと]を<b>まもりましょう</b>"
        ),
        id="Kana only - furigana & tags in text, inflectable word /3",
    ),
    pytest.param(
        "「<k> 彼[あ]の</k>はにかんだ 笑顔[えがお]が<k> 如何[どう]</k>にも 頭[あたま]に 残[のこ]る」",
        "はにかむ",
        (
            "「<k> 彼[あ]の</k><b>はにかんだ</b> 笑顔[えがお]が<k> 如何[どう]</k>にも 頭[あたま]に"
            " 残[のこ]る」"
        ),
        id="Kana only - furigana & tags in text, inflectable word /4",
    ),
    pytest.param(
        "こんな 見[み]たら 観客[かんきゃく] 座[すわ]ってるのに 総[そう]勃ち だよ",
        "総[そう]勃ち",
        # Might not always highlight correctly, though this one does, but at least shouldn't crash
        "こんな 見[み]たら 観客[かんきゃく] 座[すわ]ってるのに<b> 総[そう]勃ち</b> だよ",
        id="Shouldn't crash with mixture of furigana and non-furigana in word",
    ),
    # An Anki word field often has no furigana where the sentence field does, or the other way
    # round. The highlight then covers the same occurrence as it would if both agreed, brackets
    # and all, instead of closing between a kanji and its reading.
    pytest.param(
        "私は 日本語[にほんご]を",
        "日本語",
        "私は<b> 日本語[にほんご]</b>を",
        id="Furigana mismatch - word written without the furigana the text has",
    ),
    pytest.param(
        "食[た]べた",
        "食べる",
        "<b>食[た]べた</b>",
        id="Furigana mismatch - word written without the furigana the text has, inflected",
    ),
    pytest.param(
        "食べた",
        "食[た]べる",
        "<b>食べた</b>",
        id="Furigana mismatch - text written without the furigana the word has, inflected",
    ),
    pytest.param(
        "食[た]べた",
        "食[た]べる",
        "<b>食[た]べた</b>",
        id="Furigana mismatch - neither side is missing furigana, inflected",
    ),
    pytest.param(
        "その 人[ひと]が",
        "人[じん]",
        "その 人[ひと]が",
        id="Furigana mismatch - a reading the word disagrees with is still not the word",
    ),
    # Without the word's own reading the text's reading cannot be split between the kanji it
    # covers, so a word that is only part of a kanji run takes the whole run and its bracket.
    pytest.param(
        "この 魚[さかな]は 魚市場[うおいちば]で",
        "魚",
        "この<b> 魚[さかな]</b>は<b> 魚市場[うおいちば]</b>で",
        id="Furigana mismatch - word without furigana starting a longer kanji run",
    ),
    pytest.param(
        "私は 日本語[にほんご]を",
        "語",
        "私は<b> 日本語[にほんご]</b>を",
        id="Furigana mismatch - word without furigana ending a longer kanji run",
    ),
    pytest.param(
        "私は 日本語[にほんご]を",
        "本語",
        "私は<b> 日本語[にほんご]</b>を",
        id="Furigana mismatch - word without furigana in the middle of a longer kanji run",
    ),
    pytest.param(
        "私は 日本語[にほんご]を",
        "日本",
        "私は<b> 日本語[にほんご]</b>を",
        id="Furigana mismatch - word without furigana at the start of a longer kanji run",
    ),
    pytest.param(
        "魚市場で",
        "魚",
        "<b>魚</b>市場で",
        id="Furigana mismatch - a kanji run with no reading is highlighted as far as the word",
    ),
    pytest.param(
        "この 魚[さかな]は 魚市場[うおいちば]で",
        "魚[うお]",
        "この 魚[さかな]は<b> 魚[うお]</b> 市場[いちば]で",
        id="Furigana mismatch - a word with a reading still splits the run it is part of /1",
    ),
    pytest.param(
        "私は 日本語[にほんご]を",
        "語[ご]",
        "私は 日本[にほん]<b> 語[ご]</b>を",
        id="Furigana mismatch - a word with a reading still splits the run it is part of /2",
    ),
    # The caller's own html around the word: the highlight goes inside the element when the
    # element holds the whole word, and around it when the word runs past the element's edge.
    pytest.param(
        "<span>はしって</span>",
        "はしる",
        "<span><b>はしって</b></span>",
        id="Html shape - a tag around the whole word keeps the highlight inside it",
    ),
    pytest.param(
        '<span class="x">はしって</span>',
        "はしる",
        '<span class="x"><b>はしって</b></span>',
        id="Html shape - the space in a tag's attributes is part of the tag",
    ),
    pytest.param(
        "<span>はし</span>って",
        "はしる",
        "<b><span>はし</span>って</b>",
        id="Html shape - a tag around part of the word goes inside the highlight",
    ),
    pytest.param(
        "<span>はしって</span><br>",
        "はしる",
        "<span><b>はしって</b></span><br>",
        id="Html shape - an unpaired tag after the word stays outside the highlight",
    ),
    pytest.param(
        "<k> 昨日[きのう]</k>は バズったね",
        "バズる",
        "<k> 昨日[きのう]</k>は <b>バズった</b>ね",
        id="Html shape - the space before the word stays outside the highlight",
    ),
    pytest.param(
        "<span>食[た]</span>べた",
        "食[た]べる",
        "<b><span> 食[た]</span>べた</b>",
        id="Html shape - a tag around part of a furigana word",
    ),
    pytest.param(
        "<span>食[た]べた</span><br>",
        "食[た]べる",
        "<span><b> 食[た]べた</b></span><br>",
        id="Html shape - a furigana word in a tag with an unpaired tag after it",
    ),
    pytest.param(
        "<span>家で居る、家出はしない</span>",
        "家",
        "<span><b>家</b>で居る、<b>家</b>出はしない</span>",
        id="Html shape - several occurrences inside one tag",
    ),
    pytest.param(
        "<span> 家[いえ]と 家[いえ]</span>",
        "家[いえ]",
        "<span><b> 家[いえ]</b>と<b> 家[いえ]</b></span>",
        id="Html shape - several furigana occurrences inside one tag",
    ),
    # A splitter dot is stored like a tag: it is out of the way while the word is matched and
    # comes back where it was, inside the highlight when the word is written across it and
    # outside when it only separates two occurrences.
    pytest.param(
        "家出・家出",
        "家出",
        "<b>家出</b>・<b>家出</b>",
        id="Splitter dot - between two occurrences, not inside either",
    ),
    pytest.param(
        " 家出[いえで]・ 家出[いえで]",
        "家出[いえで]",
        "<b> 家出[いえで]</b>・<b> 家出[いえで]</b>",
        id="Splitter dot - between two furigana occurrences",
    ),
    pytest.param(
        " 家[いえ]・ 家[いえ]",
        "家[いえ]",
        "<b> 家[いえ]</b>・<b> 家[いえ]</b>",
        id="Splitter dot - between two single-kanji furigana occurrences",
    ),
    pytest.param(
        "<span> 家[いえ]・ 家[いえ]</span>",
        "家[いえ]",
        "<span><b> 家[いえ]</b>・<b> 家[いえ]</b></span>",
        id="Splitter dot - between two furigana occurrences inside a tag",
    ),
    pytest.param(
        "家・出でした",
        "家出",
        "<b>家・出</b>でした",
        id="Splitter dot - inside the word, spanned by the highlight",
    ),
    pytest.param(
        "毎日 報・ 連・ 相しています",
        "報連相する",
        "毎日<b> 報・ 連・ 相しています</b>",
        id="Splitter dot - inside a word with okurigana",
    ),
    pytest.param(
        "毎日[まいにち] 報[ほう]・ 連[れん]・ 相[そう]しています",
        "報連相[ほうれんそう]する",
        "毎日[まいにち]<b> 報[ほう]・ 連[れん]・ 相[そう]しています</b>",
        id="Splitter dot - inside a furigana word with okurigana",
    ),
    pytest.param(
        "<span></span>はしって",
        "はしる",
        "<span></span><b>はしって</b>",
        id="Html shape - an empty element next to the word is the caller's and stays",
    ),
]


@pytest.mark.parametrize("text, word, expected", CASES)
def test_word_highlight(text: str, word: str, expected: str):
    assert word_highlight(text, word) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
