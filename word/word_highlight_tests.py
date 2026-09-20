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
]


@pytest.mark.parametrize("text, word, expected", CASES)
def test_word_highlight(text: str, word: str, expected: str):
    assert word_highlight(text, word) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
