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
    # The な form: the adnominal 大きな has the stem of 大きい, so the stem is the word; the な
    # is not, unless the word to match was written with it.
    pytest.param(
        "大[おお]きな 家[いえ]",
        "大[おお]きい",
        "<b>大[おお]き</b>な 家[いえ]",
        id="Furigana - adjective in the な form",
    ),
    pytest.param(
        "大[おお]きな 家[いえ]",
        "大[おお]きいな",
        "<b>大[おお]きな</b> 家[いえ]",
        id="Furigana - adjective in the な form, the word written with the な",
    ),
    pytest.param(
        "小[ちい]さな 家[いえ]",
        "小[ちい]さい",
        "<b>小[ちい]さ</b>な 家[いえ]",
        id="Furigana - adjective in the な form /2",
    ),
    pytest.param(
        "早読[はやよ]みするぜ",
        "早[はや]い",
        "<b>早[はや]</b> 読[よ]みするぜ",
        id="Furigana - adjective inflection with な /1",
    ),
    # A word with okurigana wants that okurigana after its last kanji, so a run going on past
    # the kanji is another word: 出来事 is a noun. Only a word that gives no reading of its own
    # needs the rule; a word that gives one has it to disagree with the text's reading, so
    # 出来[でき]る splits the run the way any word with a reading does. A run that only begins
    # before the word's kanji (花見 / 見る) stays the ambiguity it is on both paths.
    pytest.param(
        "今日の 出来事[できごと]",
        "出来る",
        "今日の 出来事[できごと]",
        id="Okuri word - a run continuing past the word's kanji is not the word",
    ),
    pytest.param(
        "今日の 出来事[できごと]",
        "出来[でき]る",
        "今日の<b> 出来[でき]</b> 事[ごと]",
        id="Okuri word - a word with a reading still splits the run it is part of",
    ),
    pytest.param(
        "花見[はなみ]に 行[い]く",
        "見る",
        "<b>花見[はなみ]</b>に 行[い]く",
        id="Okuri word - a run ending at the word's kanji still matches",
    ),
    pytest.param(
        "花見[はなみ]に 行[い]く",
        "見[み]る",
        "花[はな]<b> 見[み]</b>に 行[い]く",
        id="Okuri word - a run ending at the word's kanji still matches, with furigana",
    ),
    # Matching against the text's readings splits them apart first, and only what that split
    # took apart is put back together: a part of the text the highlight did not touch comes
    # back as it was written, its own furigana words still its own.
    pytest.param(
        "出来[でき] 事[こと]が 好[す]きだ",
        "好[す]き",
        "出来[でき] 事[こと]が<b> 好[す]き</b>だ",
        id="Furigana - furigana words the text wrote apart are not merged",
    ),
    pytest.param(
        "花[はな] 見[み]に 行[い]く",
        "行[い]く",
        "花[はな] 見[み]に<b> 行[い]く</b>",
        id="Furigana - furigana words the text wrote apart are not merged, word with okuri",
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
    # A number is the same number in digits of either width and in kanji numerals, and a note's
    # word and its sentence do not always write it the same way. A word that is not found as
    # written is looked for with its numbers written as the text writes them
    # (`text_spelling_tests.py` has the rewriting on its own). The reading a digit has in the
    # text still has to be the word's; a digit without one has nothing to disagree with.
    pytest.param(
        "海賊[かいぞく]<k> 達[たち]</k>は ７[なな]つの 海[うみ]を 航海[こうかい]<k> 為[し]た</k>。",
        " 七[なな]つの 海[うみ]",
        "海賊[かいぞく]<k> 達[たち]</k>は<b> ７[なな]つの 海[うみ]</b>を 航海[こうかい]<k> 為[し]た</k>。",
        id="Number - numeral in the word, a digit with the same reading in the text",
    ),
    pytest.param(
        "海賊[かいぞく]<k> 達[たち]</k>は ７[なな]つの 海[うみ]を 航海[こうかい]<k> 為[し]た</k>。",
        "七[なな]つ",
        "海賊[かいぞく]<k> 達[たち]</k>は<b> ７[なな]つ</b>の 海[うみ]を 航海[こうかい]<k> 為[し]た</k>。",
        id="Number - numeral with okurigana in the word, a digit with the same reading in the text",
    ),
    pytest.param(
        "私[わたし]は４つの 会社[かいしゃ]に 投資[とうし]<k> 為[し]ています</k>。",
        " 四[よっ]つ",
        "私[わたし]は<b>４つ</b>の 会社[かいしゃ]に 投資[とうし]<k> 為[し]ています</k>。",
        id="Number - numeral with okurigana in the word, a digit without a reading in the text",
    ),
    pytest.param(
        "罰金[ばっきん]を３ 万[まん] 円[えん]も<k> 取[と]られた</k>よ。",
        " 三[さん]",
        "罰金[ばっきん]を<b>３</b> 万[まん] 円[えん]も<k> 取[と]られた</k>よ。",
        id="Number - one numeral in the word, a digit without a reading in the text",
    ),
    pytest.param(
        "グレゴリオ 暦[れき]の 7[しち] 月[がつ] 7日[なのか]は 夏[なつ]だが、 古来[こらい]の 七夕[たなばた]は 秋[あき]の 季語[きご]である。",
        "七[しち]",
        "グレゴリオ 暦[れき]の<b> 7[しち]</b> 月[がつ] 7日[なのか]は 夏[なつ]だが、 古来[こらい]の 七夕[たなばた]は 秋[あき]の 季語[きご]である。",
        id="Number - a half-width digit, and the same digit read otherwise is not the word",
    ),
    pytest.param(
        "<k> 此[こ]の</k> 綱[つな]は 直径[ちょっけい]２０ ｃｍ[せんち]<k> 有[あ]るそうです</k>。",
        " 二十[にじゅう]",
        "<k> 此[こ]の</k> 綱[つな]は 直径[ちょっけい]<b>２０</b> ｃｍ[せんち]<k> 有[あ]るそうです</k>。",
        id="Number - two numerals in the word, two digits in the text",
    ),
    pytest.param(
        "テスト 期間[きかん]は１０ 日[か]から１５ 日[にち]<k> 迄[まで]</k>だ。",
        "十日[とおか]",
        "テスト 期間[きかん]は<b>１０ 日[か]</b>から１５ 日[にち]<k> 迄[まで]</k>だ。",
        id="Number - one numeral in the word, two digits in the text, a counter after them",
    ),
    pytest.param(
        "火事[かじ]です。１１９ 番[ばん]に 電話[でんわ]<k> 為[し]て 下[くだ]さい</k>。",
        " 百十九番[ひゃくじゅうきゅうばん]",
        "火事[かじ]です。<b>１１９ 番[ばん]</b>に 電話[でんわ]<k> 為[し]て 下[くだ]さい</k>。",
        id="Number - three numerals in the word, three digits in the text",
    ),
    pytest.param(
        "牛[うし]の 胆石[たんせき]。 １０００[せん]<k> 居[い]る 内[うち]</k>の １頭[いっとう]しか<k> 無[な]い</k>",
        " 千[せん]",
        "牛[うし]の 胆石[たんせき]。<b> １０００[せん]</b><k> 居[い]る 内[うち]</k>の １頭[いっとう]しか<k> 無[な]い</k>",
        id="Number - one numeral in the word, four digits with the same reading in the text",
    ),
    pytest.param(
        "牛[うし]の 胆石[たんせき]。 １０００[せん]<k> 居[い]る 内[うち]</k>の １頭[いっとう]しか<k> 無[な]い</k>",
        " 一頭[いっとう]",
        "牛[うし]の 胆石[たんせき]。 １０００[せん]<k> 居[い]る 内[うち]</k>の<b> １頭[いっとう]</b>しか<k> 無[な]い</k>",
        id="Number - a digit sharing its bracket with a kanji in the text",
    ),
    pytest.param(
        "収賄事件[しゅうわいじけん]の 審問[しんもん]が 10日[とおか]に 開[ひら]かれる。",
        " 十[とお]",
        "収賄事件[しゅうわいじけん]の 審問[しんもん]が<b> 10[とお]</b> 日[か]に 開[ひら]かれる。",
        id="Number - digits sharing their bracket with a kanji the word does not have",
    ),
    # 万 and the units above it are written out after digits too, so the numerals before one
    # are a number of their own
    pytest.param(
        "<k> 此[こ]の</k> 仕事[しごと]は 日給[にっきゅう]1 万[まん] 円[えん]だ。",
        " 一万円[いちまんえん]",
        "<k> 此[こ]の</k> 仕事[しごと]は 日給[にっきゅう]<b>1 万[まん] 円[えん]</b>だ。",
        id="Number - a digit before 万 in the text",
    ),
    pytest.param(
        "<k> 此[こ]の</k> 本[ほん]の 第[だい]６ 章[しょう]が 特[とく]に 好[す]きです。",
        " 第六[だいろく]",
        "<k> 此[こ]の</k> 本[ほん]の<b> 第[だい]６</b> 章[しょう]が 特[とく]に 好[す]きです。",
        id="Number - a digit after a kanji of the word",
    ),
    pytest.param(
        "来月[らいげつ]の 二十日[はつか]に 会[あ]いましょう。",
        "20日[はつか]",
        "来月[らいげつ]の<b> 二十日[はつか]</b>に 会[あ]いましょう。",
        id="Number - digits in the word, numerals in the text",
    ),
    pytest.param(
        "あの 頃[ころ]は２ちゃんねるを 見[み]ていた",
        " 2[に]ちゃんねる",
        "あの 頃[ころ]は<b>２ちゃんねる</b>を 見[み]ていた",
        id="Number - a half-width digit in the word, the full-width one in the text",
    ),
    # A number is all of its digits: 1 is not in 10, nor 十 in 20
    pytest.param(
        "１ 月[がつ]１０ 日[か]に１１９ 番[ばん]に 電話[でんわ]した",
        " 一[いち]",
        "<b>１</b> 月[がつ]１０ 日[か]に１１９ 番[ばん]に 電話[でんわ]した",
        id="Number - a digit is not found inside a longer number",
    ),
    pytest.param(
        "明朝[みょうちょう]１０ 時[じ]に１１９ 番[ばん]に 電話[でんわ]する",
        " 一[いち]",
        "明朝[みょうちょう]１０ 時[じ]に１１９ 番[ばん]に 電話[でんわ]する",
        id="Number - a digit is not found inside a longer number, and nowhere else",
    ),
    pytest.param(
        "<k> 此[こ]の</k> 綱[つな]は 直径[ちょっけい]２０ ｃｍ[せんち]<k> 有[あ]るそうです</k>。",
        " 十[じゅう]",
        "<k> 此[こ]の</k> 綱[つな]は 直径[ちょっけい]２０ ｃｍ[せんち]<k> 有[あ]るそうです</k>。",
        id="Number - a numeral is not found in the digits of a number it is part of",
    ),
    pytest.param(
        "富士山[ふじさん]の 高[たか]さは３，７７６メートルです。",
        " 三[さん]",
        "富士山[ふじさん]の 高[たか]さは３，７７６メートルです。",
        id="Number - a digit is not found in a number written with a separator",
    ),
    pytest.param(
        "あの 頃[ころ]は１２ちゃんねるを 見[み]ていた",
        " 2[に]ちゃんねる",
        "あの 頃[ころ]は１２ちゃんねるを 見[み]ていた",
        id="Number - a digit of the word is not found inside a longer number either",
    ),
    # The digit's reading is the numeral's reading where the text gives one
    pytest.param(
        "海賊[かいぞく]<k> 達[たち]</k>は ７[なな]つの 海[うみ]を 航海[こうかい]<k> 為[し]た</k>。",
        "七[しち]",
        "海賊[かいぞく]<k> 達[たち]</k>は ７[なな]つの 海[うみ]を 航海[こうかい]<k> 為[し]た</k>。",
        id="Number - a digit the text reads otherwise is not the word",
    ),
    pytest.param(
        "学級委員[がっきゅういいん] 私[わたし] １人[ひとり]だったって<k> 事[こと]</k>に<k> 出来[でき]ない</k>かな…",
        " 一人[いちにん]",
        "学級委員[がっきゅういいん] 私[わたし] １人[ひとり]だったって<k> 事[こと]</k>に<k> 出来[でき]ない</k>かな…",
        id="Number - a digit and its kanji the text reads otherwise are not the word",
    ),
    # Only a word that is not in the text as written is looked for in another spelling
    pytest.param(
        "一人[ひとり]で１ 個[こ] 食[た]べた",
        "一[ひと]",
        "<b>一[ひと]</b> 人[り]で１ 個[こ] 食[た]べた",
        id="Number - a word found as written is not looked for in digits as well",
    ),
    # Latin letters can carry a reading like kanji do, in the word or in the text. They are
    # the same letters with it and without, and whatever it says: the letters are the word.
    pytest.param(
        "ＡＢＣ[えいびーしー]ニュースに<k> 依[よ]れば</k>、もう一 機[き]のジェット 旅客機[りょかくき]が",
        "ＡＢＣニュース",
        "<b>ＡＢＣ[えいびーしー]ニュース</b>に<k> 依[よ]れば</k>、もう一 機[き]のジェット 旅客機[りょかくき]が",
        id="Latin letters - a reading on them in the text, none in the word",
    ),
    pytest.param(
        "私[わたし]は Ｒ[あーる]．バートンの「 歴史[れきし]叢書[そうしょ]」を 買[か]う",
        "Ｒ．バートン",
        "私[わたし]は<b> Ｒ[あーる]．バートン</b>の「 歴史[れきし]叢書[そうしょ]」を 買[か]う",
        id="Latin letters - a reading on them in the text, none in the word, a space before them",
    ),
    pytest.param(
        "表面[ひょうめん]に１ｎｍ 程度[ていど]の 厚[あつ]さの 酸化[さんか]アルミニウムが<k> 出来[でき]る</k>。",
        "ｎｍ[なのめーとる]",
        "表面[ひょうめん]に１<b>ｎｍ</b> 程度[ていど]の 厚[あつ]さの 酸化[さんか]アルミニウムが<k> 出来[でき]る</k>。",
        id="Latin letters - a reading on them in the word, none in the text",
    ),
    pytest.param(
        "ＡＢＣ[えいびーしー]ニュースに<k> 依[よ]れば</k>",
        "ＡＢＣ[えーびーしー]ニュース",
        "<b>ＡＢＣ[えいびーしー]ニュース</b>に<k> 依[よ]れば</k>",
        id="Latin letters - a reading on them spelled otherwise in the text",
    ),
    pytest.param(
        "右側[みぎがわ]<k> 丈[だけ]</k>４Ｋテレビ<k> 見[み]たいだ</k>な…",
        "四Ｋ[よんけー]",
        "右側[みぎがわ]<k> 丈[だけ]</k><b>４Ｋ</b>テレビ<k> 見[み]たいだ</k>な…",
        id="Latin letters - a reading on them in the word, after a numeral the text has as a digit",
    ),
    pytest.param(
        "ＮＨＫ[えぬえいちけい] 教育[きょういく]テレビを 見[み]る",
        "ＮＨＫ 教育[きょういく]",
        "<b>ＮＨＫ[えぬえいちけい] 教育[きょういく]</b>テレビを 見[み]る",
        id="Latin letters - a reading on them in the text, before a kanji with one in the word",
    ),
    pytest.param(
        "ＮＨＫ 教育[きょういく]テレビを 見[み]る",
        "ＮＨＫ[えぬえいちけい] 教育[きょういく]",
        "<b>ＮＨＫ 教育[きょういく]</b>テレビを 見[み]る",
        id="Latin letters - a reading on them in the word, before a kanji with one in the text",
    ),
    # The katakana after the letters' reading is part of the word like any other kana
    pytest.param(
        "白[しろ]いＴシャツを 着[き]る",
        "Ｔ[てぃー]シャツ",
        "白[しろ]い<b>Ｔシャツ</b>を 着[き]る",
        id="Latin letters - a reading on them in the word, katakana after it",
    ),
    pytest.param(
        "Ｔ 字[じ]の 道[みち]を 歩[ある]く",
        "Ｔ[てぃー]シャツ",
        "Ｔ 字[じ]の 道[みち]を 歩[ある]く",
        id="Latin letters - the letters without the katakana after them are not the word",
    ),
    # A kanji said twice is written twice or with 々, and the furigana splitting keeps the two
    # spellings apart: 駄々 stays one token and 駄駄 becomes two. A word not found as written is
    # looked for in the spelling the text has.
    pytest.param(
        "そんなに<k> 駄々[だだ]</k>を<k> 捏[こ]ねる 物[もん]</k>じゃない。",
        "駄駄[だだ]",
        "そんなに<k><b> 駄々[だだ]</b></k>を<k> 捏[こ]ねる 物[もん]</k>じゃない。",
        id="Repeated kanji - written twice in the word, with 々 in the text",
    ),
    # The text's two brackets come back as one: with no space between them they are one kanji
    # run, which the furigana paths put together again after splitting it, here as anywhere
    pytest.param(
        " 民主[みんしゅ]主義[しゅぎ]に<k> 就[つ]いて</k> 勉強[べんきょう]<k> 為[し]ました</k>。",
        " 民主々義[みんしゅしゅぎ]",
        "<b> 民主主義[みんしゅしゅぎ]</b>に<k> 就[つ]いて</k> 勉強[べんきょう]<k> 為[し]ました</k>。",
        id="Repeated kanji - with 々 in the word, written twice across two brackets in the text",
    ),
    pytest.param(
        "日日[にちにち]の 記録[きろく]を 付[つ]ける",
        "日々[ひび]",
        "日日[にちにち]の 記録[きろく]を 付[つ]ける",
        id="Repeated kanji - the text's spelling read otherwise is not the word",
    ),
    # The katakana word a word ends in is written with the long vowel mark as often as not.
    # It is the same fixed tail with one: the kanji before it are matched by their readings,
    # however the text cuts them into brackets, and the tail has to follow them.
    pytest.param(
        "『 骨[こつ] 伝導[でんどう]マインドスピーカー』 注視[ちゅうし]<k> 為[し]ている</k> 相手[あいて]の 心[こころ]の 声[こえ]が 聞[き]こえる。",
        "骨伝導マインドスピーカー[こつでんどうまいんどすぴーかー]",
        "『<b> 骨[こつ] 伝導[でんどう]マインドスピーカー</b>』 注視[ちゅうし]<k> 為[し]ている</k> 相手[あいて]の 心[こころ]の 声[こえ]が 聞[き]こえる。",
        id="Katakana tail - a long vowel mark in it, the kanji in two furigana words in the text",
    ),
    pytest.param(
        "爆釣[ばくちょう]伝説[でんせつ]アングラーヒーロー 以降[いこう]では 極端[きょくたん]な 描写[びょうしゃ]は 抑[おさ]えられている",
        "爆釣伝説アングラーヒーロー[ばくちょうでんせつあんぐらーひーろー]",
        "<b>爆釣伝説[ばくちょうでんせつ]アングラーヒーロー</b> 以降[いこう]では 極端[きょくたん]な 描写[びょうしゃ]は 抑[おさ]えられている",
        id="Katakana tail - a long vowel mark in it, the kanji in two brackets in the text",
    ),
    pytest.param(
        "<k> 此[こ]れ</k>が『 絶対[ぜったい] 破壊[はかい]<k> 為[す]る</k>ビーム』、<k> 此[こ]れ</k>を 君[きみ]に 向[む]ける",
        "絶対破壊為るビーム[ぜったいはかいするびーむ]",
        "<k> 此[こ]れ</k>が『<b> 絶対[ぜったい] 破壊[はかい]<k> 為[す]る</k>ビーム</b>』、<k> 此[こ]れ</k>を 君[きみ]に 向[む]ける",
        id="Katakana tail - a long vowel mark in it, okurigana before it",
    ),
    pytest.param(
        "凄[すげ]ーな、これ",
        "凄[すげ]ー",
        "<b>凄[すげ]ー</b>な、これ",
        id="Katakana tail - nothing but a long vowel mark",
    ),
    pytest.param(
        "神[しん]ゲーム 理論[りろん]を 学[まな]ぶ",
        "神ゲー[かみげー]",
        "神[しん]ゲーム 理論[りろん]を 学[まな]ぶ",
        id="Katakana tail - the kanji before it read otherwise are not the word",
    ),
    pytest.param(
        "粘着[ねんちゃく]して 取[と]れない。テープを 貼[は]る",
        "粘着[ねんちゃく]テープ",
        "粘着[ねんちゃく]して 取[と]れない。テープを 貼[は]る",
        id="Katakana tail - the kanji without the tail after them are not the word",
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
    # A note's word field does not always hold the word alone, in ordinary furigana syntax. It
    # is brought into that before it is searched for; `word_normalizer_tests.py` has the shapes
    # one by one, these are what the search then makes of them.
    pytest.param(
        "玉葱[たまねぎ]をざくざくと 切[き]った",
        "ざくざく ",
        "玉葱[たまねぎ]を<b>ざくざく</b>と 切[き]った",
        id="Word shape - a space after a kana word",
    ),
    pytest.param(
        "そんな 冗談[じょうだん]<k> 素面[しらふ]</k>じゃ 言[い]えないよ。",
        "素面[しらふ] ",
        "そんな 冗談[じょうだん]<k><b> 素面[しらふ]</b></k>じゃ 言[い]えないよ。",
        id="Word shape - a space after the word's bracket",
    ),
    pytest.param(
        "例[れい]を<k> 幾[いく]つか</k> 見[み]せて<k> 下[くだ]さい</k>。",
        " 幾[いく]つ[ ]か",
        "例[れい]を<k><b> 幾[いく]つか</b></k> 見[み]せて<k> 下[くだ]さい</k>。",
        id="Word shape - an empty bracket inside the word",
    ),
    pytest.param(
        "量[りょう]を 少[すこ]し 宛[ずつ] 増[ふ]やす",
        "少[すこ]し<k> 宛[ずつ]</k>",
        "量[りょう]を<b> 少[すこ]し 宛[ずつ]</b> 増[ふ]やす",
        id="Word shape - a tag inside the word",
    ),
    pytest.param(
        "言[い]う<k> 迄[まで]</k>も<k> 無[な]く</k>、サーバの 負荷[ふか]が 増大[ぞうだい]する",
        "言う迄も無く[いうまでもなく]",
        "<b>言[い]う<k> 迄[まで]</k>も<k> 無[な]く</k></b>、サーバの 負荷[ふか]が 増大[ぞうだい]する",
        id="Word shape - one bracket after a whole expression",
    ),
    pytest.param(
        "<k> 其[そ]の</k> 土地[とち]に 買[か]い 手[て]が 付[つ]いた。",
        "買い手が付く[かいてがつく]",
        "<k> 其[そ]の</k> 土地[とち]に<b> 買[か]い 手[て]が 付[つ]いた</b>。",
        id="Word shape - one bracket after a whole expression, inflected in the text",
    ),
    pytest.param(
        "楽[たの]しめるなぁ。 神[かみ]ゲーの 名[な]は 伊達[だて]じゃないってか。",
        "神ゲー[かみげー]",
        "楽[たの]しめるなぁ。<b> 神[かみ]ゲー</b>の 名[な]は 伊達[だて]じゃないってか。",
        id="Word shape - one bracket after kanji and a katakana word",
    ),
    pytest.param(
        "匿名[とくめい]で<k> 垂[タ]レ 込[コ]ミ</k>が<k> 有[あ]った</k>！",
        "垂レ込ミ[たれこみ]",
        "匿名[とくめい]で<k><b> 垂[タ]レ 込[コ]ミ</b></k>が<k> 有[あ]った</k>！",
        id="Word shape - one bracket after kanji with katakana okurigana",
    ),
    pytest.param(
        "折[お]れたり<k> 為[し]てなくて</k>。 ピリ<k> 付[つ]いた</k>わ～。",
        "ピリ付く[ぴりつく]",
        "折[お]れたり<k> 為[し]てなくて</k>。<b> ピリ<k> 付[つ]いた</k></b>わ～。",
        id="Word shape - one bracket after katakana and an inflecting kanji",
    ),
    pytest.param(
        "彼女[かのじょ]はスペイン 語[ご]に 取[と]り 組[く]んでいます。",
        "スペイン 語[すぺいんご]",
        "彼女[かのじょ]は<b>スペイン 語[ご]</b>に 取[と]り 組[く]んでいます。",
        id="Word shape - a bracket that reads the katakana before its kanji",
    ),
    pytest.param(
        "彼女[かのじょ]は 人[ひと]に 対[たい]してやいばを<k> 研[と]いでいます</k>。",
        "に 対[にたい]して",
        "彼女[かのじょ]は 人[ひと]<b>に 対[たい]して</b>やいばを<k> 研[と]いでいます</k>。",
        id="Word shape - a bracket that reads the particle before its kanji",
    ),
    pytest.param(
        "<k> 其[そ]の</k> 事故[じこ]で 多量[たりょう]のガス 漏[も]れが<k> 有[あ]った</k>ね。",
        "ガス 漏[がすも]れ",
        "<k> 其[そ]の</k> 事故[じこ]で 多量[たりょう]の<b>ガス 漏[も]れ</b>が<k> 有[あ]った</k>ね。",
        id="Word shape - a bracket that reads the katakana before its kanji, okurigana after",
    ),
    pytest.param(
        "<k> 皆[みんな]</k> 聞[き]き 耳[みみ]を<k> 立[た]てた</k>。",
        "聞き 耳[ききみみ]を 立[た]てる",
        "<k> 皆[みんな]</k><b> 聞[き]き 耳[みみ]を<k> 立[た]てた</k></b>。",
        id="Word shape - a bracket that reads the kanji before its own too",
    ),
    pytest.param(
        "口[くち]は 災[わざわ]いの 元[もと]です。",
        "口は 災[くちはわざわ]いの 元[もと]",
        "<b>口[くち]は 災[わざわ]いの 元[もと]</b>です。",
        id="Word shape - a bracket that reads the kanji before its own, an ordinary one after",
    ),
    pytest.param(
        "彼[かれ]は 長[なが]い 間[あいだ]、 海[うみ]に 潜[もぐ]っていたの。",
        " 長[ながいあ]い 間[だ]",
        "彼[かれ]は<b> 長[なが]い 間[あいだ]</b>、 海[うみ]に 潜[もぐ]っていたの。",
        id="Word shape - two brackets cut at the wrong い",
    ),
    pytest.param(
        "甲[こう]の 薬[くすり]は 乙[おつ]の 毒[どく]。",
        "甲の薬は 乙[こう]の 毒[くすりはおつのどく]",
        "<b>甲[こう]の 薬[くすり]は 乙[おつ]の 毒[どく]</b>。",
        id="Word shape - two brackets cut at the wrong の",
    ),
    # Re-cutting a word gives it no licence to match a reading it does not have
    pytest.param(
        "長[なが]い 間[ま]が 空[あ]いた",
        " 長[ながいあ]い 間[だ]",
        "長[なが]い 間[ま]が 空[あ]いた",
        id="Word shape - a re-cut word still has to agree with the text's reading",
    ),
    # A sentence written with the same misplaced bracket is matched by the word as it was given
    pytest.param(
        "ファックスか 電子メール[でんしめーる]で 申[もう]し 込[こ]む。",
        "電子メール[でんしめーる]",
        "ファックスか<b> 電子メール[でんしめーる]</b>で 申[もう]し 込[こ]む。",
        id="Word shape - the text has the word's own misplaced bracket",
    ),
    # A splitter dot the word is written with is no more a character to match than the text's
    # are (see the "Splitter dot" cases below): the word is found where the text has the dot
    # and where it does not.
    pytest.param(
        "ヘレン・ケラーは 盲人[もうじん]で、 聾唖[ろうあ]者[しゃ]です。",
        "ヘレン・ケラー",
        "<b>ヘレン・ケラー</b>は 盲人[もうじん]で、 聾唖[ろうあ]者[しゃ]です。",
        id="Word shape - a splitter dot in a kana word",
    ),
    pytest.param(
        "晒[さら]す「イキュラス・エル・ラン」の 呪符[じゅふ]…！",
        "イキュラス・エル・ラン",
        "晒[さら]す「<b>イキュラス・エル・ラン</b>」の 呪符[じゅふ]…！",
        id="Word shape - two splitter dots in a kana word",
    ),
    pytest.param(
        "ヘレンケラーは 盲人[もうじん]です。",
        "ヘレン・ケラー",
        "<b>ヘレンケラー</b>は 盲人[もうじん]です。",
        id="Word shape - a splitter dot in a kana word, none in the text",
    ),
    pytest.param(
        "私への 報・ 連・ 相を 行っていただきます",
        "報・連・相",
        "私への<b> 報・ 連・ 相</b>を 行っていただきます",
        id="Word shape - splitter dots in a kanji word without furigana",
    ),
    pytest.param(
        "阪神[はんしん]・ 淡路大震災[あわじだいしんさい]では、 何[なん] 千[せん] 人[にん]もの 命[いのち]が",
        "阪神・ 淡路大震災[はんしんあわじだいしんさい]",
        "<b>阪神[はんしん]・ 淡路大震災[あわじだいしんさい]</b>では、 何[なん] 千[せん] 人[にん]もの 命[いのち]が",
        id="Word shape - a splitter dot in a kanji word, one bracket reading both parts",
    ),
    # A kana word written without a dot keeps to the text as it stands. Kana words are short,
    # and between two katakana words a dot is what keeps one from running into the other.
    pytest.param(
        "テスト・ライブを 見[み]た",
        "トラ",
        "テスト・ライブを 見[み]た",
        id="Word shape - a kana word written without a dot is not found across the text's",
    ),
    pytest.param(
        "ヘレン・ケラーは 盲人[もうじん]です。",
        "ケラー",
        "ヘレン・<b>ケラー</b>は 盲人[もうじん]です。",
        id="Word shape - a kana word written without a dot, beside the text's",
    ),
    # Degenerate: with its dot gone there is no word left. The point is not crashing.
    pytest.param(
        "ヘレン・ケラーは 盲人[もうじん]です。",
        "・",
        "ヘレン・ケラーは 盲人[もうじん]です。",
        id="Word shape - nothing but a splitter dot",
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
    # MeCab writes a verb's headword with the scripts the text has: a katakana stem with a
    # hiragana ending. The word is the same word in either script.
    pytest.param(
        "一人[ひとり] 親[おや]だから <k> 到頭[とうとう]</k>グレちゃったかと",
        "ぐれる",
        "一人[ひとり] 親[おや]だから <k> 到頭[とうとう]</k><b>グレ</b>ちゃったかと",
        id="Kana only - katakana stem in the text, word in hiragana",
    ),
    pytest.param(
        "犯人[はんにん]がフケちまう…",
        "ふける",
        "犯人[はんにん]が<b>フケ</b>ちまう…",
        id="Kana only - katakana stem in the text, word in hiragana /2",
    ),
    pytest.param(
        "思[おも]いと 反比例[はんぴれい]<k> 為[す]る 様[よう]に</k>、ダサさ、 弱[よわ]さが",
        "ださい",
        "思[おも]いと 反比例[はんぴれい]<k> 為[す]る 様[よう]に</k>、<b>ダサさ</b>、 弱[よわ]さが",
        id="Kana only - katakana stem of an adjective in the text, word in hiragana",
    ),
    # MeCab hands ～ back as ~. The text that comes back is the text that went in, with the
    # highlight added and nothing else different.
    pytest.param(
        "「しっかし<k> 其[そ]の</k>チクられた 子[こ] ああ～<k> 何[なん]</k>だっけ？」",
        "ちくる",
        "「しっかし<k> 其[そ]の</k><b>チクられた</b> 子[こ] ああ～<k> 何[なん]</k>だっけ？」",
        id="Kana only - a character MeCab rewrites comes back as the text has it",
    ),
    pytest.param(
        "今回[こんかい] 夜雲[やくも]さんはおちゃらけてないのに～～！",
        "おちゃらける",
        "今回[こんかい] 夜雲[やくも]さんは<b>おちゃらけてない</b>のに～～！",
        id="Kana only - a character MeCab rewrites comes back as the text has it /2",
    ),
    # ある after で and じゃ is an auxiliary to MeCab, which is the job it does there and not
    # another way of inflecting
    pytest.param(
        "非常[ひじょう]に 博学[はくがく]であり、 多[おお]くの 文字[もじ]を 読[よ]む",
        "ある",
        "非常[ひじょう]に 博学[はくがく]で<b>あり</b>、 多[おお]くの 文字[もじ]を 読[よ]む",
        id="Kana only - verb MeCab tags as an auxiliary",
    ),
    pytest.param(
        "移動[いどう]<k> 為[し]てる</k> 場合[ばあい]じゃありませんね｡",
        "ある",
        "移動[いどう]<k> 為[し]てる</k> 場合[ばあい]じゃ<b>ありません</b>ね｡",
        id="Kana only - verb MeCab tags as an auxiliary /2",
    ),
    pytest.param(
        "本日[ほんじつ]のランチはハンバーグでございます。",
        "ござる",
        "本日[ほんじつ]のランチはハンバーグで<b>ございます</b>。",
        id="Kana only - verb MeCab tags as an auxiliary /3",
    ),
    pytest.param(
        "そうでした",
        "です",
        "そう<b>でした</b>",
        id="Kana only - an auxiliary is found as a word too",
    ),
    # A word of several words is several tokens, the last of which inflects
    pytest.param(
        "<k> 此[こ]の</k> 写真[しゃしん]はピントがずれています。",
        "ピントがずれる",
        "<k> 此[こ]の</k> 写真[しゃしん]は<b>ピントがずれています</b>。",
        id="Kana only - phrase whose last word is inflected",
    ),
    pytest.param(
        "性的[せいてき]な 犯罪[はんざい]が 増[ふ]えつつあります。",
        "つつある",
        "性的[せいてき]な 犯罪[はんざい]が 増[ふ]え<b>つつあります</b>。",
        id="Kana only - phrase whose last word is inflected /2",
    ),
    pytest.param(
        "捜索[そうさく]の 責任者[せきにんしゃ]でもあった。",
        "でもある",
        "捜索[そうさく]の 責任者[せきにんしゃ]<b>でもあった</b>。",
        id="Kana only - phrase whose last word is inflected /3",
    ),
    pytest.param(
        "液体[えきたい]は硫酸[りゅうさん]であった。",
        "である",
        "液体[えきたい]は硫酸[りゅうさん]<b>であった</b>。",
        id="Kana only - phrase whose last word MeCab tags as an auxiliary",
    ),
    pytest.param(
        "<k> 此[こ]の</k> 四[よん] 本[ほん]の 紐[ひも]なのであって、 手[て]や 足[あし]は",
        "なのである",
        "<k> 此[こ]の</k> 四[よん] 本[ほん]の 紐[ひも]<b>なのであって</b>、 手[て]や 足[あし]は",
        id="Kana only - phrase of four tokens, the last one inflected",
    ),
    pytest.param(
        "びっくりしたよ",
        "びっくりする",
        "<b>びっくりした</b>よ",
        id="Kana only - する verb written in kana",
    ),
    pytest.param(
        "写真[しゃしん]の 位置[いち]がずれています。",
        "ピントがずれる",
        "写真[しゃしん]の 位置[いち]がずれています。",
        id="Kana only - the last word of a phrase without the rest of it is not the phrase",
    ),
    pytest.param(
        "歩[ある]きつつ 話[はなし]があります。",
        "つつある",
        "歩[ある]きつつ 話[はなし]があります。",
        id="Kana only - the words of a phrase apart from each other are not the phrase",
    ),
    # A verb MeCab does not know comes back in pieces, the last of which still inflects as
    # the word's ending does
    pytest.param(
        "性悪[しょうわる] 天使[てんし]に ぼったくられたぜ。",
        "ぼったくる",
        "性悪[しょうわる] 天使[てんし]に <b>ぼったくられた</b>ぜ。",
        id="Kana only - verb MeCab cuts into several tokens, the last one inflected",
    ),
    # は and いる spell はいる, which is a verb of its own and goes はいらない
    pytest.param(
        "彼[かれ]はいないよ",
        "はいる",
        "彼[かれ]はいないよ",
        id="Kana only - a particle and a shorter verb are not the verb they spell together",
    ),
    # One kana and a conjugation is too little to know a stem by: に before ない, か before って
    pytest.param(
        "ここにないよ",
        "にる",
        "ここにないよ",
        id="Kana only - a particle spelling a one-kana stem is not the word",
    ),
    pytest.param(
        "行[い]くかって 聞[き]いた",
        "かる",
        "行[い]くかって 聞[き]いた",
        id="Kana only - a particle spelling a one-kana stem is not the word /2",
    ),
    # し, した and して are forms of する, which a verb ending in る does not turn into
    pytest.param(
        "それはミスしたね",
        "ミスる",
        "それはミスしたね",
        id="Kana only - する's forms after the stem are not a conjugation of the word",
    ),
    # MeCab's dictionary has some inflected forms as entries of their own, with their own
    # headword: the negative そぐわない is an adjective to it and the stem ときめき a noun
    pytest.param(
        "人[ひと]の 倫理観[りんりかん]にそぐわない 術[じゅつ]は 使[つか]うのが",
        "そぐう",
        "人[ひと]の 倫理観[りんりかん]に<b>そぐわない</b> 術[じゅつ]は 使[つか]うのが",
        id="Kana only - negative form MeCab has as an adjective of its own",
    ),
    pytest.param(
        "倫理観[りんりかん]にそぐわなくなった",
        "そぐう",
        "倫理観[りんりかん]に<b>そぐわなく</b>なった",
        id="Kana only - negative form MeCab has as an adjective of its own, inflected",
    ),
    pytest.param(
        "我[が]の 強[つよ]い 男[おとこ]にときめき<k> 勝[が]ち</k>だわ．",
        "ときめく",
        "我[が]の 強[つよ]い 男[おとこ]に<b>ときめき</b><k> 勝[が]ち</k>だわ．",
        id="Kana only - verb stem MeCab has as a noun of its own",
    ),
    # Such a form is the word by its spelling alone, which is weaker than MeCab saying so: it
    # is only asked when MeCab finds the word nowhere in the text. かえって is 却って here.
    pytest.param(
        "かえって 疲[つか]れたので 家[いえ]にかえった",
        "かえる",
        "かえって 疲[つか]れたので 家[いえ]に<b>かえった</b>",
        id="Kana only - a word spelled like a form of the word is not it where MeCab finds the word",
    ),
    # A stem of two kana and a conjugation of one is another word more often than not
    pytest.param(
        "わたしは 知[し]らない",
        "わたす",
        "わたしは 知[し]らない",
        id="Kana only - a three-kana word spelled like a form of the word is not the word",
    ),
    # One kana and a conjugation is a word in its own right too often: あれ, おれ, かれ, みたい
    pytest.param(
        "あれは 何[なに]？",
        "ある",
        "あれは 何[なに]？",
        id="Kana only - a one-kana stem and a conjugation is not the word",
    ),
    pytest.param(
        "猫[ねこ]みたいな 顔[かお]",
        "みる",
        "猫[ねこ]みたいな 顔[かお]",
        id="Kana only - a one-kana stem and a conjugation is not the word /2",
    ),
    # After 毛 MeCab cuts へ/ばっ/てる, and おち/ょくって… before んじゃねえ, though it knows
    # both verbs: on their own it reads へばって and おちょくって as their forms
    pytest.param(
        "<k> 御[お]</k> 前[まえ]の 後[うし]ろに<k> 居[い]る 跳[ハ]ネ</k>っ 毛[け]へばってるぞ",
        "へばる",
        (
            "<k> 御[お]</k> 前[まえ]の 後[うし]ろに<k> 居[い]る 跳[ハ]ネ</k>っ 毛[け]"
            "<b>へばって</b>るぞ"
        ),
        id="Kana only - form MeCab cuts apart in this text and reads as the word on its own",
    ),
    pytest.param(
        "「おちょくってんじゃねえの？」",
        "おちょくる",
        "「<b>おちょくって</b>んじゃねえの？」",
        id="Kana only - form MeCab cuts apart in this text and reads as the word on its own /2",
    ),
    pytest.param(
        "それはしないで",
        "はしる",
        "それはしないで",
        id="Kana only - kana spelling a form MeCab does not read as the word is not the word",
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
    # A digit counts as a kanji everywhere, so it can also be the last kanji of a word with
    # okurigana: the one whose reading is checked and whose okurigana is inflected. These
    # raised while the word's last kanji was looked for among the ideographs only.
    pytest.param(
        "７[なな]つの 海[うみ]を 渡[わた]る",
        "７[なな]つ",
        "<b>７[なな]つ</b>の 海[うみ]を 渡[わた]る",
        id="Digit word - a reading on a digit with kana after it",
    ),
    pytest.param(
        "サイトを 閉鎖[へいさ]に 追[お]い 込[こ]んだり、2ちゃんねる 内[ない]に",
        " 2[に]ちゃんねる",
        "サイトを 閉鎖[へいさ]に 追[お]い 込[こ]んだり、<b>2ちゃんねる</b> 内[ない]に",
        id="Digit word - the text writes the digit without the reading the word gives it",
    ),
    pytest.param(
        " 第２[だいに]の 人生[じんせい]",
        "第２[だいに]の",
        "<b> 第２[だいに]の</b> 人生[じんせい]",
        id="Digit word - a digit ending the word's kanji run",
    ),
    # Degenerate: a repeater with no kanji before it repeats nothing. It is taken as the
    # kanji it stands for, which is as sensible as anything; the point is not raising.
    pytest.param(
        "その 々[びと]の 声[こえ]",
        "々[びと]の",
        "その<b> 々[びと]の</b> 声[こえ]",
        id="Crash test - a word that is a bare repeater with a reading and kana",
    ),
    # Degenerate: a bracket that holds no kana is no reading, so the word cannot be split
    # into a reading per kanji and has no last kanji to check and inflect, and the as-written
    # search gives it up. This text writes the very same thing, which the search by reading
    # takes as it stands, bracket and all; the point is not raising.
    pytest.param(
        "これは 独[x]りだった",
        "独[x]り",
        "これは<b> 独[x]り</b>だった",
        id="Crash test - a word whose bracket holds no kana, with kana after it",
    ),
    # ず and づ are one sound, and which of them a reading is spelled with is not a difference.
    pytest.param(
        "動機[どうき] 付[づ]けと<k> 言[い]う</k>のは 因子[いんし]の<k> 一[ひと]つ</k>です。",
        "動機付[どうきず]け",
        "<b>動機[どうき] 付[づ]け</b>と<k> 言[い]う</k>のは 因子[いんし]の<k> 一[ひと]つ</k>です。",
        id="Reading variant - ず in the word, づ in the text",
    ),
    # Rendaku the other way round: the word holds the voiced form of a kanji that is not its
    # first, and the text says the same compound without the voicing.
    pytest.param(
        "<k> 彼[あ]の</k> 人[ひと]は 欲[よく] 深[ふか]い。",
        "欲[よく] 深[ぶか]い",
        "<k> 彼[あ]の</k> 人[ひと]は<b> 欲[よく] 深[ふか]い</b>。",
        id="Reading variant - the word's rendaku is not in the text",
    ),
    pytest.param(
        "動[うご]きは 読[よ]み<k> 易[やす]く</k> 初見殺[しょけんころ]しな… 行動[こうどう]も",
        "初見殺[しょけんごろ]し",
        "動[うご]きは 読[よ]み<k> 易[やす]く</k><b> 初見殺[しょけんころ]し</b>な… 行動[こうどう]も",
        id="Reading variant - the word's rendaku is not in the text, inside one kanji run",
    ),
    pytest.param(
        "「 物販[ぶっぱん]で500 円[えん]で 売[う]ろう」「ぼっ 手繰[たく]り」",
        "ぼっ 手繰[たぐ]り",
        "「 物販[ぶっぱん]で500 円[えん]で 売[う]ろう」「<b>ぼっ 手繰[たく]り</b>」",
        id="Reading variant - the word's rendaku is not in the text, kana before the kanji",
    ),
    # A word that begins voiced is not a rendaku form of anything: 顔[がお] is the suffix and
    # 顔[かお] the noun, 降伏[ごうぶく] and 降伏[こうふく] are two words.
    pytest.param(
        "まこっち 顔[かお]<k> 丈[だけ]</k> 誠実[せいじつ]で 優[やさ]しそうだ",
        " 顔[がお]",
        "まこっち 顔[かお]<k> 丈[だけ]</k> 誠実[せいじつ]で 優[やさ]しそうだ",
        id="Reading variant - a word that begins voiced is not the unvoiced word",
    ),
    pytest.param(
        "白旗[しろはた]は 降伏[こうふく]の 合図[あいず]だ。",
        " 降伏[ごうぶく]",
        "白旗[しろはた]は 降伏[こうふく]の 合図[あいず]だ。",
        id="Reading variant - a word that begins voiced is not the unvoiced word /2",
    ),
    # A voiced reading the kanji lists for itself is a reading, not a sound change, and tells
    # words apart: 中 is チュウ and ジュウ, 見 is ケン and ゲン.
    pytest.param(
        "心中[しんちゅう]<k> 御[お]</k> 察[さっ]しします。",
        "心中[しんじゅう]",
        "心中[しんちゅう]<k> 御[お]</k> 察[さっ]しします。",
        id="Reading variant - a voiced reading of its own is not the unvoiced one",
    ),
    pytest.param(
        "一見[いっけん]して 分[わ]かる。",
        "一見[いちげん]",
        "一見[いっけん]して 分[わ]かる。",
        id="Reading variant - a voiced reading of its own is not the unvoiced one /2",
    ),
    # A stem said two ways: 良い is よい and いい, 行く is いく and ゆく, 得る is える and うる.
    pytest.param(
        "「 体温[たいおん]も 正常値[せいじょうち]ですね。もう<k> 良[い]い</k>ですよ。」",
        "良[よ]い",
        "「 体温[たいおん]も 正常値[せいじょうち]ですね。もう<k><b> 良[い]い</b></k>ですよ。」",
        id="Reading variant - よい found as いい",
    ),
    pytest.param(
        "虫[むし]の 良[い]い 話[はなし]だ。",
        "虫[むし]の 良[よ]い",
        "<b>虫[むし]の 良[い]い</b> 話[はなし]だ。",
        id="Reading variant - よい found as いい, at the end of an expression",
    ),
    pytest.param(
        "台風[たいふう]に 行[ゆ]く 手[て]を 阻[はば]まれました。",
        " 行[い]く 手[て]",
        "台風[たいふう]に<b> 行[ゆ]く 手[て]</b>を 阻[はば]まれました。",
        id="Reading variant - いく found as ゆく, before the word's last kanji",
    ),
    pytest.param(
        "母[はは]が<k> 余所[よそ]</k>行[ゆ]き 用[よう]の 服[ふく]を 買[か]ってくれた。",
        "余所行[よそい]き",
        "母[はは]が<b><k> 余所[よそ]</k> 行[ゆ]き</b> 用[よう]の 服[ふく]を 買[か]ってくれた。",
        id="Reading variant - いき found as ゆき, in a noun",
    ),
    pytest.param(
        "テロ 攻撃[こうげき]の 標的[ひょうてき]に<k> 成[な]り 得[う]る</k>。",
        "得[え]る",
        "テロ 攻撃[こうげき]の 標的[ひょうてき]に<k> 成[な]り<b> 得[う]る</b></k>。",
        id="Reading variant - える found as うる",
    ),
    pytest.param(
        "あの 人[ひと]は 行[ゆ]きたくないと 言[ゆ]った",
        "言[い]う",
        "あの 人[ひと]は 行[ゆ]きたくないと<b> 言[ゆ]った</b>",
        id="Reading variant - いう found as ゆう, inflected",
    ),
    pytest.param(
        "鏡[かがみ]に 映[うつ]る 顔[かお]が 歪[ゆが]む。",
        "歪[いが]む",
        "鏡[かがみ]に 映[うつ]る 顔[かお]が<b> 歪[ゆが]む</b>。",
        id="Reading variant - いがむ found as ゆがむ, a stem of two kana",
    ),
    # Two readings that only happen to take the same okurigana are still two words.
    pytest.param(
        "米[こめ]は<k> 其処[そこ]</k>なら<k> 直[す]ぐ 捌[さば]ける</k>。",
        "捌[は]ける",
        "米[こめ]は<k> 其処[そこ]</k>なら<k> 直[す]ぐ 捌[さば]ける</k>。",
        id="Reading variant - another stem with the same okurigana is not the word",
    ),
    # A place where the text reads the word's last kanji otherwise is judged by the rest of the
    # text. A text that also has the word under its own reading has answered where the word
    # is, and the same kanji read another way in it is another word: it is not marked, not in
    # an inflected form and not as a bare kanji, and its furigana stays grouped as it was.
    pytest.param(
        "面白[おもしろ]いとか 言[い]い 出[だ]す 人[ひと]が 出[で]てくるけど",
        "出[で]てくる",
        "面白[おもしろ]いとか 言[い]い 出[だ]す 人[ひと]が<b> 出[で]てくる</b>けど",
        id="Other reading - another verb of the kanji beside the word is not marked",
    ),
    pytest.param(
        "地下[ちか]に 潜[もぐ]り 索敵網[さくてきもう]を<k> 潜[くぐ]り</k> 抜[ぬ]ける。",
        "潜[もぐ]る",
        "地下[ちか]に<b> 潜[もぐ]り</b> 索敵網[さくてきもう]を<k> 潜[くぐ]り</k> 抜[ぬ]ける。",
        id="Other reading - another verb of the kanji beside the word is not marked /2",
    ),
    pytest.param(
        "そんな 所[ところ]に 居[お]りますか、 居[い]ませんか",
        "居[い]る",
        "そんな 所[ところ]に 居[お]りますか、<b> 居[い]ません</b>か",
        id="Other reading - おります beside いません is not いる",
    ),
    pytest.param(
        "紡錘[ぼうすい]で 糸[いと]を 紡[つむ]ぎ、 布[ぬの]を 織[お]る。",
        "紡[つむ]ぎ",
        "紡錘[ぼうすい]で 糸[いと]を<b> 紡[つむ]ぎ</b>、 布[ぬの]を 織[お]る。",
        id="Other reading - the kanji of a compound beside the word is not marked",
    ),
    pytest.param(
        "子供[こども]が 紙[かみ] 飛行機[ひこうき]を 飛[と]ばしています。",
        "飛[と]ばす",
        "子供[こども]が 紙[かみ] 飛行機[ひこうき]を<b> 飛[と]ばしています</b>。",
        id="Other reading - the kanji of a compound beside the word is not marked /2",
    ),
    # A text that has the kanji only under another reading is still answered with that place.
    # It is as often the word after all, given with the wrong one of the kanji's readings, as
    # it is another word, and nothing in the two arguments tells which.
    pytest.param(
        "<k> 其[そ]の</k> 門[もん]を<k> 潜[くぐ]って</k> 来[き]て<k> 下[くだ]さい</k>。",
        "潜[もぐ]る",
        "<k> 其[そ]の</k> 門[もん]を<k><b> 潜[くぐ]って</b></k> 来[き]て<k> 下[くだ]さい</k>。",
        id="Other reading - the only place the text has the kanji is marked",
    ),
    pytest.param(
        "紡錘[ぼうすい]で 糸[いと]を 巻[ま]く。",
        "紡[つむ]ぎ",
        "<b>紡[ぼう]</b> 錘[すい]で 糸[いと]を 巻[ま]く。",
        id="Other reading - the only place the text has the kanji is marked, a bare kanji",
    ),
    # What counts as the word's own reading, and so is marked beside a plain occurrence: the
    # two irregular verbs in the forms where the stem itself changes,
    pytest.param(
        "勉強[べんきょう]<k> 為[す]る</k>と 言[い]ったのに<k> 為[し]なかった</k>。",
        "為[す]る",
        "勉強[べんきょう]<k><b> 為[す]る</b></k>と 言[い]ったのに<k><b> 為[し]なかった</b></k>。",
        id="Inflected stem - しなかった beside する is the word too",
    ),
    pytest.param(
        "来[く]ると 言[い]ったのに 来[こ]なかった。",
        "来[く]る",
        "<b>来[く]る</b>と 言[い]ったのに<b> 来[こ]なかった</b>。",
        id="Inflected stem - こなかった beside くる is the word too",
    ),
    # and a bracket that ends at another kana than the word's: the text's holds the start of
    # the okurigana, or the word's holds kana the text writes after the kanji. (The noun form
    # in the text's bracket is the case with 字引[じびき] further up.)
    pytest.param(
        "水[みず]が 溜[た]まる 所[ところ]にごみも 溜[たま]っている。",
        "溜[た]まる",
        "水[みず]が<b> 溜[た]まる</b> 所[ところ]にごみも<b> 溜[たま]っている</b>。",
        id="Okurigana moved - the start of the okurigana in the text's bracket is the word too",
    ),
    pytest.param(
        "鉄[てつ]は 錆[さび]る。 包丁[ほうちょう]も 錆[さ]びてしまった。",
        "錆[さび]る",
        "鉄[てつ]は<b> 錆[さび]る</b>。 包丁[ほうちょう]も<b> 錆[さ]びて</b>しまった。",
        id="Okurigana moved - the end of the word's bracket after the kanji is the word too",
    ),
    pytest.param(
        "棒[ぼう]で 突[つ]いて、 指[ゆび]で 突[つつ]いている。",
        "突[つ]く",
        "棒[ぼう]で<b> 突[つ]いて</b>、 指[ゆび]で 突[つつ]いている。",
        id="Okurigana moved - kana in the bracket that are not the okurigana's are another word",
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
    # A kana word is searched for as it is written before the mecab path is tried, so that
    # search has to see through the caller's tags the way the mecab one does.
    pytest.param(
        "この<i>い</i>えは",
        "いえ",
        "この<b><i>い</i>え</b>は",
        id="Html shape - a tag splitting a kana word is still the word",
    ),
    pytest.param(
        'この<span class="x">い</span>えは',
        "いえ",
        'この<b><span class="x">い</span>え</b>は',
        id="Html shape - a tag with attributes splitting a kana word is still the word",
    ),
    pytest.param(
        "この<i>い</i>え<i>で</i>す",
        "いえで",
        "この<b><i>い</i>え<i>で</i></b>す",
        id="Html shape - two tags splitting a kana word are still the word",
    ),
    pytest.param(
        "この<i>いえ</i>は",
        "いえ",
        "この<i><b>いえ</b></i>は",
        id="Html shape - a tag around a whole kana word keeps the highlight inside it",
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
    # A text can spell the word another way than the word field does and read the same: kana
    # for one of its kanji or for all of them, kanji for its kana, okurigana inside the bracket
    # on one side and written out on the other. Such a place is found by its reading
    # (reading_highlight.py), and only where the word as written was found nowhere.
    #
    # A kanji that both sides write is most of what it takes, however the rest is spelled.
    pytest.param(
        "<k> 眼鏡[メガネ]</k>が 見[み]つかりません。",
        "見付[みつ]かる",
        "<k> 眼鏡[メガネ]</k>が<b> 見[み]つかりません</b>。",
        id="Reading - a kanji of the word is kana in the text, inflected",
    ),
    pytest.param(
        "雪[ゆき]の 重[おも]みで 枝[えだ]が 折[お]れそうだ。",
        "重味[おもみ]",
        "雪[ゆき]の<b> 重[おも]み</b>で 枝[えだ]が 折[お]れそうだ。",
        id="Reading - the word's last kanji is kana in the text",
    ),
    pytest.param(
        "木[こ]の 葉[は]がそよ 風[かぜ]に<k> 揺[ゆ]れている</k>。",
        "微風[そよかぜ]",
        "木[こ]の 葉[は]が<b>そよ 風[かぜ]</b>に<k> 揺[ゆ]れている</k>。",
        id="Reading - the word's first kanji is kana in the text",
    ),
    pytest.param(
        "彼[かれ]は 天[あま]の 邪鬼[じゃく]って 言[い]うか",
        "天之邪鬼[あまのじゃく]",
        "彼[かれ]は<b> 天[あま]の 邪鬼[じゃく]</b>って 言[い]うか",
        id="Reading - a kanji in the middle of the word is kana in the text",
    ),
    pytest.param(
        "彼[かれ]は<k> 飽[あ]くまで</k>自分[じぶん]の 主義[しゅぎ]を 通[とお]す。",
        "飽[あ]く 迄[まで]",
        "彼[かれ]は<k><b> 飽[あ]くまで</b></k>自分[じぶん]の 主義[しゅぎ]を 通[とお]す。",
        id="Reading - the place is the whole of a k tag",
    ),
    pytest.param(
        "場合[ばあい]、うどん<k> 粉[こ]</k> 病[びょう]を 発生[はっせい]<k> 為[す]る</k>。",
        "饂飩粉病[うどんこびょう]",
        "場合[ばあい]、<b>うどん<k> 粉[こ]</k> 病[びょう]</b>を 発生[はっせい]<k> 為[す]る</k>。",
        id="Reading - the place holds a k tag",
    ),
    pytest.param(
        "<k> 此[こ]の 挽[ひ]き</k> 肉[にく]でハンバーグを 作[つく]りましょう。",
        "挽肉[ひきにく]",
        "<k> 此[こ]の</k><b><k> 挽[ひ]き</k> 肉[にく]</b>でハンバーグを 作[つく]りましょう。",
        id="Reading - the place starts inside a k tag and ends after it",
    ),
    pytest.param(
        "<k> 酷[ひど]い</k> 有[あ]り 様[さま]でした。",
        "有様[ありさま]",
        "<k> 酷[ひど]い</k><b> 有[あ]り 様[さま]</b>でした。",
        id="Reading - okurigana the word keeps in its bracket, between two kanji",
    ),
    pytest.param(
        "彼[かれ]は 並[な]みの 人間[にんげん]ではありません。",
        "並[なみ]",
        "彼[かれ]は<b> 並[な]み</b>の 人間[にんげん]ではありません。",
        id="Reading - okurigana the word keeps in its bracket, after the kanji",
    ),
    pytest.param(
        "売主[うりぬし]は、 製品[せいひん]を 渡[わた]す。",
        "売[う]り 主[ぬし]",
        "<b>売主[うりぬし]</b>は、 製品[せいひん]を 渡[わた]す。",
        id="Reading - okurigana the text keeps in its bracket",
    ),
    pytest.param(
        "<k> 此奴[こいつ] 等[ら]</k>を<k> 摘[つ]まみ</k> 出[だ]せ。",
        "摘[つま]み 出[だ]す",
        "<k> 此奴[こいつ] 等[ら]</k>を<b><k> 摘[つ]まみ</k> 出[だ]せ</b>。",
        id="Reading - the stem and the okurigana are cut at another kana, inflected",
    ),
    # The word's reading is compared as a whole, so where it is cut between the kanji does
    # not have to be where the text cuts it.
    pytest.param(
        "私[わたし]の 住[す]まいは 東京[とうきょう]に<k> 有[あ]ります</k>。",
        "住[すま]居[い]",
        "私[わたし]の<b> 住[す]まい</b>は 東京[とうきょう]に<k> 有[あ]ります</k>。",
        id="Reading - the word splits its reading between the kanji elsewhere than the text",
    ),
    pytest.param(
        "ギリシア 軍[ぐん]は 立[た]ちはだかった。",
        "立[た]ち 開[はだ]かる",
        "ギリシア 軍[ぐん]は<b> 立[た]ちはだかった</b>。",
        id="Reading - the second verb of a compound is kana in the text, inflected",
    ),
    pytest.param(
        "靴[くつ]の 底[そこ]にガムがくっ 付[つ]いてしまった。",
        "食[く]っ 付[つ]く",
        "靴[くつ]の 底[そこ]にガムが<b>くっ 付[つ]いて</b>しまった。",
        id="Reading - the first verb of a compound is kana in the text, inflected",
    ),
    pytest.param(
        "彼[かれ]は 私[わたし]の 弱[よわ]みを 握[にぎ]っているんだ。",
        "弱味[よわみ]を 握[にぎ]る",
        "彼[かれ]は 私[わたし]の<b> 弱[よわ]みを 握[にぎ]っている</b>んだ。",
        id="Reading - a phrase with a kanji in kana, its verb inflected",
    ),
    pytest.param(
        "知[し]らないとは 情[なさ]けない。",
        "情[なさ]け 無[な]い",
        "知[し]らないとは<b> 情[なさ]けない</b>。",
        id="Reading - the kanji of an adjective's ending is kana in the text",
    ),
    pytest.param(
        "知[し]らないとは 情[なさ]けなくて 困[こま]る。",
        "情[なさ]け 無[な]い",
        "知[し]らないとは<b> 情[なさ]けなくて</b> 困[こま]る。",
        id="Reading - the kanji of an adjective's ending is kana in the text, inflected",
    ),
    # Kana the text has for the word's last kanji are only all there is of that kanji; MeCab
    # says whether they end where the word does, or what word they are when they inflect.
    pytest.param(
        "<k> 此[こ]の</k> 話[はなし]は 真実[しんじつ]に 基[もと]づいています。",
        "基付[もとづ]く",
        "<k> 此[こ]の</k> 話[はなし]は 真実[しんじつ]に<b> 基[もと]づいています</b>。",
        id="Reading - the last kanji of a verb's stem is kana in the text, inflected",
    ),
    pytest.param(
        "試[ため]しに<k> 遣[や]ってみて</k>。",
        "遣[や]って 見[み]る",
        "試[ため]しに<k><b> 遣[や]ってみて</b></k>。",
        id="Reading - the last verb of a phrase is kana in the text, inflected",
    ),
    pytest.param(
        "<k> 飽[あ]くまで</k>も 努力[どりょく]<k> 為[し]て</k>",
        "飽[あ]く 迄[まで]",
        "<k><b> 飽[あ]くまで</b></k>も 努力[どりょく]<k> 為[し]て</k>",
        id="Reading - the word's last kanji is kana in the text, a particle after it",
    ),
    pytest.param(
        "「 吝[やぶさ]かではない… 吝[やぶさ]かではないけど…」",
        "吝[やぶさ]かでは 無[な]い",
        "「<b> 吝[やぶさ]かではない</b>…<b> 吝[やぶさ]かではない</b>けど…」",
        id="Reading - the word occurs twice",
    ),
    pytest.param(
        "深[ふか]く<k> 御[お]</k> 詫[わ]び<k> 為[し]ます</k>。",
        "お 詫[わ]び",
        "深[ふか]く<b><k> 御[お]</k> 詫[わ]び</b><k> 為[し]ます</k>。",
        id="Reading - kana of the word is kanji in the text",
    ),
    pytest.param(
        "精一杯[せいいっぱい]の<k> 御[お] 粧[めか]し</k>を<k> 為[し]て</k>",
        "お 粧[めか]し",
        "精一杯[せいいっぱい]の<k><b> 御[お] 粧[めか]し</b></k>を<k> 為[し]て</k>",
        id="Reading - kana of the word is kanji in the text, in one k tag with the rest",
    ),
    pytest.param(
        (
            "海[うみ]の 底[そこ]<k> 迄[まで]</k> 引[ひ]き<k> 摺[ず]り</k> 込[こ]まれて、"
            " 命[いのち]を 奪[うば]われる。"
        ),
        "引[ひ]きずり 込[こ]む",
        (
            "海[うみ]の 底[そこ]<k> 迄[まで]</k><b> 引[ひ]き<k> 摺[ず]り</k> 込[こ]まれて</b>、"
            " 命[いのち]を 奪[うば]われる。"
        ),
        id="Reading - kana in the middle of the word is kanji in the text, inflected",
    ),
    pytest.param(
        "涼[すず]しくて<k> 良[い]い</k> 気持[きもち]なので",
        "いい 気持[きも]ち",
        "涼[すず]しくて<b><k> 良[い]い</k> 気持[きもち]</b>なので",
        id="Reading - kana of the word is kanji in the text and its okurigana is in a bracket",
    ),
    # Where both sides write kanji they have to be the same kanji: a homophone is not the word.
    pytest.param(
        "糸[いと]を 紡[つむ]ぎ 出[だ]す",
        "紬[つむぎ]",
        "糸[いと]を 紡[つむ]ぎ 出[だ]す",
        id="Reading - other kanji with the same reading are not the word",
    ),
    pytest.param(
        "夕立[ゆうだち]に<k> 遭[あ]って</k> 本屋[ほんや]で 雨宿[あまやど]り<k> 為[し]た</k>。",
        "有[あ]る",
        "夕立[ゆうだち]に<k> 遭[あ]って</k> 本屋[ほんや]で 雨宿[あまやど]り<k> 為[し]た</k>。",
        id="Reading - other kanji with the same reading are not the word, inflected",
    ),
    # With no kanji in common, a kanji word the text has in kana is only as sure as its
    # reading is long, so MeCab has to read the kana as words of their own: two kana as one
    # word in its dictionary form, three or more as whole words.
    pytest.param(
        "バツが 三[みっ]つ<k> 有[あ]る</k>ので８５ 点[てん]です。",
        "罰[ばつ]",
        "<b>バツ</b>が 三[みっ]つ<k> 有[あ]る</k>ので８５ 点[てん]です。",
        id="Reading - the whole word is katakana in the text",
    ),
    pytest.param(
        "仕事[しごと]がほぼ 終[お]わりました。",
        "略[ほぼ]",
        "仕事[しごと]が<b>ほぼ</b> 終[お]わりました。",
        id="Reading - the whole word is kana in the text, two kana",
    ),
    pytest.param(
        "さっきの 話[はなし]を 続[つづ]けましょう。",
        "先程[さっき]",
        "<b>さっき</b>の 話[はなし]を 続[つづ]けましょう。",
        id="Reading - the whole word is kana in the text, three kana",
    ),
    pytest.param(
        "もしかしたら 来年[らいねん] 転勤[てんきん]に<k> 成[な]る</k>かも<k> 知[し]れない</k>。",
        "若[も]しかしたら",
        (
            "<b>もしかしたら</b> 来年[らいねん] 転勤[てんきん]に<k> 成[な]る</k>かも<k>"
            " 知[し]れない</k>。"
        ),
        id="Reading - the whole word is kana in the text, several words to MeCab",
    ),
    pytest.param(
        "カップラーメンは 健康[けんこう]に 悪[わる]い。",
        "拉麺[らーめん]",
        "カップ<b>ラーメン</b>は 健康[けんこう]に 悪[わる]い。",
        id="Reading - four kana at the end of a longer word of MeCab's are the word",
    ),
    pytest.param(
        "これがいちばん 好[す]きだ",
        "市場[いちば]",
        "これがいちばん 好[す]きだ",
        id="Reading - three kana at the start of a longer word of MeCab's are not the word",
    ),
    pytest.param(
        "でこぼこの 道[みち]を 歩[ある]く",
        "凸[でこ]",
        "でこぼこの 道[みち]を 歩[ある]く",
        id="Reading - two kana inside another word are not the word",
    ),
    pytest.param(
        "新聞社[しんぶんしゃ]に 何千[なんぜん]ものメールが 寄[よ]せられたよ。",
        "物[もの]",
        "新聞社[しんぶんしゃ]に 何千[なんぜん]ものメールが 寄[よ]せられたよ。",
        id="Reading - two kana that are two words to MeCab are not the word",
    ),
    pytest.param(
        "<k> 何事[なにごと]</k>であれ、<k> 遣[や]る</k>からには",
        "彼[あれ]",
        "<k> 何事[なにごと]</k>であれ、<k> 遣[や]る</k>からには",
        id="Reading - two kana that are a form of another word are not the word",
    ),
    pytest.param(
        "芸術[げいじゅつ]の 高[たか]みから 見[み]る",
        "味[み]",
        "芸術[げいじゅつ]の 高[たか]みから 見[み]る",
        id="Reading - one kana is never the word",
    ),
    # The kana of an inflecting kanji word's stem prove nothing (the い of 言う begins いる), so
    # where the text has the word in kana a MeCab token has to have it for its headword.
    pytest.param(
        "垂[タ]レを 付[つ]けて 焼[や]いてみるか",
        "見[み]る",
        "垂[タ]レを 付[つ]けて 焼[や]いて<b>みる</b>か",
        id="Reading - a verb is kana in the text, in its dictionary form",
    ),
    pytest.param(
        "<k> 此[こ]の</k> 本[ほん]、<k> 貴方[あなた]</k>にあげます。",
        "上[あ]げる",
        "<k> 此[こ]の</k> 本[ほん]、<k> 貴方[あなた]</k>に<b>あげます</b>。",
        id="Reading - a verb is kana in the text, inflected",
    ),
    pytest.param(
        "一切[いっさい] 着色[ちゃくしょく]<k> 為[し]ておりません</k>。",
        "居[お]る",
        "一切[いっさい] 着色[ちゃくしょく]<k> 為[し]て<b>おりません</b></k>。",
        id="Reading - a verb is kana in the text, inflected, inside a k tag",
    ),
    pytest.param(
        "<k> 蛙[カエル]</k>が<k> 跳[は]ねている</k>ね。",
        "言[い]う",
        "<k> 蛙[カエル]</k>が<k> 跳[は]ねている</k>ね。",
        id="Reading - the kana of a verb's stem are not the verb",
    ),
    # The headword also finds the last word of a phrase, with the words before it found by
    # their reading, and a word whose stem is other kana in the inflected form.
    pytest.param(
        "液体[えきたい]は 硫酸[りゅうさん]であった。",
        "で 有[あ]る",
        "液体[えきたい]は 硫酸[りゅうさん]<b>であった</b>。",
        id="Reading - the verb of a phrase is kana in the text, inflected",
    ),
    pytest.param(
        "本日[ほんじつ]のランチはハンバーグでございます。",
        "で 御座[ござ]る",
        "本日[ほんじつ]のランチはハンバーグ<b>でございます</b>。",
        id="Reading - the verb of a phrase is kana in the text, inflected /2",
    ),
    pytest.param(
        "駅[えき]まであった。",
        "で 有[あ]る",
        "駅[えき]まであった。",
        id="Reading - the kana before the verb are the end of another word: not the phrase",
    ),
    pytest.param(
        "昨日[きのう]、 絵[え]の 展覧[てんらん] 会[かい]に 行[い]ってきました。",
        "行[い]って 来[く]る",
        "昨日[きのう]、 絵[え]の 展覧[てんらん] 会[かい]に<b> 行[い]ってきました</b>。",
        id="Reading - the verb of a phrase is kana in the text and its stem changes",
    ),
    pytest.param(
        "<k> 咄嗟[とっさ]</k>に 彼[かれ]の 名前[なまえ]が 出[で]てこなかった。",
        "出[で]て 来[く]る",
        "<k> 咄嗟[とっさ]</k>に 彼[かれ]の 名前[なまえ]が<b> 出[で]てこなかった</b>。",
        id="Reading - the verb of a phrase is kana in the text and its stem changes /2",
    ),
    # A kana word the text has in kanji needs one of its kana written out in the text as well:
    # a reading in a bracket alone is not the word occurring (see "Kana only - a kana word is
    # not the reading in a bracket").
    pytest.param(
        "斯[か]く<k> 在[あ]る 可[べ]き</k>だ。",
        "べき",
        "斯[か]く<k> 在[あ]る<b> 可[べ]き</b></k>だ。",
        id="Reading - the first kana of a kana word is kanji in the text",
    ),
    pytest.param(
        "女子[じょし]…。って<k> 言[い]う</k>か<k> 御[ご] 免[めん]</k>",
        "っていうか",
        "女子[じょし]…。<b>って<k> 言[い]う</k>か</b><k> 御[ご] 免[めん]</k>",
        id="Reading - a kana in the middle of a kana word is kanji in the text",
    ),
    pytest.param(
        "困難[こんなん]も<k> 然[さ]る 事[こと] 乍[なが]ら</k> 市場[しじょう]の",
        "さることながら",
        "困難[こんなん]も<k><b> 然[さ]る 事[こと] 乍[なが]ら</b></k> 市場[しじょう]の",
        id="Reading - most of a kana word is kanji in the text",
    ),
    pytest.param(
        "<k> 可成[かな]り</k>ごちゃ<k> 付[つ]いて</k>んだよねぇ。",
        "ごちゃつく",
        "<k> 可成[かな]り</k><b>ごちゃ<k> 付[つ]いて</k></b>んだよねぇ。",
        id="Reading - a kana of a kana verb is kanji in the text, inflected",
    ),
    pytest.param(
        "<k> 麦酒[ビール]</k>を 飲[の]む",
        "ビール",
        "<k> 麦酒[ビール]</k>を 飲[の]む",
        id="Reading - a kana word is not the reading in a bracket, three kana",
    ),
    pytest.param(
        "欲[よく]に<k> 駆[か]られて</k> 大局[たいきょく]を 誤[あやま]る",
        "かる",
        "欲[よく]に<k> 駆[か]られて</k> 大局[たいきょく]を 誤[あやま]る",
        id="Reading - a kana verb is not the reading in a bracket and an ending",
    ),
    # Width and spaces are not part of how a word reads.
    pytest.param(
        "<k> 此[こ]の</k>ケースにはＣＤが５０ 枚[まい] 入[はい]ります。",
        "CD",
        "<k> 此[こ]の</k>ケースには<b>ＣＤ</b>が５０ 枚[まい] 入[はい]ります。",
        id="Reading - half-width letters in the word, full-width in the text",
    ),
    pytest.param(
        "<k> 内[うち]</k> 2人[ふたり]は 重体[じゅうたい]です。",
        "２人[ふたり]",
        "<k> 内[うち]</k><b> 2人[ふたり]</b>は 重体[じゅうたい]です。",
        id="Reading - a full-width digit in the word, half-width in the text",
    ),
    pytest.param(
        "<k> 通[どお]り</k> ノーダメージ ノーデスだぜ。",
        "ノーダメージノーデス",
        "<k> 通[どお]り</k> <b>ノーダメージ ノーデス</b>だぜ。",
        id="Reading - a space in the text where the word has none",
    ),
]


@pytest.mark.parametrize("text, word, expected", CASES)
def test_word_highlight(text: str, word: str, expected: str):
    assert word_highlight(text, word) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
