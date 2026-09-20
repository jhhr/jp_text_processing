"""Cases for `kana_highlight`, the package's main suite, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/kana/kana_highlight_tests.py

Every case is one sentence put through each of the nine modes `kana_highlight` has — the three
return types, each of them without tags, with tags split and with tags merged — so a case is one
sentence in one mode and its id reads `<case name>-<mode>`. A case gives its expected output per
mode, keyed by the mode's id; a mode it has no expectation for is skipped rather than asserted.

To rerun one case, select it by name:

    python -m pytest jp_text_processing/kana/kana_highlight_tests.py -k "no kanji_to_highlight"

Add `--log-cli-level=debug` to that to see everything the case logged; pytest captures the
package logger on its own, so nothing here has to turn logging on, and it prints the
expected/got diff itself. A case known to fail is written
`pytest.param(..., marks=pytest.mark.xfail(reason="why"))`; none carries one at the moment.
"""


import pytest

from ..all_types.main_types import WithTagsDef
from .kana_highlight import FuriReconstruct, kana_highlight

# (mode id, return type, with_tags, merge_consecutive). The mode id is the key a case's
# expectations are stored under.
MODES = [
    pytest.param("furigana", "furigana", False, False, id="furigana"),
    pytest.param("furigana split", "furigana", True, False, id="furigana split"),
    pytest.param("furigana merged", "furigana", True, True, id="furigana merged"),
    pytest.param("furikanji", "furikanji", False, False, id="furikanji"),
    pytest.param("furikanji split", "furikanji", True, False, id="furikanji split"),
    pytest.param("furikanji merged", "furikanji", True, True, id="furikanji merged"),
    pytest.param("kana_only", "kana_only", False, False, id="kana_only"),
    pytest.param("kana_only split", "kana_only", True, False, id="kana_only split"),
    pytest.param("kana_only merged", "kana_only", True, True, id="kana_only merged"),
]


# (kanji_to_highlight, sentence, onyomi_to_katakana, expected output by mode id)
CASES = [
    pytest.param(
        None,
        "漢字[かんじ]の読[よ]み方[かた]を学[まな]ぶ。",
        True,
        {
            "furigana": " 漢字[カンジ]の 読[よ]み 方[かた]を 学[まな]ぶ。",
            "furikanji": " カンジ[漢字]の よ[読]み かた[方]を まな[学]ぶ。",
            "kana_only": "カンジのよみかたをまなぶ。",
            "furigana split": "<on> 漢[カン]</on><on> 字[ジ]</on>の<kun> 読[よ]</kun><oku>み</oku><kun>"
            " 方[かた]</kun>を<kun> 学[まな]</kun><oku>ぶ</oku>。",
            "furigana merged": "<on> 漢字[カンジ]</on>の<kun> 読[よ]</kun><oku>み</oku><kun> 方[かた]</kun>を"
            "<kun> 学[まな]</kun><oku>ぶ</oku>。",
            "furikanji split": "<on> カン[漢]</on><on> ジ[字]</on>の<kun> よ[読]</kun><oku>み</oku><kun>"
            " かた[方]</kun>を<kun> まな[学]</kun><oku>ぶ</oku>。",
            "furikanji merged": "<on> カンジ[漢字]</on>の<kun> よ[読]</kun><oku>み</oku><kun> かた[方]</kun>を"
            "<kun> まな[学]</kun><oku>ぶ</oku>。",
            "kana_only split": "<on>カン</on><on>ジ</on>の<kun>よ</kun><oku>み</oku><kun>かた</kun>を"
            "<kun>まな</kun><oku>ぶ</oku>。",
            "kana_only merged": "<on>カンジ</on>の<kun>よ</kun><oku>み</oku><kun>かた</kun>を"
            "<kun>まな</kun><oku>ぶ</oku>。",
        },
        id="Should not crash with no kanji_to_highlight",
    ),
    pytest.param(
        "漢字",
        "漢字[かんじ]",
        True,
        {
            "furigana": "<b> 漢字[カンジ]</b>",
            "furikanji": "<b> カンジ[漢字]</b>",
            "kana_only": "<b>カンジ</b>",
            "furigana split": "<b><on> 漢[カン]</on><on> 字[ジ]</on></b>",
            "furigana merged": "<b><on> 漢字[カンジ]</on></b>",
            "furikanji split": "<b><on> カン[漢]</on><on> ジ[字]</on></b>",
            "furikanji merged": "<b><on> カンジ[漢字]</on></b>",
            "kana_only split": "<b><on>カン</on><on>ジ</on></b>",
            "kana_only merged": "<b><on>カンジ</on></b>",
        },
        id="A multi-kanji kanji_to_highlight that is the whole word",
    ),
    pytest.param(
        "生物",
        "生物学[せいぶつがく]",
        True,
        {
            "furigana": "<b> 生物[セイブツ]</b> 学[ガク]",
            "furikanji": "<b> セイブツ[生物]</b> ガク[学]",
            "kana_only": "<b>セイブツ</b>ガク",
            "furigana split": "<b><on> 生[セイ]</on><on> 物[ブツ]</on></b><on> 学[ガク]</on>",
            "furigana merged": "<b><on> 生物[セイブツ]</on></b><on> 学[ガク]</on>",
            "furikanji split": "<b><on> セイ[生]</on><on> ブツ[物]</on></b><on> ガク[学]</on>",
            "furikanji merged": "<b><on> セイブツ[生物]</on></b><on> ガク[学]</on>",
            "kana_only split": "<b><on>セイ</on><on>ブツ</on></b><on>ガク</on>",
            "kana_only merged": "<b><on>セイブツ</on></b><on>ガク</on>",
        },
        id="A multi-kanji kanji_to_highlight within a longer word",
    ),
    pytest.param(
        # Only 生物 is highlighted, not the 物 that starts 物理学
        "生物",
        "生物物理学[せいぶつぶつりがく]",
        True,
        {
            "furigana": "<b> 生物[セイブツ]</b> 物理学[ブツリガク]",
            "furikanji": "<b> セイブツ[生物]</b> ブツリガク[物理学]",
            "kana_only": "<b>セイブツ</b>ブツリガク",
            "furigana split": "<b><on> 生[セイ]</on><on> 物[ブツ]</on></b><on> 物[ブツ]</on><on> 理[リ]</on>"
            "<on> 学[ガク]</on>",
            "furigana merged": "<b><on> 生物[セイブツ]</on></b><on> 物理学[ブツリガク]</on>",
            "furikanji split": "<b><on> セイ[生]</on><on> ブツ[物]</on></b><on> ブツ[物]</on><on> リ[理]</on>"
            "<on> ガク[学]</on>",
            "furikanji merged": "<b><on> セイブツ[生物]</on></b><on> ブツリガク[物理学]</on>",
            "kana_only split": "<b><on>セイ</on><on>ブツ</on></b><on>ブツ</on><on>リ</on><on>ガク</on>",
            "kana_only merged": "<b><on>セイブツ</on></b><on>ブツリガク</on>",
        },
        id="A multi-kanji kanji_to_highlight highlights only where the whole run matches",
    ),
    pytest.param(
        "匂",
        # 匂 has no onyomi, 区 has no kunyomi
        "この 区域[くいき]は 匂[にお]いがする。",
        True,
        {
            "kana_only": "この クイキは <b>におい</b>がする。",
            "furigana": "この 区域[クイキ]は<b> 匂[にお]い</b>がする。",
            "furikanji": "この クイキ[区域]は<b> にお[匂]い</b>がする。",
            "kana_only split": "この <on>ク</on><on>イキ</on>は <b><kun>にお</kun><oku>い</oku></b>がする。",
            "furigana split": "この<on> 区[ク]</on><on> 域[イキ]</on>は<b><kun> 匂[にお]</kun><oku>い</oku></b>がする。",
            "furikanji split": "この<on> ク[区]</on><on> イキ[域]</on>は<b><kun> にお[匂]</kun><oku>い</oku></b>がする。",
            "kana_only merged": "この <on>クイキ</on>は <b><kun>にお</kun><oku>い</oku></b>がする。",
            "furigana merged": "この<on> 区域[クイキ]</on>は<b><kun> 匂[にお]</kun><oku>い</oku></b>がする。",
            "furikanji merged": "この<on> クイキ[区域]</on>は<b><kun> にお[匂]</kun><oku>い</oku></b>がする。",
        },
        id="Should not crash with kanji that has empty onyomi or kunyomi",
    ),
    pytest.param(
        # An exception word (薔薇) covers its own positions in juku_parts; the kanji before it
        # get theirs from the redistribution, which used to be skipped whenever the exception
        # had filled anything. ぽぽぽぽ was then dropped from the reading entirely.
        "",
        "栗栗薔薇[ぽぽぽぽばら]",
        True,
        {
            "furigana": " 栗栗薔薇[ぽぽぽぽばら]",
            "furigana split": "<juk> 栗[ぽぽ]</juk><juk> 栗[ぽぽ]</juk><juk> 薔[ば]</juk><juk> 薇[ら]</juk>",
            "furigana merged": "<juk> 栗栗薔薇[ぽぽぽぽばら]</juk>",
            "furikanji": " ぽぽぽぽばら[栗栗薔薇]",
            "furikanji split": "<juk> ぽぽ[栗]</juk><juk> ぽぽ[栗]</juk><juk> ば[薔]</juk><juk> ら[薇]</juk>",
            "furikanji merged": "<juk> ぽぽぽぽばら[栗栗薔薇]</juk>",
            "kana_only": "ぽぽぽぽばら",
            "kana_only split": "<juk>ぽぽ</juk><juk>ぽぽ</juk><juk>ば</juk><juk>ら</juk>",
            "kana_only merged": "<juk>ぽぽぽぽばら</juk>",
        },
        id="Should keep the mora of the kanji before an exception word",
    ),
    pytest.param(
        # Same gap, but after the exception instead of before it, so the leftover mora are the
        # tail of the reading rather than its head.
        "薔",
        "薔薇栗[ばらぽぽ]",
        True,
        {
            "furigana": "<b> 薔[ば]</b> 薇栗[らぽぽ]",
            "furigana split": "<b><juk> 薔[ば]</juk></b><juk> 薇[ら]</juk><juk> 栗[ぽぽ]</juk>",
            "furigana merged": "<b><juk> 薔[ば]</juk></b><juk> 薇栗[らぽぽ]</juk>",
            "furikanji": "<b> ば[薔]</b> らぽぽ[薇栗]",
            "furikanji split": "<b><juk> ば[薔]</juk></b><juk> ら[薇]</juk><juk> ぽぽ[栗]</juk>",
            "furikanji merged": "<b><juk> ば[薔]</juk></b><juk> らぽぽ[薇栗]</juk>",
            "kana_only": "<b>ば</b>らぽぽ",
            "kana_only split": "<b><juk>ば</juk></b><juk>ら</juk><juk>ぽぽ</juk>",
            "kana_only merged": "<b><juk>ば</juk></b><juk>らぽぽ</juk>",
        },
        id="Should keep the mora of the kanji after an exception word",
    ),
    pytest.param(
        # Both gaps at once: the exception sits in the middle, so its reading bounds an
        # unclaimed run on either side and neither may be dealt the other's mora.
        "",
        "栗薔薇栗[ぽぽばらぽぽ]",
        True,
        {
            "furigana": " 栗薔薇栗[ぽぽばらぽぽ]",
            "furigana split": "<juk> 栗[ぽぽ]</juk><juk> 薔[ば]</juk><juk> 薇[ら]</juk><juk> 栗[ぽぽ]</juk>",
            "furigana merged": "<juk> 栗薔薇栗[ぽぽばらぽぽ]</juk>",
            "furikanji": " ぽぽばらぽぽ[栗薔薇栗]",
            "furikanji split": "<juk> ぽぽ[栗]</juk><juk> ば[薔]</juk><juk> ら[薇]</juk><juk> ぽぽ[栗]</juk>",
            "furikanji merged": "<juk> ぽぽばらぽぽ[栗薔薇栗]</juk>",
            "kana_only": "ぽぽばらぽぽ",
            "kana_only split": "<juk>ぽぽ</juk><juk>ば</juk><juk>ら</juk><juk>ぽぽ</juk>",
            "kana_only merged": "<juk>ぽぽばらぽぽ</juk>",
        },
        id="Should keep the mora on both sides of an exception word",
    ),
    pytest.param(
        "",
        "今日[]は天気[てんき]がいい。",
        True,
        {
            # An empty reading would leave nothing at all, so kana_only shows the placeholder too
            "kana_only": "□はテンキがいい。",
            # Furigana can show the kanji with empty reading
            "furigana": "今日は 天気[テンキ]がいい。",
            # To hide the kanji with empty furigana, a placeholder is used
            "furikanji": " □[今日]は テンキ[天気]がいい。",
            # The placeholder gets the <err> tag as well
            "kana_only split": "<err>□</err>は<on>テン</on><on>キ</on>がいい。",
            "kana_only merged": "<err>□</err>は<on>テンキ</on>がいい。",
            # furigan/furikanji uses <err> tag for empty furigana
            "furigana split": "<err>今日</err>は<on> 天[テン]</on><on> 気[キ]</on>がいい。",
            "furigana merged": "<err>今日</err>は<on> 天気[テンキ]</on>がいい。",
            "furikanji split": "<err> □[今日]</err>は<on> テン[天]</on><on> キ[気]</on>がいい。",
            "furikanji merged": "<err> □[今日]</err>は<on> テンキ[天気]</on>がいい。",
        },
        id="Should gracefully handle empty furigana - no highlight",
    ),
    pytest.param(
        "今",
        "今日[]は天気[てんき]がいい。",
        True,
        {
            # Kana is the same as no highlight since the placeholder standing in for the missing
            # reading has nothing to bold, the same way the furikanji placeholder isn't bolded
            "kana_only": "□はテンキがいい。",
            "kana_only split": "<err>□</err>は<on>テン</on><on>キ</on>がいい。",
            "kana_only merged": "<err>□</err>は<on>テンキ</on>がいい。",
            # Furigana/furikanji highglights the kanji
            "furigana": "<b>今</b>日は 天気[テンキ]がいい。",
            "furikanji": " □[<b>今</b>日]は テンキ[天気]がいい。",
            "furigana split": "<err><b>今</b>日</err>は<on> 天[テン]</on><on> 気[キ]</on>がいい。",
            "furigana merged": "<err><b>今</b>日</err>は<on> 天気[テンキ]</on>がいい。",
            "furikanji split": "<err> □[<b>今</b>日]</err>は<on> テン[天]</on><on> キ[気]</on>がいい。",
            "furikanji merged": "<err> □[<b>今</b>日]</err>は<on> テンキ[天気]</on>がいい。",
        },
        id="Should gracefully handle empty furigana - with highlight",
    ),
    pytest.param(
        "",
        "漢字[kanji]の読[yo]mi方[kata]を学[mana]bu。",
        True,
        {
            # no tags in kana_only mode
            "kana_only": "kanjiのyomikataをmanabu。",
            "furigana": " 漢字[kanji]の 読[yo]mi 方[kata]を 学[mana]bu。",
            "furikanji": " kanji[漢字]の yo[読]mi kata[方]を mana[学]bu。",
            # all tags will be <err>
            "kana_only split": "<err>kanji</err>の<err>yo</err>mi<err>kata</err>を<err>mana</err>bu。",
            "kana_only merged": "<err>kanji</err>の<err>yo</err>mi<err>kata</err>を<err>mana</err>bu。",
            "furigana split": "<err> 漢字[kanji]</err>の<err> 読[yo]</err>mi<err> 方[kata]</err>を<err>"
            " 学[mana]</err>bu。",
            "furigana merged": "<err> 漢字[kanji]</err>の<err> 読[yo]</err>mi<err> 方[kata]</err>を<err>"
            " 学[mana]</err>bu。",
            "furikanji split": "<err> kanji[漢字]</err>の<err> yo[読]</err>mi<err> kata[方]</err>を<err>"
            " mana[学]</err>bu。",
            "furikanji merged": "<err> kanji[漢字]</err>の<err> yo[読]</err>mi<err> kata[方]</err>を<err>"
            " mana[学]</err>bu。",
        },
        id="All non-kana furigana should be preserved - no highlight",
    ),
    pytest.param(
        "漢",
        "漢字[kanji]の読[yo]mi方[kata]を学[mana]bu。",
        True,
        {
            "kana_only": "kanjiのyomikataをmanabu。",
            # Simple replacement of kanji with <b> regardless of where it's positioned, in top or bottom
            "furigana": " <b>漢</b>字[kanji]の 読[yo]mi 方[kata]を 学[mana]bu。",
            "furikanji": " kanji[<b>漢</b>字]の yo[読]mi kata[方]を mana[学]bu。",
            "kana_only split": "<err>kanji</err>の<err>yo</err>mi<err>kata</err>を<err>mana</err>bu。",
            "kana_only merged": "<err>kanji</err>の<err>yo</err>mi<err>kata</err>を<err>mana</err>bu。",
            "furigana split": "<err> <b>漢</b>字[kanji]</err>の<err> 読[yo]</err>mi<err> 方[kata]</err>を<err>"
            " 学[mana]</err>bu。",
            "furigana merged": "<err> <b>漢</b>字[kanji]</err>の<err> 読[yo]</err>mi<err> 方[kata]</err>を<err>"
            " 学[mana]</err>bu。",
            "furikanji split": "<err> kanji[<b>漢</b>字]</err>の<err> yo[読]</err>mi<err> kata[方]</err>を<err>"
            " mana[学]</err>bu。",
            "furikanji merged": "<err> kanji[<b>漢</b>字]</err>の<err> yo[読]</err>mi<err> kata[方]</err>を<err>"
            " mana[学]</err>bu。",
        },
        id="All non-kana furigana should be preserved - with highlight",
    ),
    pytest.param(
        "",
        # The bracket content is an Anki audio tag, not a reading. Rewriting it in any way would
        # break the audio, so the whole match is left exactly as it was in every return type.
        "漢字[sound:test.mp3]",
        True,
        {
            "kana_only": "漢字[sound:test.mp3]",
            "furigana": "漢字[sound:test.mp3]",
            "furikanji": "漢字[sound:test.mp3]",
            "kana_only split": "漢字[sound:test.mp3]",
            "kana_only merged": "漢字[sound:test.mp3]",
            "furigana split": "漢字[sound:test.mp3]",
            "furigana merged": "漢字[sound:test.mp3]",
            "furikanji split": "漢字[sound:test.mp3]",
            "furikanji merged": "漢字[sound:test.mp3]",
        },
        id="A [sound:...] tag in the brackets is not furigana - no highlight",
    ),
    pytest.param(
        # Kana in the file name must not be mistaken for a reading, and the kanji to highlight
        # sitting in front of the tag must not get a <b> either - nothing here is touched.
        "漢",
        "漢字[sound:かんじ.mp3]",
        True,
        {
            "kana_only": "漢字[sound:かんじ.mp3]",
            "furigana": "漢字[sound:かんじ.mp3]",
            "furikanji": "漢字[sound:かんじ.mp3]",
            "kana_only split": "漢字[sound:かんじ.mp3]",
            "kana_only merged": "漢字[sound:かんじ.mp3]",
            "furigana split": "漢字[sound:かんじ.mp3]",
            "furigana merged": "漢字[sound:かんじ.mp3]",
            "furikanji split": "漢字[sound:かんじ.mp3]",
            "furikanji merged": "漢字[sound:かんじ.mp3]",
        },
        id="A [sound:...] tag with kana in the file name is not read as furigana",
    ),
    pytest.param(
        "気",
        "天気[てんき]の 音[sound:おと.mp3]を 聞[き]く。",
        True,
        {
            "kana_only": "テン<b>キ</b>の 音[sound:おと.mp3]を きく。",
            "furigana": " 天[テン]<b> 気[キ]</b>の 音[sound:おと.mp3]を 聞[き]く。",
            "furikanji": " テン[天]<b> キ[気]</b>の 音[sound:おと.mp3]を き[聞]く。",
            "kana_only split": "<on>テン</on><b><on>キ</on></b>の 音[sound:おと.mp3]を <kun>き</kun><oku>く</oku>。",
            "kana_only merged": "<on>テン</on><b><on>キ</on></b>の 音[sound:おと.mp3]を <kun>き</kun><oku>く</oku>。",
            "furigana split": "<on> 天[テン]</on><b><on> 気[キ]</on></b>の 音[sound:おと.mp3]を<kun>"
            " 聞[き]</kun><oku>く</oku>。",
            "furigana merged": "<on> 天[テン]</on><b><on> 気[キ]</on></b>の 音[sound:おと.mp3]を<kun>"
            " 聞[き]</kun><oku>く</oku>。",
            "furikanji split": "<on> テン[天]</on><b><on> キ[気]</on></b>の 音[sound:おと.mp3]を<kun>"
            " き[聞]</kun><oku>く</oku>。",
            "furikanji merged": "<on> テン[天]</on><b><on> キ[気]</on></b>の 音[sound:おと.mp3]を<kun>"
            " き[聞]</kun><oku>く</oku>。",
        },
        id="A [sound:...] tag mixed into a sentence leaves the real furigana working",
    ),
    pytest.param(
        "",
        # 消え去[...]る would normally be split into 消[き]え去[さ]る; with a sound tag there is no
        # reading to split, so the word has to survive whole.
        "消え去[sound:test.mp3]る",
        True,
        {
            "kana_only": "消え去[sound:test.mp3]る",
            "furigana": "消え去[sound:test.mp3]る",
            "furikanji": "消え去[sound:test.mp3]る",
            "kana_only split": "消え去[sound:test.mp3]る",
            "kana_only merged": "消え去[sound:test.mp3]る",
            "furigana split": "消え去[sound:test.mp3]る",
            "furigana merged": "消え去[sound:test.mp3]る",
            "furikanji split": "消え去[sound:test.mp3]る",
            "furikanji merged": "消え去[sound:test.mp3]る",
        },
        id="A [sound:...] tag in a mixed okurigana word is left alone with its okurigana",
    ),
    pytest.param(
        # The highlighter leaves the caller's <b> where it is; only the word it highlights gets
        # a <b> of its own.
        "気",
        "<b>これは</b>天気[てんき]だ",
        True,
        {
            "furigana": "<b>これは</b> 天[テン]<b> 気[キ]</b>だ",
            "furigana split": "<b>これは</b><on> 天[テン]</on><b><on> 気[キ]</on></b>だ",
            "furigana merged": "<b>これは</b><on> 天[テン]</on><b><on> 気[キ]</on></b>だ",
            "furikanji": "<b>これは</b> テン[天]<b> キ[気]</b>だ",
            "furikanji split": "<b>これは</b><on> テン[天]</on><b><on> キ[気]</on></b>だ",
            "furikanji merged": "<b>これは</b><on> テン[天]</on><b><on> キ[気]</on></b>だ",
            "kana_only": "<b>これは</b>テン<b>キ</b>だ",
            "kana_only split": "<b>これは</b><on>テン</on><b><on>キ</on></b>だ",
            "kana_only merged": "<b>これは</b><on>テン</on><b><on>キ</on></b>だ",
        },
        id="A <b> tag around text with no furigana is left where it is",
    ),
    pytest.param(
        # A <b> the caller put around the highlighted word itself nests with the highlight's own
        # <b>, by design: the word is read and highlighted as usual inside it and the caller's
        # tag comes back out untouched. Giving text without <b> around the word, or living with
        # the nesting, is the caller's call.
        "気",
        "これは<b>天気[てんき]</b>だ",
        True,
        {
            "furigana": "これは<b> 天[テン]<b> 気[キ]</b></b>だ",
            "furigana split": "これは<b><on> 天[テン]</on><b><on> 気[キ]</on></b></b>だ",
            "furigana merged": "これは<b><on> 天[テン]</on><b><on> 気[キ]</on></b></b>だ",
            "furikanji": "これは<b> テン[天]<b> キ[気]</b></b>だ",
            "furikanji split": "これは<b><on> テン[天]</on><b><on> キ[気]</on></b></b>だ",
            "furikanji merged": "これは<b><on> テン[天]</on><b><on> キ[気]</on></b></b>だ",
            "kana_only": "これは<b>テン<b>キ</b></b>だ",
            "kana_only split": "これは<b><on>テン</on><b><on>キ</on></b></b>だ",
            "kana_only merged": "これは<b><on>テン</on><b><on>キ</on></b></b>だ",
        },
        id="A <b> tag the caller put around the highlighted word stays around it",
    ),
    pytest.param(
        "",
        "天気[てんき123]は良[い]いですね。",
        True,
        {
            "kana_only": "テンキはいいですね。",
            "furigana": " 天気[テンキ]は 良[い]いですね。",
            "furikanji": " テンキ[天気]は い[良]いですね。",
            "kana_only split": "<on>テン</on><on>キ</on>は<kun>い</kun><oku>い</oku>ですね。",
            "kana_only merged": "<on>テンキ</on>は<kun>い</kun><oku>い</oku>ですね。",
            "furigana split": "<on> 天[テン]</on><on> 気[キ]</on>は<kun> 良[い]</kun><oku>い</oku>ですね。",
            "furigana merged": "<on> 天気[テンキ]</on>は<kun> 良[い]</kun><oku>い</oku>ですね。",
            "furikanji split": "<on> テン[天]</on><on> キ[気]</on>は<kun> い[良]</kun><oku>い</oku>ですね。",
            "furikanji merged": "<on> テンキ[天気]</on>は<kun> い[良]</kun><oku>い</oku>ですね。",
        },
        id="Should ignore non-kana characters in furigana if there are also kana - no highlight",
    ),
    pytest.param(
        "歩",
        "歩道[ほどう123]を歩[bある]く。",
        True,
        {
            "kana_only": "<b>ホ</b>ドウを<b>あるく</b>。",
            "furigana": "<b> 歩[ホ]</b> 道[ドウ]を<b> 歩[ある]く</b>。",
            "furikanji": "<b> ホ[歩]</b> ドウ[道]を<b> ある[歩]く</b>。",
            "kana_only split": "<b><on>ホ</on></b><on>ドウ</on>を<b><kun>ある</kun><oku>く</oku></b>。",
            "kana_only merged": "<b><on>ホ</on></b><on>ドウ</on>を<b><kun>ある</kun><oku>く</oku></b>。",
            "furigana split": "<b><on> 歩[ホ]</on></b><on> 道[ドウ]</on>を<b><kun> 歩[ある]</kun><oku>く</oku></b>。",
            "furigana merged": "<b><on> 歩[ホ]</on></b><on> 道[ドウ]</on>を<b><kun> 歩[ある]</kun><oku>く</oku></b>。",
            "furikanji split": "<b><on> ホ[歩]</on></b><on> ドウ[道]</on>を<b><kun> ある[歩]</kun><oku>く</oku></b>。",
            "furikanji merged": "<b><on> ホ[歩]</on></b><on> ドウ[道]</on>を<b><kun> ある[歩]</kun><oku>く</oku></b>。",
        },
        id="Should ignore non-kana characters in furigana if there are also kana - with highlight",
    ),
    pytest.param(
        "",
        # This case would be due to incorrect furigana input
        "今日[きょ]",
        True,
        {
            "kana_only": "きょ",
            "furigana": " 今日[きょ]",
            "furikanji": " きょ[今日]",
            "kana_only split": "<juk>きょ</juk>",
            "furigana split": "<juk> 今日[きょ]</juk>",
            "furikanji split": "<juk> きょ[今日]</juk>",
            "kana_only merged": "<juk>きょ</juk>",
            "furigana merged": "<juk> 今日[きょ]</juk>",
            "furikanji merged": "<juk> きょ[今日]</juk>",
        },
        id="Should merge if furigana doesn't have enough mora for kanji - with highlight",
    ),
    pytest.param(
        "視",
        # しちょうしゃ　has し in it twice but only the first one should be highlighted
        "視聴者[しちょうしゃ]",
        True,
        {
            "kana_only": "<b>シ</b>チョウシャ",
            "furigana": "<b> 視[シ]</b> 聴者[チョウシャ]",
            "furikanji": "<b> シ[視]</b> チョウシャ[聴者]",
            "kana_only split": "<b><on>シ</on></b><on>チョウ</on><on>シャ</on>",
            "furigana split": "<b><on> 視[シ]</on></b><on> 聴[チョウ]</on><on> 者[シャ]</on>",
            "furikanji split": "<b><on> シ[視]</on></b><on> チョウ[聴]</on><on> シャ[者]</on>",
            "kana_only merged": "<b><on>シ</on></b><on>チョウシャ</on>",
            "furigana merged": "<b><on> 視[シ]</on></b><on> 聴者[チョウシャ]</on>",
            "furikanji merged": "<b><on> シ[視]</on></b><on> チョウシャ[聴者]</on>",
        },
        id="Should not incorrectly match onyomi twice 1/",
    ),
    pytest.param(
        "儀",
        # ぎょうぎ　has ぎ in it twice but only the first one should be highlighted
        "行儀[ぎょうぎ]",
        True,
        {
            "kana_only": "ギョウ<b>ギ</b>",
            "furigana": " 行[ギョウ]<b> 儀[ギ]</b>",
            "furikanji": " ギョウ[行]<b> ギ[儀]</b>",
            "kana_only split": "<on>ギョウ</on><b><on>ギ</on></b>",
            "furigana split": "<on> 行[ギョウ]</on><b><on> 儀[ギ]</on></b>",
            "furikanji split": "<on> ギョウ[行]</on><b><on> ギ[儀]</on></b>",
            "kana_only merged": "<on>ギョウ</on><b><on>ギ</on></b>",
            "furigana merged": "<on> 行[ギョウ]</on><b><on> 儀[ギ]</on></b>",
            "furikanji merged": "<on> ギョウ[行]</on><b><on> ギ[儀]</on></b>",
        },
        id="Should not incorrectly match onyomi twice 2/",
    ),
    pytest.param(
        "嗜",
        # the onyomi し occurs in the middle of the furigana but should not be matched
        "嗜[たしな]まれたことは？",
        True,
        {
            "kana_only": "<b>たしなまれた</b>ことは？",
            "furigana": "<b> 嗜[たしな]まれた</b>ことは？",
            "furikanji": "<b> たしな[嗜]まれた</b>ことは？",
            "kana_only split": "<b><kun>たしな</kun><oku>まれた</oku></b>ことは？",
            "furigana split": "<b><kun> 嗜[たしな]</kun><oku>まれた</oku></b>ことは？",
            "furikanji split": "<b><kun> たしな[嗜]</kun><oku>まれた</oku></b>ことは？",
            "kana_only merged": "<b><kun>たしな</kun><oku>まれた</oku></b>ことは？",
            "furigana merged": "<b><kun> 嗜[たしな]</kun><oku>まれた</oku></b>ことは？",
            "furikanji merged": "<b><kun> たしな[嗜]</kun><oku>まれた</oku></b>ことは？",
        },
        id="Should not match onyomi in whole edge match 1/",
    ),
    pytest.param(
        "悠",
        # the onyomi ユウ occurs twice in the furigana and should be matched both times
        "悠々[ゆうゆう]とした時間[じかん]。",
        True,
        {
            "kana_only": "<b>ユウユウ</b>としたジカン。",
            "furigana": "<b> 悠々[ユウユウ]</b>とした 時間[ジカン]。",
            "furikanji": "<b> ユウユウ[悠々]</b>とした ジカン[時間]。",
            "kana_only split": "<b><on>ユウユウ</on></b>とした<on>ジ</on><on>カン</on>。",
            "furigana split": "<b><on> 悠々[ユウユウ]</on></b>とした<on> 時[ジ]</on><on> 間[カン]</on>。",
            "furikanji split": "<b><on> ユウユウ[悠々]</on></b>とした<on> ジ[時]</on><on> カン[間]</on>。",
            "kana_only merged": "<b><on>ユウユウ</on></b>とした<on>ジカン</on>。",
            "furigana merged": "<b><on> 悠々[ユウユウ]</on></b>とした<on> 時間[ジカン]</on>。",
            "furikanji merged": "<b><on> ユウユウ[悠々]</on></b>とした<on> ジカン[時間]</on>。",
        },
        id="Should match onyomi twice in whole edge match 2/",
    ),
    pytest.param(
        "去",
        # 消え去[きえさ]った　has え in the middle but った at the end is not included in the furigana
        "団子[だんご]が 消え去[きえさ]った。",
        True,
        {
            "kana_only": "ダンごが きえ<b>さった</b>。",
            "furigana": " 団子[ダンご]が 消[き]え<b> 去[さ]った</b>。",
            "furikanji": " ダンご[団子]が き[消]え<b> さ[去]った</b>。",
            "kana_only split": "<on>ダン</on><kun>ご</kun>が"
            " <kun>き</kun><oku>え</oku><b><kun>さ</kun><oku>った</oku></b>。",
            "furigana split": "<on> 団[ダン]</on><kun> 子[ご]</kun>が<kun> 消[き]</kun><oku>え</oku><b><kun>"
            " 去[さ]</kun><oku>った</oku></b>。",
            "furikanji split": "<on> ダン[団]</on><kun> ご[子]</kun>が<kun> き[消]</kun><oku>え</oku><b><kun>"
            " さ[去]</kun><oku>った</oku></b>。",
            "kana_only merged": "<on>ダン</on><kun>ご</kun>が"
            " <kun>き</kun><oku>え</oku><b><kun>さ</kun><oku>った</oku></b>。",
            "furigana merged": "<on> 団[ダン]</on><kun> 子[ご]</kun>が<kun> 消[き]</kun><oku>え</oku><b><kun>"
            " 去[さ]</kun><oku>った</oku></b>。",
            "furikanji merged": "<on> ダン[団]</on><kun> ご[子]</kun>が<kun> き[消]</kun><oku>え</oku><b><kun>"
            " さ[去]</kun><oku>った</oku></b>。",
        },
        id="Should be able to clean furigana that bridges over some okurigana 1/",
    ),
    pytest.param(
        "隣",
        # 隣り合わせ[となりあわせ]のまち　has り　in the middle and わせ　at the end of the group
        "隣り合わせ[となりあわせ]の町[まち]。",
        True,
        {
            "kana_only": "<b>となり</b>あわせのまち。",
            "furigana": "<b> 隣[とな]り</b> 合[あ]わせの 町[まち]。",
            "furikanji": "<b> とな[隣]り</b> あ[合]わせの まち[町]。",
            "kana_only split": "<b><kun>とな</kun><oku>り</oku></b><kun>あ</kun><oku>わせ</oku>の<kun>まち</kun>。",
            "furigana split": "<b><kun> 隣[とな]</kun><oku>り</oku></b><kun> 合[あ]</kun><oku>わせ</oku>の"
            "<kun> 町[まち]</kun>。",
            "furikanji split": "<b><kun> とな[隣]</kun><oku>り</oku></b><kun> あ[合]</kun><oku>わせ</oku>の"
            "<kun> まち[町]</kun>。",
            "kana_only merged": "<b><kun>とな</kun><oku>り</oku></b><kun>あ</kun><oku>わせ</oku>の<kun>まち</kun>。",
            "furigana merged": "<b><kun> 隣[とな]</kun><oku>り</oku></b><kun> 合[あ]</kun><oku>わせ</oku>の"
            "<kun> 町[まち]</kun>。",
            "furikanji merged": "<b><kun> とな[隣]</kun><oku>り</oku></b><kun> あ[合]</kun><oku>わせ</oku>の"
            "<kun> まち[町]</kun>。",
        },
        id="Should be able to clean furigana that bridges over some okurigana 2/",
    ),
    pytest.param(
        "",
        # Can in fact use kana_highlight to generate correct furigana by simply putting the full kana
        # reading into brackets after text
        "見逃した映画をみる[みのがしたえいがをみる]",
        True,
        {
            "kana_only": "みのがしたエイガをみる",
            "furigana": " 見逃[みのが]した 映画[エイガ]をみる",
            "furikanji": " みのが[見逃]した エイガ[映画]をみる",
            "kana_only split": "<kun>み</kun><kun>のが</kun><oku>した</oku><on>エイ</on><on>ガ</on>をみる",
            "furigana split": "<kun> 見[み]</kun><kun> 逃[のが]</kun><oku>した</oku><on> 映[エイ]</on><on>"
            " 画[ガ]</on>をみる",
            "furikanji split": "<kun> み[見]</kun><kun> のが[逃]</kun><oku>した</oku><on> エイ[映]</on><on>"
            " ガ[画]</on>をみる",
            "kana_only merged": "<kun>みのが</kun><oku>した</oku><on>エイガ</on>をみる",
            "furigana merged": "<kun> 見逃[みのが]</kun><oku>した</oku><on> 映画[エイガ]</on>をみる",
            "furikanji merged": "<kun> みのが[見逃]</kun><oku>した</oku><on> エイガ[映画]</on>をみる",
        },
        id="Generates furigana for a whole phrase from its full reading in brackets",
    ),
    # A word opening with kana only gives that kana back when the kanji's own readings say it is
    # part of the word. A prefix test on its own could not tell お前[おまえ] from a particle at the
    # start of the text: か家族[かぞく] lost its first mora and came out as か <juk> 家族[ぞく]</juk>.
    pytest.param(
        "",
        "か家族[かぞく]と",
        True,
        {
            "furigana": "か 家族[カゾク]と",
            "furigana split": "か<on> 家[カ]</on><on> 族[ゾク]</on>と",
            "furigana merged": "か<on> 家族[カゾク]</on>と",
            "furikanji": "か カゾク[家族]と",
            "furikanji split": "か<on> カ[家]</on><on> ゾク[族]</on>と",
            "furikanji merged": "か<on> カゾク[家族]</on>と",
            "kana_only": "かカゾクと",
            "kana_only split": "か<on>カ</on><on>ゾク</on>と",
            "kana_only merged": "か<on>カゾク</on>と",
        },
        id="a particle opening the text is not eaten by the word after it",
    ),
    pytest.param(
        "家",
        "か家族[かぞく]と",
        True,
        {
            "furigana": "か<b> 家[カ]</b> 族[ゾク]と",
            "furigana split": "か<b><on> 家[カ]</on></b><on> 族[ゾク]</on>と",
            "furigana merged": "か<b><on> 家[カ]</on></b><on> 族[ゾク]</on>と",
            "furikanji": "か<b> カ[家]</b> ゾク[族]と",
            "furikanji split": "か<b><on> カ[家]</on></b><on> ゾク[族]</on>と",
            "furikanji merged": "か<b><on> カ[家]</on></b><on> ゾク[族]</on>と",
            "kana_only": "か<b>カ</b>ゾクと",
            "kana_only split": "か<b><on>カ</on></b><on>ゾク</on>と",
            "kana_only merged": "か<b><on>カ</on></b><on>ゾク</on>と",
        },
        id="a particle opening the text, with highlight",
    ),
    pytest.param(
        "",
        "が学校[がっこう]に",
        True,
        {
            "furigana": "が 学校[ガッコウ]に",
            "furigana split": "が<on> 学[ガッ]</on><on> 校[コウ]</on>に",
            "furigana merged": "が<on> 学校[ガッコウ]</on>に",
            "furikanji": "が ガッコウ[学校]に",
            "furikanji split": "が<on> ガッ[学]</on><on> コウ[校]</on>に",
            "furikanji merged": "が<on> ガッコウ[学校]</on>に",
            "kana_only": "がガッコウに",
            "kana_only split": "が<on>ガッ</on><on>コウ</on>に",
            "kana_only merged": "が<on>ガッコウ</on>に",
        },
        id="a particle opening the text, kanji with a sound change",
    ),
    pytest.param(
        "",
        "も紅葉[もみじ]が",
        True,
        {
            "furigana": "も 紅葉[もみじ]が",
            "furigana split": "も<juk> 紅[もみ]</juk><juk> 葉[じ]</juk>が",
            "furigana merged": "も<juk> 紅葉[もみじ]</juk>が",
            "furikanji": "も もみじ[紅葉]が",
            "furikanji split": "も<juk> もみ[紅]</juk><juk> じ[葉]</juk>が",
            "furikanji merged": "も<juk> もみじ[紅葉]</juk>が",
            "kana_only": "ももみじが",
            "kana_only split": "も<juk>もみ</juk><juk>じ</juk>が",
            "kana_only merged": "も<juk>もみじ</juk>が",
        },
        id="a particle opening the text before a jukujikun word",
    ),
    pytest.param(
        "前",
        "お前[おまえ]",
        True,
        {
            "furigana": "お<b> 前[まえ]</b>",
            "furigana split": "お<b><kun> 前[まえ]</kun></b>",
            "furigana merged": "お<b><kun> 前[まえ]</kun></b>",
            "furikanji": "お<b> まえ[前]</b>",
            "furikanji split": "お<b><kun> まえ[前]</kun></b>",
            "furikanji merged": "お<b><kun> まえ[前]</kun></b>",
            "kana_only": "お<b>まえ</b>",
            "kana_only split": "お<b><kun>まえ</kun></b>",
            "kana_only merged": "お<b><kun>まえ</kun></b>",
        },
        id="honorific opening the text is given back to it",
    ),
    pytest.param(
        "",
        "お土産[おみやげ]",
        True,
        {
            "furigana": "お 土産[みやげ]",
            "furigana split": "お<juk> 土[みや]</juk><juk> 産[げ]</juk>",
            "furigana merged": "お<juk> 土産[みやげ]</juk>",
            "furikanji": "お みやげ[土産]",
            "furikanji split": "お<juk> みや[土]</juk><juk> げ[産]</juk>",
            "furikanji merged": "お<juk> みやげ[土産]</juk>",
            "kana_only": "おみやげ",
            "kana_only split": "お<juk>みや</juk><juk>げ</juk>",
            "kana_only merged": "お<juk>みやげ</juk>",
        },
        id="honorific opening the text before a jukujikun word",
    ),
    pytest.param(
        "漢",
        "漢字読解[かんじどっかい]",
        True,
        {
            "kana_only": "<b>カン</b>ジドッカイ",
            "furigana": "<b> 漢[カン]</b> 字読解[ジドッカイ]",
            "furikanji": "<b> カン[漢]</b> ジドッカイ[字読解]",
            "kana_only split": "<b><on>カン</on></b><on>ジ</on><on>ドッ</on><on>カイ</on>",
            "furigana split": "<b><on> 漢[カン]</on></b><on> 字[ジ]</on><on> 読[ドッ]</on><on> 解[カイ]</on>",
            "furikanji split": "<b><on> カン[漢]</on></b><on> ジ[字]</on><on> ドッ[読]</on><on> カイ[解]</on>",
            "kana_only merged": "<b><on>カン</on></b><on>ジドッカイ</on>",
            "furigana merged": "<b><on> 漢[カン]</on></b><on> 字読解[ジドッカイ]</on>",
            "furikanji merged": "<b><on> カン[漢]</on></b><on> ジドッカイ[字読解]</on>",
        },
        id="Should work for 4-kanji word",
    ),
    pytest.param(
        "報",
        "情報処理技術者[じょうほうしょりぎじゅつしゃ]",
        True,
        {
            "kana_only": "ジョウ<b>ホウ</b>ショリギジュツシャ",
            "furigana": " 情[ジョウ]<b> 報[ホウ]</b> 処理技術者[ショリギジュツシャ]",
            "furikanji": " ジョウ[情]<b> ホウ[報]</b> ショリギジュツシャ[処理技術者]",
            "kana_only split": "<on>ジョウ</on><b><on>ホウ</on></b><on>ショ</on><on>リ</on><on>ギ</on><on>ジュツ</on><on>シャ</on>",
            "furigana split": "<on> 情[ジョウ]</on><b><on> 報[ホウ]</on></b><on> 処[ショ]</on><on> 理[リ]</on>"
            "<on> 技[ギ]</on><on> 術[ジュツ]</on><on> 者[シャ]</on>",
            "furikanji split": "<on> ジョウ[情]</on><b><on> ホウ[報]</on></b><on> ショ[処]</on><on> リ[理]</on>"
            "<on> ギ[技]</on><on> ジュツ[術]</on><on> シャ[者]</on>",
            "kana_only merged": "<on>ジョウ</on><b><on>ホウ</on></b><on>ショリギジュツシャ</on>",
            "furigana merged": "<on> 情[ジョウ]</on><b><on> 報[ホウ]</on></b><on> 処理技術者[ショリギジュツシャ]</on>",
            "furikanji merged": "<on> ジョウ[情]</on><b><on> ホウ[報]</on></b><on> ショリギジュツシャ[処理技術者]</on>",
        },
        id="Should work for 5-kanji word",
    ),
    pytest.param(
        "",
        " 愈々[いよいよ]",
        True,
        {
            "kana_only": " いよいよ",
            "furigana": " 愈々[いよいよ]",
            "furikanji": " いよいよ[愈々]",
            "kana_only split": " <kun>いよいよ</kun>",
            "furigana split": "<kun> 愈々[いよいよ]</kun>",
            "furikanji split": "<kun> いよいよ[愈々]</kun>",
            "kana_only merged": " <kun>いよいよ</kun>",
            "furigana merged": "<kun> 愈々[いよいよ]</kun>",
            "furikanji merged": "<kun> いよいよ[愈々]</kun>",
        },
        id="Kunyomi repeater word with no highlight /1",
    ),
    pytest.param(
        "",
        " 努々[ゆめゆめ]",
        True,
        {
            "kana_only": " ゆめゆめ",
            "furigana": " 努々[ゆめゆめ]",
            "furikanji": " ゆめゆめ[努々]",
            "kana_only split": " <kun>ゆめゆめ</kun>",
            "furigana split": "<kun> 努々[ゆめゆめ]</kun>",
            "furikanji split": "<kun> ゆめゆめ[努々]</kun>",
            "kana_only merged": " <kun>ゆめゆめ</kun>",
            "furigana merged": "<kun> 努々[ゆめゆめ]</kun>",
            "furikanji merged": "<kun> ゆめゆめ[努々]</kun>",
        },
        id="Kunyomi repeater word with no highlight /2",
    ),
    pytest.param(
        "彼",
        "我々[われわれ]",
        True,
        {
            "kana_only": "われわれ",
            "furigana": " 我々[われわれ]",
            "furikanji": " われわれ[我々]",
            "kana_only split": "<kun>われわれ</kun>",
            "furigana split": "<kun> 我々[われわれ]</kun>",
            "furikanji split": "<kun> われわれ[我々]</kun>",
            "kana_only merged": "<kun>われわれ</kun>",
            "furigana merged": "<kun> 我々[われわれ]</kun>",
            "furikanji merged": "<kun> われわれ[我々]</kun>",
        },
        id="Repeater word with another kanji as highlight",
    ),
    pytest.param(
        "",
        "<gikun> 清々[すっきり]する</gikun>",
        True,
        {
            "kana_only": "<gikun> すっきりする</gikun>",
            "furigana": "<gikun> 清々[すっきり]する</gikun>",
            "furikanji": "<gikun> すっきり[清々]する</gikun>",
            "kana_only split": "<gikun> <juk>すっきり</juk><oku>する</oku></gikun>",
            "furigana split": "<gikun><juk> 清々[すっきり]</juk><oku>する</oku></gikun>",
            "furikanji split": "<gikun><juk> すっきり[清々]</juk><oku>する</oku></gikun>",
            "kana_only merged": "<gikun> <juk>すっきり</juk><oku>する</oku></gikun>",
            "furigana merged": "<gikun><juk> 清々[すっきり]</juk><oku>する</oku></gikun>",
            "furikanji merged": "<gikun><juk> すっきり[清々]</juk><oku>する</oku></gikun>",
        },
        id="Jukujikun repeater word with no repeating furigana with no highlight",
    ),
    pytest.param(
        "",
        " 斯々然々[かくかくしかじか]",
        True,
        {
            "kana_only": " かくかくしかじか",
            "furigana": " 斯々然々[かくかくしかじか]",
            "furikanji": " かくかくしかじか[斯々然々]",
            "kana_only split": " <kun>かくかく</kun><kun>しかじか</kun>",
            "furigana split": "<kun> 斯々[かくかく]</kun><kun> 然々[しかじか]</kun>",
            "furikanji split": "<kun> かくかく[斯々]</kun><kun> しかじか[然々]</kun>",
            "kana_only merged": " <kun>かくかくしかじか</kun>",
            "furigana merged": "<kun> 斯々然々[かくかくしかじか]</kun>",
            "furikanji merged": "<kun> かくかくしかじか[斯々然々]</kun>",
        },
        id="Should match 斯斯 as kunyomi in 斯斯然然 - no highlight",
    ),
    pytest.param(
        "斯",
        " 斯々然々[かくかくしかじか]",
        True,
        {
            "kana_only": " <b>かくかく</b>しかじか",
            "furigana": "<b> 斯々[かくかく]</b> 然々[しかじか]",
            "furikanji": "<b> かくかく[斯々]</b> しかじか[然々]",
            "kana_only split": " <b><kun>かくかく</kun></b><kun>しかじか</kun>",
            "furigana split": "<b><kun> 斯々[かくかく]</kun></b><kun> 然々[しかじか]</kun>",
            "furikanji split": "<b><kun> かくかく[斯々]</kun></b><kun> しかじか[然々]</kun>",
            "kana_only merged": " <b><kun>かくかく</kun></b><kun>しかじか</kun>",
            "furigana merged": "<b><kun> 斯々[かくかく]</kun></b><kun> 然々[しかじか]</kun>",
            "furikanji merged": "<b><kun> かくかく[斯々]</kun></b><kun> しかじか[然々]</kun>",
        },
        id="Should match 斯斯 as kunyomi in 斯斯然然 - with highlight",
    ),
    pytest.param(
        "婦",
        "新婦[しんぷ]",
        True,
        {
            "kana_only": "シン<b>プ</b>",
            "furigana": " 新[シン]<b> 婦[プ]</b>",
            "furikanji": " シン[新]<b> プ[婦]</b>",
            "kana_only split": "<on>シン</on><b><on>プ</on></b>",
            "furigana split": "<on> 新[シン]</on><b><on> 婦[プ]</on></b>",
            "furikanji split": "<on> シン[新]</on><b><on> プ[婦]</on></b>",
            "kana_only merged": "<on>シン</on><b><on>プ</on></b>",
            "furigana merged": "<on> 新[シン]</on><b><on> 婦[プ]</on></b>",
            "furikanji merged": "<on> シン[新]</on><b><on> プ[婦]</on></b>",
        },
        id="Rendaku test 1/",
    ),
    pytest.param(
        "各",
        "各々[おのおの]",
        True,
        {
            "kana_only": "<b>おのおの</b>",
            "furigana": "<b> 各々[おのおの]</b>",
            "furikanji": "<b> おのおの[各々]</b>",
            "kana_only split": "<b><kun>おのおの</kun></b>",
            "furigana split": "<b><kun> 各々[おのおの]</kun></b>",
            "furikanji split": "<b><kun> おのおの[各々]</kun></b>",
            "kana_only merged": "<b><kun>おのおの</kun></b>",
            "furigana merged": "<b><kun> 各々[おのおの]</kun></b>",
            "furikanji merged": "<b><kun> おのおの[各々]</kun></b>",
        },
        id="Matches repeater word with kunyomi matching the whole word",
    ),
    pytest.param(
        "国",
        "国々[くにぐに]の 関係[かんけい]が 深い[ふかい]。",
        True,
        {
            "kana_only": "<b>くにぐに</b>の カンケイが ふかい。",
            "furigana": "<b> 国々[くにぐに]</b>の 関係[カンケイ]が 深[ふか]い。",
            "furikanji": "<b> くにぐに[国々]</b>の カンケイ[関係]が ふか[深]い。",
            "kana_only split": "<b><kun>くにぐに</kun></b>の <on>カン</on><on>ケイ</on>が <kun>ふか</kun><oku>い</oku>。",
            "furigana split": "<b><kun> 国々[くにぐに]</kun></b>の<on> 関[カン]</on><on>"
            " 係[ケイ]</on>が<kun> 深[ふか]</kun><oku>い</oku>。",
            "furikanji split": "<b><kun> くにぐに[国々]</kun></b>の<on> カン[関]</on><on>"
            " ケイ[係]</on>が<kun> ふか[深]</kun><oku>い</oku>。",
            "kana_only merged": "<b><kun>くにぐに</kun></b>の <on>カンケイ</on>が <kun>ふか</kun><oku>い</oku>。",
            "furigana merged": "<b><kun> 国々[くにぐに]</kun></b>の<on> 関係[カンケイ]</on>が<kun>"
            " 深[ふか]</kun><oku>い</oku>。",
            "furikanji merged": "<b><kun> くにぐに[国々]</kun></b>の<on> カンケイ[関係]</on>が<kun>"
            " ふか[深]</kun><oku>い</oku>。",
        },
        id="Matches word that uses the repeater 々 with rendaku 1/",
    ),
    pytest.param(
        "時",
        "時々[ときどき] 雨[あめ]が 降る[ふる]。",
        True,
        {
            "kana_only": "<b>ときどき</b> あめが ふる。",
            "furigana": "<b> 時々[ときどき]</b> 雨[あめ]が 降[ふ]る。",
            "furikanji": "<b> ときどき[時々]</b> あめ[雨]が ふ[降]る。",
            "kana_only split": "<b><kun>ときどき</kun></b> <kun>あめ</kun>が <kun>ふ</kun><oku>る</oku>。",
            "furigana split": "<b><kun> 時々[ときどき]</kun></b><kun> 雨[あめ]</kun>が<kun> 降[ふ]</kun><oku>る</oku>。",
            "furikanji split": "<b><kun> ときどき[時々]</kun></b><kun> あめ[雨]</kun>が<kun> ふ[降]</kun><oku>る</oku>。",
            "kana_only merged": "<b><kun>ときどき</kun></b> <kun>あめ</kun>が <kun>ふ</kun><oku>る</oku>。",
            "furigana merged": "<b><kun> 時々[ときどき]</kun></b><kun> 雨[あめ]</kun>が<kun> 降[ふ]</kun><oku>る</oku>。",
            "furikanji merged": "<b><kun> ときどき[時々]</kun></b><kun> あめ[雨]</kun>が<kun> ふ[降]</kun><oku>る</oku>。",
        },
        id="Matches word that uses the repeater 々 with rendaku 2/",
    ),
    pytest.param(
        "云",
        "云々[うんぬん]",
        True,
        {
            "kana_only": "<b>ウンヌン</b>",
            "furigana": "<b> 云々[ウンヌン]</b>",
            "furikanji": "<b> ウンヌン[云々]</b>",
            "kana_only split": "<b><on>ウンヌン</on></b>",
            "furigana split": "<b><on> 云々[ウンヌン]</on></b>",
            "furikanji split": "<b><on> ウンヌン[云々]</on></b>",
            "kana_only merged": "<b><on>ウンヌン</on></b>",
            "furigana merged": "<b><on> 云々[ウンヌン]</on></b>",
            "furikanji merged": "<b><on> ウンヌン[云々]</on></b>",
        },
        id="Matches word that uses the repeater 々 with rendaku 3/",
    ),
    pytest.param(
        "菜",
        "娃々菜[わわさい]",
        True,
        {
            "kana_only": "ワワ<b>サイ</b>",
            "furigana": " 娃々[ワワ]<b> 菜[サイ]</b>",
            "furikanji": " ワワ[娃々]<b> サイ[菜]</b>",
            "kana_only split": "<on>ワワ</on><b><on>サイ</on></b>",
            "furigana split": "<on> 娃々[ワワ]</on><b><on> 菜[サイ]</on></b>",
            "furikanji split": "<on> ワワ[娃々]</on><b><on> サイ[菜]</on></b>",
            "kana_only merged": "<on>ワワ</on><b><on>サイ</on></b>",
            "furigana merged": "<on> 娃々[ワワ]</on><b><on> 菜[サイ]</on></b>",
            "furikanji merged": "<on> ワワ[娃々]</on><b><on> サイ[菜]</on></b>",
        },
        id="Matches repeater in the middle of the word from left edge",
    ),
    pytest.param(
        "奄",
        "気息奄々[きそくえんえん]",
        True,
        {
            "kana_only": "キソク<b>エンエン</b>",
            "furigana": " 気息[キソク]<b> 奄々[エンエン]</b>",
            "furikanji": " キソク[気息]<b> エンエン[奄々]</b>",
            "kana_only split": "<on>キ</on><on>ソク</on><b><on>エンエン</on></b>",
            "furigana split": "<on> 気[キ]</on><on> 息[ソク]</on><b><on> 奄々[エンエン]</on></b>",
            "furikanji split": "<on> キ[気]</on><on> ソク[息]</on><b><on> エンエン[奄々]</on></b>",
            "kana_only merged": "<on>キソク</on><b><on>エンエン</on></b>",
            "furigana merged": "<on> 気息[キソク]</on><b><on> 奄々[エンエン]</on></b>",
            "furikanji merged": "<on> キソク[気息]</on><b><on> エンエン[奄々]</on></b>",
        },
        id="Matches repeater in the middle of the word from right edge",
    ),
    pytest.param(
        "侃",
        "熱々侃々諤々[あつあつかんかんがくがく]",
        True,
        {
            "kana_only": "あつあつ<b>カンカン</b>ガクガク",
            "furigana": " 熱々[あつあつ]<b> 侃々[カンカン]</b> 諤々[ガクガク]",
            "furikanji": " あつあつ[熱々]<b> カンカン[侃々]</b> ガクガク[諤々]",
            "kana_only split": "<kun>あつあつ</kun><b><on>カンカン</on></b><on>ガクガク</on>",
            "furigana split": "<kun> 熱々[あつあつ]</kun><b><on> 侃々[カンカン]</on></b><on> 諤々[ガクガク]</on>",
            "furikanji split": "<kun> あつあつ[熱々]</kun><b><on> カンカン[侃々]</on></b><on> ガクガク[諤々]</on>",
            "kana_only merged": "<kun>あつあつ</kun><b><on>カンカン</on></b><on>ガクガク</on>",
            "furigana merged": "<kun> 熱々[あつあつ]</kun><b><on> 侃々[カンカン]</on></b><on> 諤々[ガクガク]</on>",
            "furikanji merged": "<kun> あつあつ[熱々]</kun><b><on> カンカン[侃々]</on></b><on> ガクガク[諤々]</on>",
        },
        id="Matches repeater in the middle of the word from middle edge",
    ),
    pytest.param(
        "刻",
        "刻々[こっこく]と 変化[へんか]する。",
        True,
        {
            "kana_only": "<b>コッコク</b>と ヘンカする。",
            "furigana": "<b> 刻々[コッコク]</b>と 変化[ヘンカ]する。",
            "furikanji": "<b> コッコク[刻々]</b>と ヘンカ[変化]する。",
            "kana_only split": "<b><on>コッコク</on></b>と <on>ヘン</on><on>カ</on><oku>する</oku>。",
            "furigana split": "<b><on> 刻々[コッコク]</on></b>と<on> 変[ヘン]</on><on> 化[カ]</on><oku>する</oku>。",
            "furikanji split": "<b><on> コッコク[刻々]</on></b>と<on> ヘン[変]</on><on> カ[化]</on><oku>する</oku>。",
            "kana_only merged": "<b><on>コッコク</on></b>と <on>ヘンカ</on><oku>する</oku>。",
            "furigana merged": "<b><on> 刻々[コッコク]</on></b>と<on> 変化[ヘンカ]</on><oku>する</oku>。",
            "furikanji merged": "<b><on> コッコク[刻々]</on></b>と<on> ヘンカ[変化]</on><oku>する</oku>。",
        },
        id="Matches word that uses the repeater 々 with small tsu",
    ),
    pytest.param(
        "瑞",
        "瑞々[みずみず]しく",
        True,
        {
            "kana_only": "<b>みずみずしく</b>",
            "furigana": "<b> 瑞々[みずみず]しく</b>",
            "furikanji": "<b> みずみず[瑞々]しく</b>",
            "kana_only split": "<b><kun>みずみず</kun><oku>しく</oku></b>",
            "furigana split": "<b><kun> 瑞々[みずみず]</kun><oku>しく</oku></b>",
            "furikanji split": "<b><kun> みずみず[瑞々]</kun><oku>しく</oku></b>",
            "kana_only merged": "<b><kun>みずみず</kun><oku>しく</oku></b>",
            "furigana merged": "<b><kun> 瑞々[みずみず]</kun><oku>しく</oku></b>",
            "furikanji merged": "<b><kun> みずみず[瑞々]</kun><oku>しく</oku></b>",
        },
        id="Matches repeater adjective 瑞々しい - with highlight",
    ),
    pytest.param(
        "",
        "瑞々[みずみず]しさ",
        True,
        {
            "kana_only": "みずみずしさ",
            "furigana": " 瑞々[みずみず]しさ",
            "furikanji": " みずみず[瑞々]しさ",
            "kana_only split": "<kun>みずみず</kun><oku>しさ</oku>",
            "furigana split": "<kun> 瑞々[みずみず]</kun><oku>しさ</oku>",
            "furikanji split": "<kun> みずみず[瑞々]</kun><oku>しさ</oku>",
            "kana_only merged": "<kun>みずみず</kun><oku>しさ</oku>",
            "furigana merged": "<kun> 瑞々[みずみず]</kun><oku>しさ</oku>",
            "furikanji merged": "<kun> みずみず[瑞々]</kun><oku>しさ</oku>",
        },
        id="Matches repeater adjective 瑞々しい - no highlight",
    ),
    pytest.param(
        "瑞",
        "超瑞々[ちょうみずみず]しい",
        True,
        {
            "kana_only": "チョウ<b>みずみずしい</b>",
            "furigana": " 超[チョウ]<b> 瑞々[みずみず]しい</b>",
            "furikanji": " チョウ[超]<b> みずみず[瑞々]しい</b>",
            "kana_only split": "<on>チョウ</on><b><kun>みずみず</kun><oku>しい</oku></b>",
            "furigana split": "<on> 超[チョウ]</on><b><kun> 瑞々[みずみず]</kun><oku>しい</oku></b>",
            "furikanji split": "<on> チョウ[超]</on><b><kun> みずみず[瑞々]</kun><oku>しい</oku></b>",
            "kana_only merged": "<on>チョウ</on><b><kun>みずみず</kun><oku>しい</oku></b>",
            "furigana merged": "<on> 超[チョウ]</on><b><kun> 瑞々[みずみず]</kun><oku>しい</oku></b>",
            "furikanji merged": "<on> チョウ[超]</on><b><kun> みずみず[瑞々]</kun><oku>しい</oku></b>",
        },
        id="Matches repeater adjective with other word - with highlight",
    ),
    pytest.param(
        "",
        "超瑞々[ちょうみずみず]しい",
        True,
        {
            "kana_only": "チョウみずみずしい",
            "furigana": " 超瑞々[チョウみずみず]しい",
            "furikanji": " チョウみずみず[超瑞々]しい",
            "kana_only split": "<on>チョウ</on><kun>みずみず</kun><oku>しい</oku>",
            "furigana split": "<on> 超[チョウ]</on><kun> 瑞々[みずみず]</kun><oku>しい</oku>",
            "furikanji split": "<on> チョウ[超]</on><kun> みずみず[瑞々]</kun><oku>しい</oku>",
            "kana_only merged": "<on>チョウ</on><kun>みずみず</kun><oku>しい</oku>",
            "furigana merged": "<on> 超[チョウ]</on><kun> 瑞々[みずみず]</kun><oku>しい</oku>",
            "furikanji merged": "<on> チョウ[超]</on><kun> みずみず[瑞々]</kun><oku>しい</oku>",
        },
        id="Matches repeater adjective with other word - no highlight",
    ),
    pytest.param(
        "瑞",
        "精々瑞々[せいせいみずみず]しい",
        True,
        {
            "kana_only": "セイセイ<b>みずみずしい</b>",
            "furigana": " 精々[セイセイ]<b> 瑞々[みずみず]しい</b>",
            "furikanji": " セイセイ[精々]<b> みずみず[瑞々]しい</b>",
            "kana_only split": "<on>セイセイ</on><b><kun>みずみず</kun><oku>しい</oku></b>",
            "furigana split": "<on> 精々[セイセイ]</on><b><kun> 瑞々[みずみず]</kun><oku>しい</oku></b>",
            "furikanji split": "<on> セイセイ[精々]</on><b><kun> みずみず[瑞々]</kun><oku>しい</oku></b>",
            "kana_only merged": "<on>セイセイ</on><b><kun>みずみず</kun><oku>しい</oku></b>",
            "furigana merged": "<on> 精々[セイセイ]</on><b><kun> 瑞々[みずみず]</kun><oku>しい</oku></b>",
            "furikanji merged": "<on> セイセイ[精々]</on><b><kun> みずみず[瑞々]</kun><oku>しい</oku></b>",
        },
        id="Matches repeater adjective with other repeater word - with highlight",
    ),
    pytest.param(
        "",
        "精々瑞々[せいせいみずみず]しい",
        True,
        {
            "kana_only": "セイセイみずみずしい",
            "furigana": " 精々瑞々[セイセイみずみず]しい",
            "furikanji": " セイセイみずみず[精々瑞々]しい",
            "kana_only split": "<on>セイセイ</on><kun>みずみず</kun><oku>しい</oku>",
            "furigana split": "<on> 精々[セイセイ]</on><kun> 瑞々[みずみず]</kun><oku>しい</oku>",
            "furikanji split": "<on> セイセイ[精々]</on><kun> みずみず[瑞々]</kun><oku>しい</oku>",
            "kana_only merged": "<on>セイセイ</on><kun>みずみず</kun><oku>しい</oku>",
            "furigana merged": "<on> 精々[セイセイ]</on><kun> 瑞々[みずみず]</kun><oku>しい</oku>",
            "furikanji merged": "<on> セイセイ[精々]</on><kun> みずみず[瑞々]</kun><oku>しい</oku>",
        },
        id="Matches repeater adjective with other repeater word - no highlight",
    ),
    pytest.param(
        "猛",
        "猛々[たけだけ]しい",
        True,
        {
            "kana_only": "<b>たけだけしい</b>",
            "furigana": "<b> 猛々[たけだけ]しい</b>",
            "furikanji": "<b> たけだけ[猛々]しい</b>",
            "kana_only split": "<b><kun>たけだけ</kun><oku>しい</oku></b>",
            "furigana split": "<b><kun> 猛々[たけだけ]</kun><oku>しい</oku></b>",
            "furikanji split": "<b><kun> たけだけ[猛々]</kun><oku>しい</oku></b>",
            "kana_only merged": "<b><kun>たけだけ</kun><oku>しい</oku></b>",
            "furigana merged": "<b><kun> 猛々[たけだけ]</kun><oku>しい</oku></b>",
            "furikanji merged": "<b><kun> たけだけ[猛々]</kun><oku>しい</oku></b>",
        },
        id="Matches rendaku containing repeater adjective 猛々しい - with highlight",
    ),
    pytest.param(
        "",
        "猛猛[たけだけ]しい",
        True,
        {
            "kana_only": "たけだけしい",
            "furigana": " 猛々[たけだけ]しい",
            "furikanji": " たけだけ[猛々]しい",
            "kana_only split": "<kun>たけだけ</kun><oku>しい</oku>",
            "furigana split": "<kun> 猛々[たけだけ]</kun><oku>しい</oku>",
            "furikanji split": "<kun> たけだけ[猛々]</kun><oku>しい</oku>",
            "kana_only merged": "<kun>たけだけ</kun><oku>しい</oku>",
            "furigana merged": "<kun> 猛々[たけだけ]</kun><oku>しい</oku>",
            "furikanji merged": "<kun> たけだけ[猛々]</kun><oku>しい</oku>",
        },
        id="Matches rendaku containing repeater adjective 猛々しい - no highlight",
    ),
    pytest.param(
        # 生物 + 物理学, so the doubled 物 is two words meeting, not a repeater: it must stay
        # spelled out and keep a tag each, unlike the 猛猛 above where the reading rendakus
        "",
        "生物物理学[せいぶつぶつりがく]",
        True,
        {
            "kana_only": "セイブツブツリガク",
            "furigana": " 生物物理学[セイブツブツリガク]",
            "furikanji": " セイブツブツリガク[生物物理学]",
            "kana_only split": "<on>セイ</on><on>ブツ</on><on>ブツ</on><on>リ</on><on>ガク</on>",
            "furigana split": "<on> 生[セイ]</on><on> 物[ブツ]</on><on> 物[ブツ]</on><on> 理[リ]</on><on> 学[ガク]</on>",
            "furikanji split": "<on> セイ[生]</on><on> ブツ[物]</on><on> ブツ[物]</on><on> リ[理]</on><on> ガク[学]</on>",
            "kana_only merged": "<on>セイブツブツリガク</on>",
            "furigana merged": "<on> 生物物理学[セイブツブツリガク]</on>",
            "furikanji merged": "<on> セイブツブツリガク[生物物理学]</on>",
        },
        id="Keeps a kanji doubled across a word boundary spelled out",
    ),
    pytest.param(
        # 毎月 + 月末, so the second 月 reads げつ where the first reads つき: the second
        # occurrence is matched on its own readings instead of copying the first one's
        "",
        "毎月月末[まいつきげつまつ]",
        True,
        {
            "kana_only": "マイつきゲツマツ",
            "furigana": " 毎月月末[マイつきゲツマツ]",
            "furikanji": " マイつきゲツマツ[毎月月末]",
            "kana_only split": "<on>マイ</on><kun>つき</kun><on>ゲツ</on><on>マツ</on>",
            "furigana split": "<on> 毎[マイ]</on><kun> 月[つき]</kun><on> 月[ゲツ]</on><on> 末[マツ]</on>",
            "furikanji split": "<on> マイ[毎]</on><kun> つき[月]</kun><on> ゲツ[月]</on><on> マツ[末]</on>",
            "kana_only merged": "<on>マイ</on><kun>つき</kun><on>ゲツマツ</on>",
            "furigana merged": "<on> 毎[マイ]</on><kun> 月[つき]</kun><on> 月末[ゲツマツ]</on>",
            "furikanji merged": "<on> マイ[毎]</on><kun> つき[月]</kun><on> ゲツマツ[月末]</on>",
        },
        id="Reads a kanji doubled across a word boundary as kun then on - 毎月月末",
    ),
    pytest.param(
        # The same with 毎年 + 年末: とし then ねん
        "",
        "毎年年末[まいとしねんまつ]",
        True,
        {
            "kana_only": "マイとしネンマツ",
            "furigana": " 毎年年末[マイとしネンマツ]",
            "furikanji": " マイとしネンマツ[毎年年末]",
            "kana_only split": "<on>マイ</on><kun>とし</kun><on>ネン</on><on>マツ</on>",
            "furigana split": "<on> 毎[マイ]</on><kun> 年[とし]</kun><on> 年[ネン]</on><on> 末[マツ]</on>",
            "furikanji split": "<on> マイ[毎]</on><kun> とし[年]</kun><on> ネン[年]</on><on> マツ[末]</on>",
            "kana_only merged": "<on>マイ</on><kun>とし</kun><on>ネンマツ</on>",
            "furigana merged": "<on> 毎[マイ]</on><kun> 年[とし]</kun><on> 年末[ネンマツ]</on>",
            "furikanji merged": "<on> マイ[毎]</on><kun> とし[年]</kun><on> ネンマツ[年末]</on>",
        },
        id="Reads a kanji doubled across a word boundary as kun then on - 毎年年末",
    ),
    pytest.param(
        # A genuine doubled word written out: びと is ひと rendakued, which is evidence of a
        # repeater, so it is written back as 人々
        "",
        "人人[ひとびと]",
        True,
        {
            "kana_only": "ひとびと",
            "furigana": " 人々[ひとびと]",
            "furikanji": " ひとびと[人々]",
            "kana_only split": "<kun>ひとびと</kun>",
            "furigana split": "<kun> 人々[ひとびと]</kun>",
            "furikanji split": "<kun> ひとびと[人々]</kun>",
            "kana_only merged": "<kun>ひとびと</kun>",
            "furigana merged": "<kun> 人々[ひとびと]</kun>",
            "furikanji merged": "<kun> ひとびと[人々]</kun>",
        },
        id="Keeps a doubled word whose second reading rendakus - 人人",
    ),
    pytest.param(
        # 各 only lists the doubled reading おのおの, so the second おの matches nothing on its
        # own and falls back to a copy of the first match
        "",
        "各各[おのおの]",
        True,
        {
            "kana_only": "おのおの",
            "furigana": " 各各[おのおの]",
            "furikanji": " おのおの[各各]",
            "kana_only split": "<kun>おの</kun><kun>おの</kun>",
            "furigana split": "<kun> 各[おの]</kun><kun> 各[おの]</kun>",
            "furikanji split": "<kun> おの[各]</kun><kun> おの[各]</kun>",
            "kana_only merged": "<kun>おのおの</kun>",
            "furigana merged": "<kun> 各各[おのおの]</kun>",
            "furikanji merged": "<kun> おのおの[各各]</kun>",
        },
        id="Keeps a doubled word that only lists the doubled reading - 各各",
    ),
    pytest.param(
        # Both 物 are the kanji being studied, so both get highlighted, even though they belong
        # to different words. Being adjacent, they highlight as one run under a single <b>.
        "物",
        "生物物理学[せいぶつぶつりがく]",
        True,
        {
            "kana_only": "セイ<b>ブツブツ</b>リガク",
            "furigana": " 生[セイ]<b> 物物[ブツブツ]</b> 理学[リガク]",
            "furikanji": " セイ[生]<b> ブツブツ[物物]</b> リガク[理学]",
            "kana_only split": "<on>セイ</on><b><on>ブツ</on><on>ブツ</on></b><on>リ</on><on>ガク</on>",
            "furigana split": "<on> 生[セイ]</on><b><on> 物[ブツ]</on><on> 物[ブツ]</on></b><on> 理[リ]</on><on>"
            " 学[ガク]</on>",
            "furikanji split": "<on> セイ[生]</on><b><on> ブツ[物]</on><on> ブツ[物]</on></b><on> リ[理]</on><on>"
            " ガク[学]</on>",
            "kana_only merged": "<on>セイ</on><b><on>ブツブツ</on></b><on>リガク</on>",
            "furigana merged": "<on> 生[セイ]</on><b><on> 物物[ブツブツ]</on></b><on> 理学[リガク]</on>",
            "furikanji merged": "<on> セイ[生]</on><b><on> ブツブツ[物物]</on></b><on> リガク[理学]</on>",
        },
        id="Highlights both halves of a kanji doubled across a word boundary",
    ),
    pytest.param(
        # The same rule with the occurrences apart rather than adjacent: each gets its own <b>,
        # and the 民 between them stays outside both
        "国",
        "国民国家[こくみんこっか]",
        True,
        {
            "kana_only": "<b>コク</b>ミン<b>コッ</b>カ",
            "furigana": "<b> 国[コク]</b> 民[ミン]<b> 国[コッ]</b> 家[カ]",
            "furikanji": "<b> コク[国]</b> ミン[民]<b> コッ[国]</b> カ[家]",
            "kana_only split": "<b><on>コク</on></b><on>ミン</on><b><on>コッ</on></b><on>カ</on>",
            "furigana split": "<b><on> 国[コク]</on></b><on> 民[ミン]</on><b><on> 国[コッ]</on></b><on> 家[カ]</on>",
            "furikanji split": "<b><on> コク[国]</on></b><on> ミン[民]</on><b><on> コッ[国]</on></b><on> カ[家]</on>",
            "kana_only merged": "<b><on>コク</on></b><on>ミン</on><b><on>コッ</on></b><on>カ</on>",
            "furigana merged": "<b><on> 国[コク]</on></b><on> 民[ミン]</on><b><on> 国[コッ]</on></b><on> 家[カ]</on>",
            "furikanji merged": "<b><on> コク[国]</on></b><on> ミン[民]</on><b><on> コッ[国]</on></b><on> カ[家]</on>",
        },
        id="Highlights every occurrence of a kanji used twice in one word",
    ),
    pytest.param(
        # 中国 + 国民: the same kanji doubled across the seam, but reading ごく then こく. A
        # repeater would have to copy the first reading, which would misread the second 国.
        "",
        "中国国民[ちゅうごくこくみん]",
        True,
        {
            "kana_only": "チュウゴクコクミン",
            "furigana": " 中国国民[チュウゴクコクミン]",
            "furikanji": " チュウゴクコクミン[中国国民]",
            "kana_only split": "<on>チュウ</on><on>ゴク</on><on>コク</on><on>ミン</on>",
            "furigana split": "<on> 中[チュウ]</on><on> 国[ゴク]</on><on> 国[コク]</on><on> 民[ミン]</on>",
            "furikanji split": "<on> チュウ[中]</on><on> ゴク[国]</on><on> コク[国]</on><on> ミン[民]</on>",
            "kana_only merged": "<on>チュウゴクコクミン</on>",
            "furigana merged": "<on> 中国国民[チュウゴクコクミン]</on>",
            "furikanji merged": "<on> チュウゴクコクミン[中国国民]</on>",
        },
        id="Reads each side of a doubled kanji at a word boundary on its own",
    ),
    pytest.param(
        # A repeater word written out, but with the reading simply repeating: nothing here says
        # repeater rather than word boundary, so the spelling the note used is what we keep
        "",
        "我我[われわれ]",
        True,
        {
            "kana_only": "われわれ",
            "furigana": " 我我[われわれ]",
            "furikanji": " われわれ[我我]",
            "kana_only split": "<kun>われ</kun><kun>われ</kun>",
            "furigana split": "<kun> 我[われ]</kun><kun> 我[われ]</kun>",
            "furikanji split": "<kun> われ[我]</kun><kun> われ[我]</kun>",
            "kana_only merged": "<kun>われわれ</kun>",
            "furigana merged": "<kun> 我我[われわれ]</kun>",
            "furikanji merged": "<kun> われわれ[我我]</kun>",
        },
        id="Leaves a doubled kanji whose reading merely repeats as written",
    ),
    pytest.param(
        # The baseline the three tests below have to match: 々 and the kanji it stands in for
        # written as the one furigana group they belong in
        "",
        "其々[それぞれ]",
        True,
        {
            "kana_only": "それぞれ",
            "furigana": " 其々[それぞれ]",
            "furikanji": " それぞれ[其々]",
            "kana_only split": "<kun>それぞれ</kun>",
            "furigana split": "<kun> 其々[それぞれ]</kun>",
            "furikanji split": "<kun> それぞれ[其々]</kun>",
            "kana_only merged": "<kun>それぞれ</kun>",
            "furigana merged": "<kun> 其々[それぞれ]</kun>",
            "furikanji merged": "<kun> それぞれ[其々]</kun>",
        },
        id="Reads a repeater word written as a single furigana group",
    ),
    pytest.param(
        # A space between the word and its 々 ends the run of kanji the furigana regex reads as
        # one word, leaving the 々 as a word of its own with no kanji in front of it to repeat.
        # It has no readings to match either, so it used to come out read as jukujikun, with the
        # kanji it belongs to stranded outside the tag: 其<juk> 々[それぞれ]</juk>
        "",
        "其 々[それぞれ]",
        True,
        {
            "kana_only": "それぞれ",
            "furigana": " 其々[それぞれ]",
            "furikanji": " それぞれ[其々]",
            "kana_only split": "<kun>それぞれ</kun>",
            "furigana split": "<kun> 其々[それぞれ]</kun>",
            "furikanji split": "<kun> それぞれ[其々]</kun>",
            "kana_only merged": "<kun>それぞれ</kun>",
            "furigana merged": "<kun> 其々[それぞれ]</kun>",
            "furikanji merged": "<kun> それぞれ[其々]</kun>",
        },
        id="Reads a repeater separated from its word by a space",
    ),
    pytest.param(
        # The same split, made by giving each of the two its own half of the reading rather than
        # by a space. The halves are put back together in the order they were written.
        "",
        "其[それ]々[ぞれ]",
        True,
        {
            "kana_only": "それぞれ",
            "furigana": " 其々[それぞれ]",
            "furikanji": " それぞれ[其々]",
            "kana_only split": "<kun>それぞれ</kun>",
            "furigana split": "<kun> 其々[それぞれ]</kun>",
            "furikanji split": "<kun> それぞれ[其々]</kun>",
            "kana_only merged": "<kun>それぞれ</kun>",
            "furigana merged": "<kun> 其々[それぞれ]</kun>",
            "furikanji merged": "<kun> それぞれ[其々]</kun>",
        },
        id="Reads a repeater given its own half of the word's reading",
    ),
    pytest.param(
        # Highlighting reaches the 々 as well as the kanji, the same as it does when the word
        # was written as one group to begin with
        "其",
        "其 々[それぞれ]",
        True,
        {
            "kana_only": "<b>それぞれ</b>",
            "furigana": "<b> 其々[それぞれ]</b>",
            "furikanji": "<b> それぞれ[其々]</b>",
            "kana_only split": "<b><kun>それぞれ</kun></b>",
            "furigana split": "<b><kun> 其々[それぞれ]</kun></b>",
            "furikanji split": "<b><kun> それぞれ[其々]</kun></b>",
            "kana_only merged": "<b><kun>それぞれ</kun></b>",
            "furigana merged": "<b><kun> 其々[それぞれ]</kun></b>",
            "furikanji merged": "<b><kun> それぞれ[其々]</kun></b>",
        },
        id="Highlights a repeater word that was separated from its word",
    ),
    pytest.param(
        # The whole kanji run has to survive the repair, not just the kanji the 々 repeats:
        # taking 物 alone would drop 生 and the reading it was given along with it
        "",
        "生物[せいぶつ]々[ぶつ]",
        True,
        {
            "kana_only": "セイブツブツ",
            "furigana": " 生物々[セイブツブツ]",
            "furikanji": " セイブツブツ[生物々]",
            "kana_only split": "<on>セイ</on><on>ブツブツ</on>",
            "furigana split": "<on> 生[セイ]</on><on> 物々[ブツブツ]</on>",
            "furikanji split": "<on> セイ[生]</on><on> ブツブツ[物々]</on>",
            "kana_only merged": "<on>セイブツブツ</on>",
            "furigana merged": "<on> 生物々[セイブツブツ]</on>",
            "furikanji merged": "<on> セイブツブツ[生物々]</on>",
        },
        id="Keeps the rest of the word when reuniting it with its repeater",
    ),
    pytest.param(
        "",
        # An edge case: the furigana does not repeat completely, for example 蝶々 can sometimes
        # be colloquially written as ちょうちょ
        "蝶々[ちょうちょ]",
        True,
        {
            "kana_only": "チョウチョ",
            "furigana": " 蝶々[チョウチョ]",
            "furikanji": " チョウチョ[蝶々]",
            "kana_only split": "<on>チョウチョ</on>",
            "furigana split": "<on> 蝶々[チョウチョ]</on>",
            "furikanji split": "<on> チョウチョ[蝶々]</on>",
            "kana_only merged": "<on>チョウチョ</on>",
            "furigana merged": "<on> 蝶々[チョウチョ]</on>",
            "furikanji merged": "<on> チョウチョ[蝶々]</on>",
        },
        id="Handles repeater with non repeating furigana 1/",
    ),
    pytest.param(
        "止",
        # A third edge case: there is only okurigana at the end
        "歯止め[はどめ]",
        True,
        {
            "kana_only": "は<b>どめ</b>",
            "furigana": " 歯[は]<b> 止[ど]め</b>",
            "furikanji": " は[歯]<b> ど[止]め</b>",
            "kana_only split": "<kun>は</kun><b><kun>ど</kun><oku>め</oku></b>",
            "furigana split": "<kun> 歯[は]</kun><b><kun> 止[ど]</kun><oku>め</oku></b>",
            "furikanji split": "<kun> は[歯]</kun><b><kun> ど[止]</kun><oku>め</oku></b>",
            "kana_only merged": "<kun>は</kun><b><kun>ど</kun><oku>め</oku></b>",
            "furigana merged": "<kun> 歯[は]</kun><b><kun> 止[ど]</kun><oku>め</oku></b>",
            "furikanji merged": "<kun> は[歯]</kun><b><kun> ど[止]</kun><oku>め</oku></b>",
        },
        id="Should be able to clean furigana whose okurigana is only at the end",
    ),
    pytest.param(
        "閣",
        "新[しん] 内閣[ないかく]の 組閣[そかく]が 発表[はっぴょう]された。",
        True,
        {
            "kana_only": "シン ナイ<b>カク</b>の ソ<b>カク</b>が ハッピョウされた。",
            "furigana": " 新[シン] 内[ナイ]<b> 閣[カク]</b>の 組[ソ]<b> 閣[カク]</b>が 発表[ハッピョウ]された。",
            "furikanji": " シン[新] ナイ[内]<b> カク[閣]</b>の ソ[組]<b> カク[閣]</b>が ハッピョウ[発表]された。",
            "kana_only split": "<on>シン</on> <on>ナイ</on><b><on>カク</on></b>の <on>ソ</on><b>"
            "<on>カク</on></b>が <on>ハッ</on><on>ピョウ</on><oku>された</oku>。",
            "furigana split": "<on> 新[シン]</on><on> 内[ナイ]</on><b><on> 閣[カク]</on></b>の<on> 組[ソ]</on>"
            "<b><on> 閣[カク]</on></b>が<on> 発[ハッ]</on><on> 表[ピョウ]</on><oku>された</oku>。",
            "furikanji split": "<on> シン[新]</on><on> ナイ[内]</on><b><on> カク[閣]</on></b>の<on> ソ[組]</on>"
            "<b><on> カク[閣]</on></b>が<on> ハッ[発]</on><on> ピョウ[表]</on><oku>された</oku>。",
            "kana_only merged": "<on>シン</on> <on>ナイ</on><b><on>カク</on></b>の <on>ソ</on><b>"
            "<on>カク</on></b>が <on>ハッピョウ</on><oku>された</oku>。",
            "furigana merged": "<on> 新[シン]</on><on> 内[ナイ]</on><b><on> 閣[カク]</on></b>の<on> 組[ソ]</on>"
            "<b><on> 閣[カク]</on></b>が<on> 発表[ハッピョウ]</on><oku>された</oku>。",
            "furikanji merged": "<on> シン[新]</on><on> ナイ[内]</on><b><on> カク[閣]</on></b>の<on>"
            " ソ[組]</on><b><on> カク[閣]</on></b>が<on> ハッピョウ[発表]</on><oku>された</oku>。",
        },
        id="Is able to match the same kanji occurring twice",
    ),
    pytest.param(
        "国",
        "その2 国[こく]は 国交[こっこう]を 断絶[だんぜつ]した。",
        True,
        {
            "kana_only": "その2 <b>コク</b>は <b>コッ</b>コウを ダンゼツした。",
            "furigana": "その2<b> 国[コク]</b>は<b> 国[コッ]</b> 交[コウ]を 断絶[ダンゼツ]した。",
            "furikanji": "その2<b> コク[国]</b>は<b> コッ[国]</b> コウ[交]を ダンゼツ[断絶]した。",
            "kana_only split": "その2 <b><on>コク</on></b>は <b><on>コッ</on></b><on>コウ</on>を"
            " <on>ダン</on><on>ゼツ</on><oku>した</oku>。",
            "furigana split": "その2<b><on> 国[コク]</on></b>は<b><on> 国[コッ]</on></b><on> 交[コウ]</on>を<on>"
            " 断[ダン]</on><on> 絶[ゼツ]</on><oku>した</oku>。",
            "furikanji split": "その2<b><on> コク[国]</on></b>は<b><on> コッ[国]</on></b><on> コウ[交]</on>を<on>"
            " ダン[断]</on><on> ゼツ[絶]</on><oku>した</oku>。",
            "kana_only merged": "その2 <b><on>コク</on></b>は <b><on>コッ</on></b><on>コウ</on>を"
            " <on>ダンゼツ</on><oku>した</oku>。",
            "furigana merged": "その2<b><on> 国[コク]</on></b>は<b><on> 国[コッ]</on></b><on> 交[コウ]</on>を<on>"
            " 断絶[ダンゼツ]</on><oku>した</oku>。",
            "furikanji merged": "その2<b><on> コク[国]</on></b>は<b><on> コッ[国]</on></b><on> コウ[交]</on>を<on>"
            " ダンゼツ[断絶]</on><oku>した</oku>。",
        },
        id="Is able to match the same kanji occurring twice with other using small tsu",
    ),
    pytest.param(
        "靴",
        # ながぐつ　has が (onyomi か match) and ぐつ (kunyomi くつ) as matches
        "お 前[まえ]いつも 長靴[ながぐつ]に 傘[かさ]さしてキメーんだよ！！",
        True,
        {
            "kana_only": "お まえいつも なが<b>ぐつ</b>に かささしてキメーんだよ！！",
            "furigana": "お 前[まえ]いつも 長[なが]<b> 靴[ぐつ]</b>に 傘[かさ]さしてキメーんだよ！！",
            "furikanji": "お まえ[前]いつも なが[長]<b> ぐつ[靴]</b>に かさ[傘]さしてキメーんだよ！！",
            "kana_only split": "お <kun>まえ</kun>いつも <kun>なが</kun><b><kun>ぐつ</kun></b>に"
            " <kun>かさ</kun>さしてキメーんだよ！！",
            "furigana split": "お<kun> 前[まえ]</kun>いつも<kun> 長[なが]</kun><b><kun> 靴[ぐつ]</kun></b>に"
            "<kun> 傘[かさ]</kun>さしてキメーんだよ！！",
            "furikanji split": "お<kun> まえ[前]</kun>いつも<kun> なが[長]</kun><b><kun> ぐつ[靴]</kun></b>に"
            "<kun> かさ[傘]</kun>さしてキメーんだよ！！",
            "kana_only merged": "お <kun>まえ</kun>いつも <kun>なが</kun><b><kun>ぐつ</kun></b>に"
            " <kun>かさ</kun>さしてキメーんだよ！！",
            "furigana merged": "お<kun> 前[まえ]</kun>いつも<kun> 長[なが]</kun><b><kun> 靴[ぐつ]</kun></b>に"
            "<kun> 傘[かさ]</kun>さしてキメーんだよ！！",
            "furikanji merged": "お<kun> まえ[前]</kun>いつも<kun> なが[長]</kun><b><kun> ぐつ[靴]</kun></b>に"
            "<kun> かさ[傘]</kun>さしてキメーんだよ！！",
        },
        id="Is able to pick the right reading when there are multiple matches 1/",
    ),
    pytest.param(
        "輸",
        # 輸 has ゆ and しゅ as onyomi readings, should correctly match to the left edge
        "輸出[ゆしゅつ]可能[かのう]。",
        True,
        {
            "kana_only": "<b>ユ</b>シュツカノウ。",
            "furigana": "<b> 輸[ユ]</b> 出[シュツ] 可能[カノウ]。",
            "furikanji": "<b> ユ[輸]</b> シュツ[出] カノウ[可能]。",
            "kana_only split": "<b><on>ユ</on></b><on>シュツ</on><on>カ</on><on>ノウ</on>。",
            "furigana split": "<b><on> 輸[ユ]</on></b><on> 出[シュツ]</on><on> 可[カ]</on><on> 能[ノウ]</on>。",
            "furikanji split": "<b><on> ユ[輸]</on></b><on> シュツ[出]</on><on> カ[可]</on><on> ノウ[能]</on>。",
            "kana_only merged": "<b><on>ユ</on></b><on>シュツ</on><on>カノウ</on>。",
            "furigana merged": "<b><on> 輸[ユ]</on></b><on> 出[シュツ]</on><on> 可能[カノウ]</on>。",
            "furikanji merged": "<b><on> ユ[輸]</on></b><on> シュツ[出]</on><on> カノウ[可能]</on>。",
        },
        id="Is able to pick the right reading when there are multiple matches 2/",
    ),
    pytest.param(
        "必",
        "見敵必殺[けんてきひっさつ]の 指示[しじ]もないのに 戦闘[せんとう]は 不自然[ふしぜん]。",
        True,
        {
            "kana_only": "ケンテキ<b>ヒッ</b>サツの シジもないのに セントウは フシゼン。",
            "furigana": " 見敵[ケンテキ]<b> 必[ヒッ]</b> 殺[サツ]の 指示[シジ]もないのに"
            " 戦闘[セントウ]は 不自然[フシゼン]。",
            "furikanji": " ケンテキ[見敵]<b> ヒッ[必]</b> サツ[殺]の シジ[指示]もないのに"
            " セントウ[戦闘]は フシゼン[不自然]。",
            "kana_only split": "<on>ケン</on><on>テキ</on><b><on>ヒッ</on></b><on>サツ</on>の"
            " <on>シ</on><on>ジ</on>もないのに <on>セン</on><on>トウ</on>は"
            " <on>フ</on><on>シ</on><on>ゼン</on>。",
            "furigana split": "<on> 見[ケン]</on><on> 敵[テキ]</on><b><on> 必[ヒッ]</on></b><on> 殺[サツ]</on>の"
            "<on> 指[シ]</on><on> 示[ジ]</on>もないのに<on> 戦[セン]</on><on> 闘[トウ]</on>は"
            "<on> 不[フ]</on><on> 自[シ]</on><on> 然[ゼン]</on>。",
            "furikanji split": "<on> ケン[見]</on><on> テキ[敵]</on><b><on> ヒッ[必]</on></b><on> サツ[殺]</on>の"
            "<on> シ[指]</on><on> ジ[示]</on>もないのに<on> セン[戦]</on><on> トウ[闘]</on>は"
            "<on> フ[不]</on><on> シ[自]</on><on> ゼン[然]</on>。",
            "kana_only merged": "<on>ケンテキ</on><b><on>ヒッ</on></b><on>サツ</on>の <on>シジ</on>もないのに"
            " <on>セントウ</on>は <on>フシゼン</on>。",
            "furigana merged": "<on> 見敵[ケンテキ]</on><b><on> 必[ヒッ]</on></b><on> 殺[サツ]</on>の"
            "<on> 指示[シジ]</on>もないのに<on> 戦闘[セントウ]</on>は<on> 不自然[フシゼン]</on>。",
            "furikanji merged": "<on> ケンテキ[見敵]</on><b><on> ヒッ[必]</on></b><on> サツ[殺]</on>の"
            "<on> シジ[指示]</on>もないのに<on> セントウ[戦闘]</on>は<on> フシゼン[不自然]</on>。",
        },
        id="Should match reading in 4 kanji compound word",
    ),
    pytest.param(
        "馴",
        "幼馴染[おさななじ]みと 久[ひさ]しぶりに 会[あ]った。",
        True,
        {
            "kana_only": "おさな<b>な</b>じみと ひさしぶりに あった。",
            "furigana": " 幼[おさな]<b> 馴[な]</b> 染[じ]みと 久[ひさ]しぶりに 会[あ]った。",
            "furikanji": " おさな[幼]<b> な[馴]</b> じ[染]みと ひさ[久]しぶりに あ[会]った。",
            "kana_only split": "<kun>おさな</kun><b><kun>な</kun></b><kun>じ</kun><oku>み</oku>と"
            " <kun>ひさ</kun><oku>し</oku>ぶりに <kun>あ</kun><oku>った</oku>。",
            "furigana split": "<kun> 幼[おさな]</kun><b><kun> 馴[な]</kun></b><kun> 染[じ]</kun><oku>み</oku>と<kun>"
            " 久[ひさ]</kun><oku>し</oku>ぶりに<kun> 会[あ]</kun><oku>った</oku>。",
            "furikanji split": "<kun> おさな[幼]</kun><b><kun> な[馴]</kun></b><kun> じ[染]</kun><oku>み</oku>と<kun>"
            " ひさ[久]</kun><oku>し</oku>ぶりに<kun> あ[会]</kun><oku>った</oku>。",
            "kana_only merged": "<kun>おさな</kun><b><kun>な</kun></b><kun>じ</kun><oku>み</oku>と"
            " <kun>ひさ</kun><oku>し</oku>ぶりに <kun>あ</kun><oku>った</oku>。",
            "furigana merged": "<kun> 幼[おさな]</kun><b><kun> 馴[な]</kun></b><kun> 染[じ]</kun><oku>み</oku>と<kun>"
            " 久[ひさ]</kun><oku>し</oku>ぶりに<kun> 会[あ]</kun><oku>った</oku>。",
            "furikanji merged": "<kun> おさな[幼]</kun><b><kun> な[馴]</kun></b><kun> じ[染]</kun><oku>み</oku>と<kun>"
            " ひさ[久]</kun><oku>し</oku>ぶりに<kun> あ[会]</kun><oku>った</oku>。",
        },
        id="Should match reading in middle of 3 kanji kunyomi compound",
    ),
    pytest.param(
        "賊",
        # Note: jpn number
        "海賊[かいぞく]たちは ７[なな]つの 海[うみ]を 航海[こうかい]した。",
        True,
        {
            "kana_only": "カイ<b>ゾク</b>たちは ななつの うみを コウカイした。",
            "furigana": " 海[カイ]<b> 賊[ゾク]</b>たちは ７[なな]つの 海[うみ]を 航海[コウカイ]した。",
            "furikanji": " カイ[海]<b> ゾク[賊]</b>たちは なな[７]つの うみ[海]を コウカイ[航海]した。",
            "kana_only split": "<on>カイ</on><b><on>ゾク</on></b>たちは <kun>なな</kun><oku>つ</oku>の <kun>うみ</kun>を"
            " <on>コウ</on><on>カイ</on><oku>した</oku>。",
            "furigana split": "<on> 海[カイ]</on><b><on> 賊[ゾク]</on></b>たちは<kun> ７[なな]</kun><oku>つ</oku>の"
            "<kun>"
            " 海[うみ]</kun>を<on> 航[コウ]</on><on> 海[カイ]</on><oku>した</oku>。",
            "furikanji split": "<on> カイ[海]</on><b><on> ゾク[賊]</on></b>たちは<kun> なな[７]</kun><oku>つ</oku>の"
            "<kun>"
            " うみ[海]</kun>を<on> コウ[航]</on><on> カイ[海]</on><oku>した</oku>。",
            "kana_only merged": "<on>カイ</on><b><on>ゾク</on></b>たちは <kun>なな</kun><oku>つ</oku>の <kun>うみ</kun>を"
            " <on>コウカイ</on><oku>した</oku>。",
            "furigana merged": "<on> 海[カイ]</on><b><on> 賊[ゾク]</on></b>たちは<kun> ７[なな]</kun><oku>つ</oku>の"
            "<kun>"
            " 海[うみ]</kun>を<on> 航海[コウカイ]</on><oku>した</oku>。",
            "furikanji merged": "<on> カイ[海]</on><b><on> ゾク[賊]</on></b>たちは<kun> なな[７]</kun><oku>つ</oku>の"
            "<kun>"
            " うみ[海]</kun>を<on> コウカイ[航海]</on><oku>した</oku>。",
        },
        id="Should match furigana for numbers",
    ),
    pytest.param(
        "由",
        # Both ゆ and ゆい are in the furigana but the correct match is ゆい
        "彼女[かのじょ]は 由緒[ゆいしょ]ある 家柄[いえがら]の 出[で]だ。",
        True,
        {
            "kana_only": "かのジョは <b>ユイ</b>ショある いえがらの でだ。",
            "furigana": " 彼女[かのジョ]は<b> 由[ユイ]</b> 緒[ショ]ある 家柄[いえがら]の 出[で]だ。",
            "furikanji": " かのジョ[彼女]は<b> ユイ[由]</b> ショ[緒]ある いえがら[家柄]の で[出]だ。",
            "kana_only split": "<kun>かの</kun><on>ジョ</on>は <b><on>ユイ</on></b><on>ショ</on>ある"
            " <kun>いえ</kun><kun>がら</kun>の <kun>で</kun>だ。",
            "furigana split": "<kun> 彼[かの]</kun><on> 女[ジョ]</on>は<b><on> 由[ユイ]</on></b><on>"
            " 緒[ショ]</on>ある<kun> 家[いえ]</kun><kun> 柄[がら]</kun>の<kun>"
            " 出[で]</kun>だ。",
            "furikanji split": "<kun> かの[彼]</kun><on> ジョ[女]</on>は<b><on> ユイ[由]</on></b><on>"
            " ショ[緒]</on>ある<kun> いえ[家]</kun><kun> がら[柄]</kun>の<kun>"
            " で[出]</kun>だ。",
            "kana_only merged": "<kun>かの</kun><on>ジョ</on>は <b><on>ユイ</on></b><on>ショ</on>ある"
            " <kun>いえがら</kun>の <kun>で</kun>だ。",
            "furigana merged": "<kun> 彼[かの]</kun><on> 女[ジョ]</on>は<b><on> 由[ユイ]</on></b><on>"
            " 緒[ショ]</on>ある<kun> 家柄[いえがら]</kun>の<kun> 出[で]</kun>だ。",
            "furikanji merged": "<kun> かの[彼]</kun><on> ジョ[女]</on>は<b><on> ユイ[由]</on></b><on>"
            " ショ[緒]</on>ある<kun> いえがら[家柄]</kun>の<kun> で[出]</kun>だ。",
        },
        id="Should match the full reading match when there are multiple /1",
    ),
    pytest.param(
        "口",
        # Both ク (on) and くち (kun) are in the furigana but the correct match is くち
        "口紅[くちべに]",
        True,
        {
            "kana_only": "<b>くち</b>べに",
            "furigana": "<b> 口[くち]</b> 紅[べに]",
            "furikanji": "<b> くち[口]</b> べに[紅]",
            "kana_only split": "<b><kun>くち</kun></b><kun>べに</kun>",
            "furigana split": "<b><kun> 口[くち]</kun></b><kun> 紅[べに]</kun>",
            "furikanji split": "<b><kun> くち[口]</kun></b><kun> べに[紅]</kun>",
            "kana_only merged": "<b><kun>くち</kun></b><kun>べに</kun>",
            "furigana merged": "<b><kun> 口[くち]</kun></b><kun> 紅[べに]</kun>",
            "furikanji merged": "<b><kun> くち[口]</kun></b><kun> べに[紅]</kun>",
        },
        id="Should match the full reading match when there are multiple 2/",
    ),
    pytest.param(
        "主",
        # Both シュ (on) and シュウ (on) are in the furigana but the correct match is シュウ
        "主従[しゅうじゅう]",
        True,
        {
            "kana_only": "<b>シュウ</b>ジュウ",
            "furigana": "<b> 主[シュウ]</b> 従[ジュウ]",
            "furikanji": "<b> シュウ[主]</b> ジュウ[従]",
            "kana_only split": "<b><on>シュウ</on></b><on>ジュウ</on>",
            "furigana split": "<b><on> 主[シュウ]</on></b><on> 従[ジュウ]</on>",
            "furikanji split": "<b><on> シュウ[主]</on></b><on> ジュウ[従]</on>",
            "kana_only merged": "<b><on>シュウ</on></b><on>ジュウ</on>",
            "furigana merged": "<b><on> 主[シュウ]</on></b><on> 従[ジュウ]</on>",
            "furikanji merged": "<b><on> シュウ[主]</on></b><on> ジュウ[従]</on>",
        },
        id="Should match the full reading match when there are multiple 3/",
    ),
    pytest.param(
        "剔",
        "剔抉[てっけつ]",
        True,
        {
            "kana_only": "<b>テッ</b>ケツ",
            "furigana": "<b> 剔[テッ]</b> 抉[ケツ]",
            "furikanji": "<b> テッ[剔]</b> ケツ[抉]",
            "kana_only split": "<b><on>テッ</on></b><on>ケツ</on>",
            "furigana split": "<b><on> 剔[テッ]</on></b><on> 抉[ケツ]</on>",
            "furikanji split": "<b><on> テッ[剔]</on></b><on> ケツ[抉]</on>",
            "kana_only merged": "<b><on>テッ</on></b><on>ケツ</on>",
            "furigana merged": "<b><on> 剔[テッ]</on></b><on> 抉[ケツ]</on>",
            "furikanji merged": "<b><on> テッ[剔]</on></b><on> ケツ[抉]</on>",
        },
        id="small tsu 1/",
    ),
    pytest.param(
        "一",
        "一見[いっけん]",
        True,
        {
            "kana_only": "<b>イッ</b>ケン",
            "furigana": "<b> 一[イッ]</b> 見[ケン]",
            "furikanji": "<b> イッ[一]</b> ケン[見]",
            "kana_only split": "<b><on>イッ</on></b><on>ケン</on>",
            "furigana split": "<b><on> 一[イッ]</on></b><on> 見[ケン]</on>",
            "furikanji split": "<b><on> イッ[一]</on></b><on> ケン[見]</on>",
            "kana_only merged": "<b><on>イッ</on></b><on>ケン</on>",
            "furigana merged": "<b><on> 一[イッ]</on></b><on> 見[ケン]</on>",
            "furikanji merged": "<b><on> イッ[一]</on></b><on> ケン[見]</on>",
        },
        id="small tsu 2/",
    ),
    pytest.param(
        "各",
        "各国[かっこく]",
        True,
        {
            "kana_only": "<b>カッ</b>コク",
            "furigana": "<b> 各[カッ]</b> 国[コク]",
            "furikanji": "<b> カッ[各]</b> コク[国]",
            "kana_only split": "<b><on>カッ</on></b><on>コク</on>",
            "furigana split": "<b><on> 各[カッ]</on></b><on> 国[コク]</on>",
            "furikanji split": "<b><on> カッ[各]</on></b><on> コク[国]</on>",
            "kana_only merged": "<b><on>カッ</on></b><on>コク</on>",
            "furigana merged": "<b><on> 各[カッ]</on></b><on> 国[コク]</on>",
            "furikanji merged": "<b><on> カッ[各]</on></b><on> コク[国]</on>",
        },
        id="small tsu 3/",
    ),
    pytest.param(
        "吉",
        "吉兆[きっちょう]",
        True,
        {
            "kana_only": "<b>キッ</b>チョウ",
            "furigana": "<b> 吉[キッ]</b> 兆[チョウ]",
            "furikanji": "<b> キッ[吉]</b> チョウ[兆]",
            "kana_only split": "<b><on>キッ</on></b><on>チョウ</on>",
            "furigana split": "<b><on> 吉[キッ]</on></b><on> 兆[チョウ]</on>",
            "furikanji split": "<b><on> キッ[吉]</on></b><on> チョウ[兆]</on>",
            "kana_only merged": "<b><on>キッ</on></b><on>チョウ</on>",
            "furigana merged": "<b><on> 吉[キッ]</on></b><on> 兆[チョウ]</on>",
            "furikanji merged": "<b><on> キッ[吉]</on></b><on> チョウ[兆]</on>",
        },
        id="small tsu 4/",
    ),
    pytest.param(
        "尻",
        # Should be considered a kunyomi match, it's the only instance of お->ぽ conversion
        # with small tsu
        "尻尾[しっぽ]",
        True,
        {
            "kana_only": "<b>しっ</b>ぽ",
            "furigana": "<b> 尻[しっ]</b> 尾[ぽ]",
            "furikanji": "<b> しっ[尻]</b> ぽ[尾]",
            "kana_only split": "<b><kun>しっ</kun></b><kun>ぽ</kun>",
            "furigana split": "<b><kun> 尻[しっ]</kun></b><kun> 尾[ぽ]</kun>",
            "furikanji split": "<b><kun> しっ[尻]</kun></b><kun> ぽ[尾]</kun>",
            "kana_only merged": "<b><kun>しっ</kun></b><kun>ぽ</kun>",
            "furigana merged": "<b><kun> 尻[しっ]</kun></b><kun> 尾[ぽ]</kun>",
            "furikanji merged": "<b><kun> しっ[尻]</kun></b><kun> ぽ[尾]</kun>",
        },
        id="small tsu 5/",
    ),
    pytest.param(
        "呆",
        "呆気[あっけ]ない",
        True,
        {
            "kana_only": "<b>あっ</b>ケない",
            "furigana": "<b> 呆[あっ]</b> 気[ケ]ない",
            "furikanji": "<b> あっ[呆]</b> ケ[気]ない",
            "kana_only split": "<b><kun>あっ</kun></b><on>ケ</on><oku>ない</oku>",
            "furigana split": "<b><kun> 呆[あっ]</kun></b><on> 気[ケ]</on><oku>ない</oku>",
            "furikanji split": "<b><kun> あっ[呆]</kun></b><on> ケ[気]</on><oku>ない</oku>",
            "kana_only merged": "<b><kun>あっ</kun></b><on>ケ</on><oku>ない</oku>",
            "furigana merged": "<b><kun> 呆[あっ]</kun></b><on> 気[ケ]</on><oku>ない</oku>",
            "furikanji merged": "<b><kun> あっ[呆]</kun></b><on> ケ[気]</on><oku>ない</oku>",
        },
        id="small tsu 6/",
    ),
    pytest.param(
        "甲",
        "甲冑[かっちゅう]の 試着[しちゃく]をお 願[ねが]いします｡",
        True,
        {
            "kana_only": "<b>カッ</b>チュウの シチャクをお ねがいします｡",
            "furigana": "<b> 甲[カッ]</b> 冑[チュウ]の 試着[シチャク]をお 願[ねが]いします｡",
            "furikanji": "<b> カッ[甲]</b> チュウ[冑]の シチャク[試着]をお ねが[願]いします｡",
            "kana_only split": "<b><on>カッ</on></b><on>チュウ</on>の"
            " <on>シ</on><on>チャク</on>をお <kun>ねが</kun><oku>い</oku>します｡",
            "furigana split": "<b><on> 甲[カッ]</on></b><on> 冑[チュウ]</on>の<on> 試[シ]</on><on>"
            " 着[チャク]</on>をお<kun> 願[ねが]</kun><oku>い</oku>します｡",
            "furikanji split": "<b><on> カッ[甲]</on></b><on> チュウ[冑]</on>の<on> シ[試]</on><on>"
            " チャク[着]</on>をお<kun> ねが[願]</kun><oku>い</oku>します｡",
            "kana_only merged": "<b><on>カッ</on></b><on>チュウ</on>の"
            " <on>シチャク</on>をお <kun>ねが</kun><oku>い</oku>します｡",
            "furigana merged": "<b><on> 甲[カッ]</on></b><on> 冑[チュウ]</on>の<on> 試着[シチャク]</on>をお<kun>"
            " 願[ねが]</kun><oku>い</oku>します｡",
            "furikanji merged": "<b><on> カッ[甲]</on></b><on> チュウ[冑]</on>の<on> シチャク[試着]</on>をお<kun>"
            " ねが[願]</kun><oku>い</oku>します｡",
        },
        id="small tsu 7/",
    ),
    pytest.param(
        "百",
        "百貨店[ひゃっかてん]",
        True,
        {
            "kana_only": "<b>ヒャッ</b>カテン",
            "furigana": "<b> 百[ヒャッ]</b> 貨店[カテン]",
            "furikanji": "<b> ヒャッ[百]</b> カテン[貨店]",
            "kana_only split": "<b><on>ヒャッ</on></b><on>カ</on><on>テン</on>",
            "furigana split": "<b><on> 百[ヒャッ]</on></b><on> 貨[カ]</on><on> 店[テン]</on>",
            "furikanji split": "<b><on> ヒャッ[百]</on></b><on> カ[貨]</on><on> テン[店]</on>",
            "kana_only merged": "<b><on>ヒャッ</on></b><on>カテン</on>",
            "furigana merged": "<b><on> 百[ヒャッ]</on></b><on> 貨店[カテン]</on>",
            "furikanji merged": "<b><on> ヒャッ[百]</on></b><on> カテン[貨店]</on>",
        },
        id="small tsu 8/",
    ),
    pytest.param(
        "蔵",
        "秘蔵っ子[ひぞっこ]",
        True,
        {
            "kana_only": "ヒ<b>ゾ</b>っこ",
            "furigana": " 秘[ヒ]<b> 蔵[ゾ]</b>っ 子[こ]",
            "furikanji": " ヒ[秘]<b> ゾ[蔵]</b>っ こ[子]",
            "kana_only split": "<on>ヒ</on><b><on>ゾ</on></b>っ<kun>こ</kun>",
            "furigana split": "<on> 秘[ヒ]</on><b><on> 蔵[ゾ]</on></b>っ<kun> 子[こ]</kun>",
            "furikanji split": "<on> ヒ[秘]</on><b><on> ゾ[蔵]</on></b>っ<kun> こ[子]</kun>",
            "kana_only merged": "<on>ヒ</on><b><on>ゾ</on></b>っ<kun>こ</kun>",
            "furigana merged": "<on> 秘[ヒ]</on><b><on> 蔵[ゾ]</on></b>っ<kun> 子[こ]</kun>",
            "furikanji merged": "<on> ヒ[秘]</on><b><on> ゾ[蔵]</on></b>っ<kun> こ[子]</kun>",
        },
        id="small tsu 秘蔵っ子 with う dropped",
    ),
    pytest.param(
        "蔵",
        "秘蔵っ子[ひぞうっこ]",
        True,
        {
            "kana_only": "ヒ<b>ゾウ</b>っこ",
            "furigana": " 秘[ヒ]<b> 蔵[ゾウ]</b>っ 子[こ]",
            "furikanji": " ヒ[秘]<b> ゾウ[蔵]</b>っ こ[子]",
            "kana_only split": "<on>ヒ</on><b><on>ゾウ</on></b>っ<kun>こ</kun>",
            "furigana split": "<on> 秘[ヒ]</on><b><on> 蔵[ゾウ]</on></b>っ<kun> 子[こ]</kun>",
            "furikanji split": "<on> ヒ[秘]</on><b><on> ゾウ[蔵]</on></b>っ<kun> こ[子]</kun>",
            "kana_only merged": "<on>ヒ</on><b><on>ゾウ</on></b>っ<kun>こ</kun>",
            "furigana merged": "<on> 秘[ヒ]</on><b><on> 蔵[ゾウ]</on></b>っ<kun> 子[こ]</kun>",
            "furikanji merged": "<on> ヒ[秘]</on><b><on> ゾウ[蔵]</on></b>っ<kun> こ[子]</kun>",
        },
        id="small tsu 秘蔵っ子 with う included",
    ),
    pytest.param(
        "放",
        "放[ほ]ったらかす",
        True,
        {
            "kana_only": "<b>ほったら</b>かす",
            "furigana": "<b> 放[ほ]ったら</b>かす",
            "furikanji": "<b> ほ[放]ったら</b>かす",
            "kana_only split": "<b><kun>ほ</kun><oku>ったら</oku></b>かす",
            "furigana split": "<b><kun> 放[ほ]</kun><oku>ったら</oku></b>かす",
            "furikanji split": "<b><kun> ほ[放]</kun><oku>ったら</oku></b>かす",
            "kana_only merged": "<b><kun>ほ</kun><oku>ったら</oku></b>かす",
            "furigana merged": "<b><kun> 放[ほ]</kun><oku>ったら</oku></b>かす",
            "furikanji merged": "<b><kun> ほ[放]</kun><oku>ったら</oku></b>かす",
        },
        id="small tsu 放[ほ]ったら with う dropped",
    ),
    pytest.param(
        "放",
        "放[ほう]ったらかす",
        True,
        {
            "kana_only": "<b>ほうったら</b>かす",
            "furigana": "<b> 放[ほう]ったら</b>かす",
            "furikanji": "<b> ほう[放]ったら</b>かす",
            "kana_only split": "<b><kun>ほう</kun><oku>ったら</oku></b>かす",
            "furigana split": "<b><kun> 放[ほう]</kun><oku>ったら</oku></b>かす",
            "furikanji split": "<b><kun> ほう[放]</kun><oku>ったら</oku></b>かす",
            "kana_only merged": "<b><kun>ほう</kun><oku>ったら</oku></b>かす",
            "furigana merged": "<b><kun> 放[ほう]</kun><oku>ったら</oku></b>かす",
            "furikanji merged": "<b><kun> ほう[放]</kun><oku>ったら</oku></b>かす",
        },
        id="small tsu 放[ほ]ったら with う included",
    ),
    pytest.param(
        "目",
        "完全[かんぜん]に 裏目[うらめ]ったな",
        True,
        {
            "kana_only": "カンゼンに うら<b>めった</b>な",
            "furigana": " 完全[カンゼン]に 裏[うら]<b> 目[め]った</b>な",
            "furikanji": " カンゼン[完全]に うら[裏]<b> め[目]った</b>な",
            "kana_only split": "<on>カン</on><on>ゼン</on>に <kun>うら</kun><b><kun>め</kun>"
            "<oku>った</oku></b>な",
            "furigana split": "<on> 完[カン]</on><on> 全[ゼン]</on>に<kun> 裏[うら]</kun><b><kun> 目[め]</kun>"
            "<oku>った</oku></b>な",
            "furikanji split": "<on> カン[完]</on><on> ゼン[全]</on>に<kun> うら[裏]</kun><b><kun> め[目]</kun>"
            "<oku>った</oku></b>な",
            "kana_only merged": "<on>カンゼン</on>に <kun>うら</kun><b><kun>め</kun><oku>った</oku></b>な",
            "furigana merged": "<on> 完全[カンゼン]</on>に<kun> 裏[うら]</kun><b><kun> 目[め]</kun>"
            "<oku>った</oku></b>な",
            "furikanji merged": "<on> カンゼン[完全]</on>に<kun> うら[裏]</kun><b><kun> め[目]</kun><oku>"
            "った</oku></b>な",
        },
        id="okurigana of godan verb from a noun 裏目る",
    ),
    pytest.param(
        "口",
        # 口 kunyomi くち is found in the furigana too, but the onyomi ク wins correctly
        "口調[くちょう]",
        True,
        {
            "kana_only": "<b>ク</b>チョウ",
            "furigana": "<b> 口[ク]</b> 調[チョウ]",
            "furikanji": "<b> ク[口]</b> チョウ[調]",
            "kana_only split": "<b><on>ク</on></b><on>チョウ</on>",
            "furigana split": "<b><on> 口[ク]</on></b><on> 調[チョウ]</on>",
            "furikanji split": "<b><on> ク[口]</on></b><on> チョウ[調]</on>",
            "kana_only merged": "<b><on>ク</on></b><on>チョウ</on>",
            "furigana merged": "<b><on> 口[ク]</on></b><on> 調[チョウ]</on>",
            "furikanji merged": "<b><on> ク[口]</on></b><on> チョウ[調]</on>",
        },
        id="reading mixup /1",
    ),
    pytest.param(
        "青",
        # あお -> さお
        "真[ま]っ青[さお]",
        True,
        {
            "kana_only": "まっ<b>さお</b>",
            "furigana": " 真[ま]っ<b> 青[さお]</b>",
            "furikanji": " ま[真]っ<b> さお[青]</b>",
            "kana_only split": "<kun>ま</kun>っ<b><kun>さお</kun></b>",
            "furigana split": "<kun> 真[ま]</kun>っ<b><kun> 青[さお]</kun></b>",
            "furikanji split": "<kun> ま[真]</kun>っ<b><kun> さお[青]</kun></b>",
            "kana_only merged": "<kun>ま</kun>っ<b><kun>さお</kun></b>",
            "furigana merged": "<kun> 真[ま]</kun>っ<b><kun> 青[さお]</kun></b>",
            "furikanji merged": "<kun> ま[真]</kun>っ<b><kun> さお[青]</kun></b>",
        },
        id="sound change readings 1/",
    ),
    pytest.param(
        "赤",
        # あか -> か
        "真っ赤[まっか]",
        True,
        {
            "kana_only": "まっ<b>か</b>",
            "furigana": " 真[ま]っ<b> 赤[か]</b>",
            "furikanji": " ま[真]っ<b> か[赤]</b>",
            "kana_only split": "<kun>ま</kun>っ<b><kun>か</kun></b>",
            "furigana split": "<kun> 真[ま]</kun>っ<b><kun> 赤[か]</kun></b>",
            "furikanji split": "<kun> ま[真]</kun>っ<b><kun> か[赤]</kun></b>",
            "kana_only merged": "<kun>ま</kun>っ<b><kun>か</kun></b>",
            "furigana merged": "<kun> 真[ま]</kun>っ<b><kun> 赤[か]</kun></b>",
            "furikanji merged": "<kun> ま[真]</kun>っ<b><kun> か[赤]</kun></b>",
        },
        id="sound change readings 2/",
    ),
    pytest.param(
        "新",
        # あら -> さら
        "真っ新[まっさら]",
        True,
        {
            "kana_only": "まっ<b>さら</b>",
            "furigana": " 真[ま]っ<b> 新[さら]</b>",
            "furikanji": " ま[真]っ<b> さら[新]</b>",
            "kana_only split": "<kun>ま</kun>っ<b><kun>さら</kun></b>",
            "furigana split": "<kun> 真[ま]</kun>っ<b><kun> 新[さら]</kun></b>",
            "furikanji split": "<kun> ま[真]</kun>っ<b><kun> さら[新]</kun></b>",
            "kana_only merged": "<kun>ま</kun>っ<b><kun>さら</kun></b>",
            "furigana merged": "<kun> 真[ま]</kun>っ<b><kun> 新[さら]</kun></b>",
            "furikanji merged": "<kun> ま[真]</kun>っ<b><kun> さら[新]</kun></b>",
        },
        id="sound change readings 3/",
    ),
    pytest.param(
        "雨",
        # あめ -> さめ
        "春雨[はるさめ]",
        True,
        {
            "kana_only": "はる<b>さめ</b>",
            "furigana": " 春[はる]<b> 雨[さめ]</b>",
            "furikanji": " はる[春]<b> さめ[雨]</b>",
            "kana_only split": "<kun>はる</kun><b><kun>さめ</kun></b>",
            "furigana split": "<kun> 春[はる]</kun><b><kun> 雨[さめ]</kun></b>",
            "furikanji split": "<kun> はる[春]</kun><b><kun> さめ[雨]</kun></b>",
            "kana_only merged": "<kun>はる</kun><b><kun>さめ</kun></b>",
            "furigana merged": "<kun> 春[はる]</kun><b><kun> 雨[さめ]</kun></b>",
            "furikanji merged": "<kun> はる[春]</kun><b><kun> さめ[雨]</kun></b>",
        },
        id="sound change readings 4/",
    ),
    pytest.param(
        "雨",
        # あめ -> あま
        "雨傘[あまがさ]",
        True,
        {
            "kana_only": "<b>あま</b>がさ",
            "furigana": "<b> 雨[あま]</b> 傘[がさ]",
            "furikanji": "<b> あま[雨]</b> がさ[傘]",
            "kana_only split": "<b><kun>あま</kun></b><kun>がさ</kun>",
            "furigana split": "<b><kun> 雨[あま]</kun></b><kun> 傘[がさ]</kun>",
            "furikanji split": "<b><kun> あま[雨]</kun></b><kun> がさ[傘]</kun>",
            "kana_only merged": "<b><kun>あま</kun></b><kun>がさ</kun>",
            "furigana merged": "<b><kun> 雨[あま]</kun></b><kun> 傘[がさ]</kun>",
            "furikanji merged": "<b><kun> あま[雨]</kun></b><kun> がさ[傘]</kun>",
        },
        id="sound change readings 5/",
    ),
    pytest.param(
        "酒",
        # さけ -> さか
        "居酒屋[いざかや]",
        True,
        {
            "kana_only": "い<b>ざか</b>や",
            "furigana": " 居[い]<b> 酒[ざか]</b> 屋[や]",
            "furikanji": " い[居]<b> ざか[酒]</b> や[屋]",
            "kana_only split": "<kun>い</kun><b><kun>ざか</kun></b><kun>や</kun>",
            "furigana split": "<kun> 居[い]</kun><b><kun> 酒[ざか]</kun></b><kun> 屋[や]</kun>",
            "furikanji split": "<kun> い[居]</kun><b><kun> ざか[酒]</kun></b><kun> や[屋]</kun>",
            "kana_only merged": "<kun>い</kun><b><kun>ざか</kun></b><kun>や</kun>",
            "furigana merged": "<kun> 居[い]</kun><b><kun> 酒[ざか]</kun></b><kun> 屋[や]</kun>",
            "furikanji merged": "<kun> い[居]</kun><b><kun> ざか[酒]</kun></b><kun> や[屋]</kun>",
        },
        id="sound change readings 6/",
    ),
    pytest.param(
        "応",
        # おう -> のう
        "反応[はんのう]",
        True,
        {
            "kana_only": "ハン<b>ノウ</b>",
            "furigana": " 反[ハン]<b> 応[ノウ]</b>",
            "furikanji": " ハン[反]<b> ノウ[応]</b>",
            "kana_only split": "<on>ハン</on><b><on>ノウ</on></b>",
            "furigana split": "<on> 反[ハン]</on><b><on> 応[ノウ]</on></b>",
            "furikanji split": "<on> ハン[反]</on><b><on> ノウ[応]</on></b>",
            "kana_only merged": "<on>ハン</on><b><on>ノウ</on></b>",
            "furigana merged": "<on> 反[ハン]</on><b><on> 応[ノウ]</on></b>",
            "furikanji merged": "<on> ハン[反]</on><b><on> ノウ[応]</on></b>",
        },
        id="sound change readings 7/",
    ),
    pytest.param(
        "皇",
        # おう -> のう
        "天皇[てんのう]",
        True,
        {
            "kana_only": "テン<b>ノウ</b>",
            "furigana": " 天[テン]<b> 皇[ノウ]</b>",
            "furikanji": " テン[天]<b> ノウ[皇]</b>",
            "kana_only split": "<on>テン</on><b><on>ノウ</on></b>",
            "furigana split": "<on> 天[テン]</on><b><on> 皇[ノウ]</on></b>",
            "furikanji split": "<on> テン[天]</on><b><on> ノウ[皇]</on></b>",
            "kana_only merged": "<on>テン</on><b><on>ノウ</on></b>",
            "furigana merged": "<on> 天[テン]</on><b><on> 皇[ノウ]</on></b>",
            "furikanji merged": "<on> テン[天]</on><b><on> ノウ[皇]</on></b>",
        },
        id="sound change readings 8/",
    ),
    pytest.param(
        "者",
        # もの -> もん
        "馬鹿者[ばかもん]",
        True,
        {
            "kana_only": "バか<b>もん</b>",
            "furigana": " 馬鹿[バか]<b> 者[もん]</b>",
            "furikanji": " バか[馬鹿]<b> もん[者]</b>",
            "kana_only split": "<on>バ</on><kun>か</kun><b><kun>もん</kun></b>",
            "furigana split": "<on> 馬[バ]</on><kun> 鹿[か]</kun><b><kun> 者[もん]</kun></b>",
            "furikanji split": "<on> バ[馬]</on><kun> か[鹿]</kun><b><kun> もん[者]</kun></b>",
            "kana_only merged": "<on>バ</on><kun>か</kun><b><kun>もん</kun></b>",
            "furigana merged": "<on> 馬[バ]</on><kun> 鹿[か]</kun><b><kun> 者[もん]</kun></b>",
            "furikanji merged": "<on> バ[馬]</on><kun> か[鹿]</kun><b><kun> もん[者]</kun></b>",
        },
        id="sound change readings 9/",
    ),
    pytest.param(
        "裸",
        # はだか -> はだ
        "裸足[はだあし]",
        True,
        {
            "kana_only": "<b>はだ</b>あし",
            "furigana": "<b> 裸[はだ]</b> 足[あし]",
            "furikanji": "<b> はだ[裸]</b> あし[足]",
            "kana_only split": "<b><kun>はだ</kun></b><kun>あし</kun>",
            "furigana split": "<b><kun> 裸[はだ]</kun></b><kun> 足[あし]</kun>",
            "furikanji split": "<b><kun> はだ[裸]</kun></b><kun> あし[足]</kun>",
            "kana_only merged": "<b><kun>はだ</kun></b><kun>あし</kun>",
            "furigana merged": "<b><kun> 裸[はだ]</kun></b><kun> 足[あし]</kun>",
            "furikanji merged": "<b><kun> はだ[裸]</kun></b><kun> あし[足]</kun>",
        },
        id="sound dropped readings 1/",
    ),
    pytest.param(
        "原",
        # はら -> は
        "河原[かわら]",
        True,
        {
            "kana_only": "かわ<b>ら</b>",
            "furigana": " 河[かわ]<b> 原[ら]</b>",
            "furikanji": " かわ[河]<b> ら[原]</b>",
            "kana_only split": "<kun>かわ</kun><b><kun>ら</kun></b>",
            "furigana split": "<kun> 河[かわ]</kun><b><kun> 原[ら]</kun></b>",
            "furikanji split": "<kun> かわ[河]</kun><b><kun> ら[原]</kun></b>",
            "kana_only merged": "<kun>かわ</kun><b><kun>ら</kun></b>",
            "furigana merged": "<kun> 河[かわ]</kun><b><kun> 原[ら]</kun></b>",
            "furikanji merged": "<kun> かわ[河]</kun><b><kun> ら[原]</kun></b>",
        },
        id="sound dropped readings 2/",
    ),
    pytest.param(
        "胡",
        # Likely by 黄[き] + 瓜[うり] forming 黄瓜[きゅうり] through sound fusion
        # 胡瓜 is read as きゅうり making 胡[きゅ] techinically jukujikun
        # However, since 瓜[うり] is a normal kunyomi reading, 黄瓜[きゅうり] can't be considered
        # jukujikun, thus we'll note 胡[きゅ] as a kunyomi
        "胡瓜[きゅうり]",
        True,
        {
            "kana_only": "<b>きゅ</b>うり",
            "furigana": "<b> 胡[きゅ]</b> 瓜[うり]",
            "furikanji": "<b> きゅ[胡]</b> うり[瓜]",
            "kana_only split": "<b><kun>きゅ</kun></b><kun>うり</kun>",
            "furigana split": "<b><kun> 胡[きゅ]</kun></b><kun> 瓜[うり]</kun>",
            "furikanji split": "<b><kun> きゅ[胡]</kun></b><kun> うり[瓜]</kun>",
            "kana_only merged": "<b><kun>きゅ</kun></b><kun>うり</kun>",
            "furigana merged": "<b><kun> 胡[きゅ]</kun></b><kun> 瓜[うり]</kun>",
            "furikanji merged": "<b><kun> きゅ[胡]</kun></b><kun> うり[瓜]</kun>",
        },
        id="sound fusion readings 1/",
    ),
    pytest.param(
        "狩",
        "狩人[かりゅうど]",
        True,
        {
            "kana_only": "<b>かりゅ</b>うど",
            "furigana": "<b> 狩[かりゅ]</b> 人[うど]",
            "furikanji": "<b> かりゅ[狩]</b> うど[人]",
            "kana_only split": "<b><kun>かりゅ</kun></b><kun>うど</kun>",
            "furigana split": "<b><kun> 狩[かりゅ]</kun></b><kun> 人[うど]</kun>",
            "furikanji split": "<b><kun> かりゅ[狩]</kun></b><kun> うど[人]</kun>",
            "kana_only merged": "<b><kun>かりゅ</kun></b><kun>うど</kun>",
            "furigana merged": "<b><kun> 狩[かりゅ]</kun></b><kun> 人[うど]</kun>",
            "furikanji merged": "<b><kun> かりゅ[狩]</kun></b><kun> うど[人]</kun>",
        },
        id="sound fusion readings 2/",
    ),
    pytest.param(
        # 祖 usually only lists ソ as the only onyomi
        "祖",
        "先祖[せんぞ]",
        True,
        {
            "kana_only": "セン<b>ゾ</b>",
            "furigana": " 先[セン]<b> 祖[ゾ]</b>",
            "furikanji": " セン[先]<b> ゾ[祖]</b>",
            "kana_only split": "<on>セン</on><b><on>ゾ</on></b>",
            "furigana split": "<on> 先[セン]</on><b><on> 祖[ゾ]</on></b>",
            "furikanji split": "<on> セン[先]</on><b><on> ゾ[祖]</on></b>",
            "kana_only merged": "<on>セン</on><b><on>ゾ</on></b>",
            "furigana merged": "<on> 先[セン]</on><b><on> 祖[ゾ]</on></b>",
            "furikanji merged": "<on> セン[先]</on><b><on> ゾ[祖]</on></b>",
        },
        id="Single kana reading conversion 1/",
    ),
    pytest.param(
        "来",
        "それは 私[わたし]たちの 日常生活[にちじょうせいかつ]の 仕来[しき]たりの １[ひと]つだ。",
        True,
        {
            "kana_only": "それは わたしたちの ニチジョウセイカツの シ<b>きたり</b>の ひとつだ。",
            "furigana": "それは 私[わたし]たちの 日常生活[ニチジョウセイカツ]の 仕[シ]<b>"
            " 来[き]たり</b>の １[ひと]つだ。",
            "furikanji": "それは わたし[私]たちの ニチジョウセイカツ[日常生活]の シ[仕]<b>"
            " き[来]たり</b>の ひと[１]つだ。",
            "kana_only split": "それは <kun>わたし</kun>たちの <on>ニチ</on><on>ジョウ</on><on>セイ</on><on>カツ</on>の "
            "<on>シ</on><b><kun>き</kun><oku>たり</oku></b>の <kun>ひと</kun><oku>つ</oku>だ。",
            "furigana split": "それは<kun> 私[わたし]</kun>たちの<on> 日[ニチ]</on><on> 常[ジョウ]</on><on>"
            " 生[セイ]</on>"
            "<on> 活[カツ]</on>の<on> 仕[シ]</on><b><kun> 来[き]</kun><oku>たり</oku></b>の<kun>"
            " １[ひと]</kun>"
            "<oku>つ</oku>だ。",
            "furikanji split": "それは<kun> わたし[私]</kun>たちの<on> ニチ[日]</on><on> ジョウ[常]</on><on>"
            " セイ[生]</on>"
            "<on> カツ[活]</on>の<on> シ[仕]</on><b><kun> き[来]</kun><oku>たり</oku></b>の<kun>"
            " ひと[１]</kun>"
            "<oku>つ</oku>だ。",
            "kana_only merged": "それは <kun>わたし</kun>たちの <on>ニチジョウセイカツ</on>の"
            " <on>シ</on><b><kun>き</kun><oku>たり</oku></b>の "
            "<kun>ひと</kun><oku>つ</oku>だ。",
            "furigana merged": "それは<kun> 私[わたし]</kun>たちの<on> 日常生活[ニチジョウセイカツ]</on>の"
            "<on> 仕[シ]</on><b><kun> 来[き]</kun><oku>たり</oku></b>の<kun> １[ひと]</kun>"
            "<oku>つ</oku>だ。",
            "furikanji merged": "それは<kun> わたし[私]</kun>たちの<on> ニチジョウセイカツ[日常生活]</on>の"
            "<on> シ[仕]</on><b><kun> き[来]</kun><oku>たり</oku></b>の<kun> ひと[１]</kun>"
            "<oku>つ</oku>だ。",
        },
        id="Single kana reading conversion 2/",
    ),
    pytest.param(
        # 不 has two matching onyomi フ and フウ and but フ is the correct reading for 不運
        "不",
        "不運[ふうん]",
        True,
        {
            "kana_only": "<b>フ</b>ウン",
            "furigana": "<b> 不[フ]</b> 運[ウン]",
            "furikanji": "<b> フ[不]</b> ウン[運]",
            "kana_only split": "<b><on>フ</on></b><on>ウン</on>",
            "kana_only merged": "<b><on>フ</on></b><on>ウン</on>",
            "furigana split": "<b><on> 不[フ]</on></b><on> 運[ウン]</on>",
            "furikanji split": "<b><on> フ[不]</on></b><on> ウン[運]</on>",
            "furigana merged": "<b><on> 不[フ]</on></b><on> 運[ウン]</on>",
            "furikanji merged": "<b><on> フ[不]</on></b><on> ウン[運]</on>",
        },
        id="word where shorter reading is correct 1/",
    ),
    pytest.param(
        "大",
        "大人[おとな] 達[たち]は 大[おお]きいですね",
        True,
        {
            "kana_only": "<b>おと</b>な タチは <b>おおきい</b>ですね",
            "furigana": "<b> 大[おと]</b> 人[な] 達[タチ]は<b> 大[おお]きい</b>ですね",
            "furikanji": "<b> おと[大]</b> な[人] タチ[達]は<b> おお[大]きい</b>ですね",
            "kana_only split": "<b><juk>おと</juk></b><juk>な</juk> <on>タチ</on>は"
            " <b><kun>おお</kun><oku>きい</oku></b>ですね",
            "furigana split": "<b><juk> 大[おと]</juk></b><juk> 人[な]</juk><on> 達[タチ]</on>は<b><kun>"
            " 大[おお]</kun><oku>きい</oku></b>ですね",
            "furikanji split": "<b><juk> おと[大]</juk></b><juk> な[人]</juk><on> タチ[達]</on>は<b><kun>"
            " おお[大]</kun><oku>きい</oku></b>ですね",
            "kana_only merged": "<b><juk>おと</juk></b><juk>な</juk> <on>タチ</on>は"
            " <b><kun>おお</kun><oku>きい</oku></b>ですね",
            "furigana merged": "<b><juk> 大[おと]</juk></b><juk> 人[な]</juk><on> 達[タチ]</on>は<b><kun>"
            " 大[おお]</kun><oku>きい</oku></b>ですね",
            "furikanji merged": "<b><juk> おと[大]</juk></b><juk> な[人]</juk><on> タチ[達]</on>は<b><kun>"
            " おお[大]</kun><oku>きい</oku></b>ですね",
        },
        id="jukujikun test 大人 1/",
    ),
    pytest.param(
        "人",
        "大人[おとな] 達[たち]は 人々[ひとびと]の 中[なか]に いる。",
        True,
        {
            "kana_only": "おと<b>な</b> タチは <b>ひとびと</b>の なかに いる。",
            "furigana": " 大[おと]<b> 人[な]</b> 達[タチ]は<b> 人々[ひとびと]</b>の 中[なか]に いる。",
            "furikanji": " おと[大]<b> な[人]</b> タチ[達]は<b> ひとびと[人々]</b>の なか[中]に いる。",
            "kana_only split": "<juk>おと</juk><b><juk>な</juk></b> <on>タチ</on>は <b><kun>ひとびと</kun></b>の"
            " <kun>なか</kun>に いる。",
            "furigana split": "<juk> 大[おと]</juk><b><juk> 人[な]</juk></b><on> 達[タチ]</on>は<b><kun>"
            " 人々[ひとびと]</kun></b>"
            "の<kun> 中[なか]</kun>に いる。",
            "furikanji split": "<juk> おと[大]</juk><b><juk> な[人]</juk></b><on> タチ[達]</on>は<b><kun>"
            " ひとびと[人々]</kun></b>"
            "の<kun> なか[中]</kun>に いる。",
            "kana_only merged": "<juk>おと</juk><b><juk>な</juk></b> <on>タチ</on>は <b><kun>ひとびと</kun></b>の"
            " <kun>なか</kun>に いる。",
            "furigana merged": "<juk> 大[おと]</juk><b><juk> 人[な]</juk></b><on> 達[タチ]</on>は<b><kun>"
            " 人々[ひとびと]</kun></b>"
            "の<kun> 中[なか]</kun>に いる。",
            "furikanji merged": "<juk> おと[大]</juk><b><juk> な[人]</juk></b><on> タチ[達]</on>は<b><kun>"
            " ひとびと[人々]</kun></b>"
            "の<kun> なか[中]</kun>に いる。",
        },
        id="jukujikun test 大人 2/",
    ),
    pytest.param(
        "展",
        "昨日[きのう]、 絵[え]の 展覧[てんらん] 会[かい]に 行[い]ってきました。",
        True,
        {
            "kana_only": "きのう、 エの <b>テン</b>ラン カイに いってきました。",
            "furigana": " 昨日[きのう]、 絵[エ]の<b> 展[テン]</b> 覧[ラン] 会[カイ]に 行[い]ってきました。",
            "furikanji": " きのう[昨日]、 エ[絵]の<b> テン[展]</b> ラン[覧] カイ[会]に い[行]ってきました。",
            "kana_only split": "<juk>きの</juk><juk>う</juk>、 <on>エ</on>の <b><on>テン</on></b><on>ラン</on>"
            " <on>カイ</on>に <kun>い</kun><oku>って</oku>きました。",
            "furigana split": "<juk> 昨[きの]</juk><juk> 日[う]</juk>、<on> 絵[エ]</on>の<b><on> 展[テン]</on></b>"
            "<on> 覧[ラン]</on><on> 会[カイ]</on>に<kun> 行[い]</kun><oku>って</oku>きました。",
            "furikanji split": "<juk> きの[昨]</juk><juk> う[日]</juk>、<on> エ[絵]</on>の<b><on> テン[展]</on></b>"
            "<on> ラン[覧]</on><on> カイ[会]</on>に<kun> い[行]</kun><oku>って</oku>きました。",
            "kana_only merged": "<juk>きのう</juk>、 <on>エ</on>の <b><on>テン</on></b><on>ラン</on>"
            " <on>カイ</on>に <kun>い</kun><oku>って</oku>きました。",
            "furigana merged": "<juk> 昨日[きのう]</juk>、<on> 絵[エ]</on>の<b><on> 展[テン]</on></b>"
            "<on> 覧[ラン]</on><on> 会[カイ]</on>に<kun> 行[い]</kun><oku>って</oku>きました。",
            "furikanji merged": "<juk> きのう[昨日]</juk>、<on> エ[絵]</on>の<b><on> テン[展]</on></b>"
            "<on> ラン[覧]</on><on> カイ[会]</on>に<kun> い[行]</kun><oku>って</oku>きました。",
        },
        id="jukujikun test 昨日",
    ),
    pytest.param(
        "明",
        "明々後日[しあさって]",
        True,
        {
            "kana_only": "<b>しあ</b>さって",
            "furigana": "<b> 明々[しあ]</b> 後日[さって]",
            "furikanji": "<b> しあ[明々]</b> さって[後日]",
            "kana_only split": "<b><juk>しあ</juk></b><juk>さっ</juk><juk>て</juk>",
            "furigana split": "<b><juk> 明々[しあ]</juk></b><juk> 後[さっ]</juk><juk> 日[て]</juk>",
            "furikanji split": "<b><juk> しあ[明々]</juk></b><juk> さっ[後]</juk><juk> て[日]</juk>",
            "kana_only merged": "<b><juk>しあ</juk></b><juk>さって</juk>",
            "furigana merged": "<b><juk> 明々[しあ]</juk></b><juk> 後日[さって]</juk>",
            "furikanji merged": "<b><juk> しあ[明々]</juk></b><juk> さって[後日]</juk>",
        },
        id="jukujikun test with repeater 明々後日",
    ),
    pytest.param(
        "後",
        # Problem with あ.かり getting kunyomi match on 明, so the reading is not fully
        # correctly identified as jukujikun
        "明後日[あさって]",
        True,
        {
            "kana_only": "あ<b>さっ</b>て",
            "furigana": " 明[あ]<b> 後[さっ]</b> 日[て]",
            "furikanji": " あ[明]<b> さっ[後]</b> て[日]",
            "kana_only split": "<kun>あ</kun><b><juk>さっ</juk></b><juk>て</juk>",
            "furigana split": "<kun> 明[あ]</kun><b><juk> 後[さっ]</juk></b><juk> 日[て]</juk>",
            "furikanji split": "<kun> あ[明]</kun><b><juk> さっ[後]</juk></b><juk> て[日]</juk>",
            "kana_only merged": "<kun>あ</kun><b><juk>さっ</juk></b><juk>て</juk>",
            "furigana merged": "<kun> 明[あ]</kun><b><juk> 後[さっ]</juk></b><juk> 日[て]</juk>",
            "furikanji merged": "<kun> あ[明]</kun><b><juk> さっ[後]</juk></b><juk> て[日]</juk>",
        },
        id="jukujikun test 明後日",
    ),
    pytest.param(
        "",
        " 清清[すがすが]しい",
        True,
        {
            "kana_only": " すがすがしい",
            "furigana": " 清々[すがすが]しい",
            "furikanji": " すがすが[清々]しい",
            "kana_only split": " <juk>すがすが</juk><oku>しい</oku>",
            "furigana split": "<juk> 清々[すがすが]</juk><oku>しい</oku>",
            "furikanji split": "<juk> すがすが[清々]</juk><oku>しい</oku>",
            "kana_only merged": " <juk>すがすが</juk><oku>しい</oku>",
            "furigana merged": "<juk> 清々[すがすが]</juk><oku>しい</oku>",
            "furikanji merged": "<juk> すがすが[清々]</juk><oku>しい</oku>",
        },
        id="jukujikun test 清々しい no highlight",
    ),
    pytest.param(
        "清",
        "清清[すがすが]しい",
        True,
        {
            "kana_only": "<b>すがすがしい</b>",
            "furigana": "<b> 清々[すがすが]しい</b>",
            "furikanji": "<b> すがすが[清々]しい</b>",
            "kana_only split": "<b><juk>すがすが</juk><oku>しい</oku></b>",
            "furigana split": "<b><juk> 清々[すがすが]</juk><oku>しい</oku></b>",
            "furikanji split": "<b><juk> すがすが[清々]</juk><oku>しい</oku></b>",
            "kana_only merged": "<b><juk>すがすが</juk><oku>しい</oku></b>",
            "furigana merged": "<b><juk> 清々[すがすが]</juk><oku>しい</oku></b>",
            "furikanji merged": "<b><juk> すがすが[清々]</juk><oku>しい</oku></b>",
        },
        id="jukujikun test 清々しい with highlight",
    ),
    pytest.param(
        "",
        "趙清々[ちょうすがすが]しい",
        True,
        {
            "kana_only": "チョウすがすがしい",
            "furigana": " 趙清々[チョウすがすが]しい",
            "furikanji": " チョウすがすが[趙清々]しい",
            "kana_only split": "<on>チョウ</on><juk>すがすが</juk><oku>しい</oku>",
            "furigana split": "<on> 趙[チョウ]</on><juk> 清々[すがすが]</juk><oku>しい</oku>",
            "furikanji split": "<on> チョウ[趙]</on><juk> すがすが[清々]</juk><oku>しい</oku>",
            "kana_only merged": "<on>チョウ</on><juk>すがすが</juk><oku>しい</oku>",
            "furigana merged": "<on> 趙[チョウ]</on><juk> 清々[すがすが]</juk><oku>しい</oku>",
            "furikanji merged": "<on> チョウ[趙]</on><juk> すがすが[清々]</juk><oku>しい</oku>",
        },
        id="jukujikun test 清々しい with another word at left - no highlight",
    ),
    pytest.param(
        "清",
        "趙清々[ちょうすがすが]しい",
        True,
        {
            "kana_only": "チョウ<b>すがすがしい</b>",
            "furigana": " 趙[チョウ]<b> 清々[すがすが]しい</b>",
            "furikanji": " チョウ[趙]<b> すがすが[清々]しい</b>",
            "kana_only split": "<on>チョウ</on><b><juk>すがすが</juk><oku>しい</oku></b>",
            "furigana split": "<on> 趙[チョウ]</on><b><juk> 清々[すがすが]</juk><oku>しい</oku></b>",
            "furikanji split": "<on> チョウ[趙]</on><b><juk> すがすが[清々]</juk><oku>しい</oku></b>",
            "kana_only merged": "<on>チョウ</on><b><juk>すがすが</juk><oku>しい</oku></b>",
            "furigana merged": "<on> 趙[チョウ]</on><b><juk> 清々[すがすが]</juk><oku>しい</oku></b>",
            "furikanji merged": "<on> チョウ[趙]</on><b><juk> すがすが[清々]</juk><oku>しい</oku></b>",
        },
        id="jukujikun test 清々しい with another word at left - with highlight",
    ),
    pytest.param(
        "",
        "趙清々瑞々[ちょうすがすがみずみず]しい",
        True,
        {
            "kana_only": "チョウすがすがみずみずしい",
            "furigana": " 趙清々瑞々[チョウすがすがみずみず]しい",
            "furikanji": " チョウすがすがみずみず[趙清々瑞々]しい",
            "kana_only split": "<on>チョウ</on><juk>すがすが</juk><kun>みずみず</kun><oku>しい</oku>",
            "furigana split": "<on> 趙[チョウ]</on><juk> 清々[すがすが]</juk><kun> 瑞々[みずみず]</kun><oku>しい</oku>",
            "furikanji split": "<on> チョウ[趙]</on><juk> すがすが[清々]</juk><kun> みずみず[瑞々]</kun><oku>しい</oku>",
            "kana_only merged": "<on>チョウ</on><juk>すがすが</juk><kun>みずみず</kun><oku>しい</oku>",
            "furigana merged": "<on> 趙[チョウ]</on><juk> 清々[すがすが]</juk><kun> 瑞々[みずみず]</kun><oku>しい</oku>",
            "furikanji merged": "<on> チョウ[趙]</on><juk> すがすが[清々]</juk><kun> みずみず[瑞々]</kun><oku>しい</oku>",
        },
        id="jukujikun test 清々しい in middle of two words - no highlight",
    ),
    pytest.param(
        "清",
        "趙清々瑞々[ちょうすがすがみずみず]しい",
        True,
        {
            "kana_only": "チョウ<b>すがすが</b>みずみずしい",
            "furigana": " 趙[チョウ]<b> 清々[すがすが]</b> 瑞々[みずみず]しい",
            "furikanji": " チョウ[趙]<b> すがすが[清々]</b> みずみず[瑞々]しい",
            "kana_only split": "<on>チョウ</on><b><juk>すがすが</juk></b><kun>みずみず</kun><oku>しい</oku>",
            "furigana split": "<on> 趙[チョウ]</on><b><juk> 清々[すがすが]</juk></b><kun>"
            " 瑞々[みずみず]</kun><oku>しい</oku>",
            "furikanji split": "<on> チョウ[趙]</on><b><juk> すがすが[清々]</juk></b><kun>"
            " みずみず[瑞々]</kun><oku>しい</oku>",
            "kana_only merged": "<on>チョウ</on><b><juk>すがすが</juk></b><kun>みずみず</kun><oku>しい</oku>",
            "furigana merged": "<on> 趙[チョウ]</on><b><juk> 清々[すがすが]</juk></b><kun>"
            " 瑞々[みずみず]</kun><oku>しい</oku>",
            "furikanji merged": "<on> チョウ[趙]</on><b><juk> すがすが[清々]</juk></b><kun>"
            " みずみず[瑞々]</kun><oku>しい</oku>",
        },
        id="jukujikun test 清々しい in middle of two words - with highlight",
    ),
    pytest.param(
        "田",
        "田圃[たんぼ]",
        True,
        {
            "kana_only": "<b>たん</b>ボ",
            "furigana": "<b> 田[たん]</b> 圃[ボ]",
            "furikanji": "<b> たん[田]</b> ボ[圃]",
            "kana_only split": "<b><juk>たん</juk></b><on>ボ</on>",
            "furigana split": "<b><juk> 田[たん]</juk></b><on> 圃[ボ]</on>",
            "furikanji split": "<b><juk> たん[田]</juk></b><on> ボ[圃]</on>",
            "kana_only merged": "<b><juk>たん</juk></b><on>ボ</on>",
            "furigana merged": "<b><juk> 田[たん]</juk></b><on> 圃[ボ]</on>",
            "furikanji merged": "<b><juk> たん[田]</juk></b><on> ボ[圃]</on>",
        },
        id="jukujikun test 田圃",
    ),
    pytest.param(
        "魁",
        "花魁[おいらん]",
        True,
        {
            "kana_only": "おい<b>らん</b>",
            "furigana": " 花[おい]<b> 魁[らん]</b>",
            "furikanji": " おい[花]<b> らん[魁]</b>",
            "kana_only split": "<juk>おい</juk><b><juk>らん</juk></b>",
            "furigana split": "<juk> 花[おい]</juk><b><juk> 魁[らん]</juk></b>",
            "furikanji split": "<juk> おい[花]</juk><b><juk> らん[魁]</juk></b>",
            "kana_only merged": "<juk>おい</juk><b><juk>らん</juk></b>",
            "furigana merged": "<juk> 花[おい]</juk><b><juk> 魁[らん]</juk></b>",
            "furikanji merged": "<juk> おい[花]</juk><b><juk> らん[魁]</juk></b>",
        },
        id="jukujikun test ん ending",
    ),
    pytest.param(
        "何",
        "何方[どっち]",
        True,
        {
            "kana_only": "<b>どっ</b>ち",
            "furigana": "<b> 何[どっ]</b> 方[ち]",
            "furikanji": "<b> どっ[何]</b> ち[方]",
            "kana_only split": "<b><juk>どっ</juk></b><juk>ち</juk>",
            "furigana split": "<b><juk> 何[どっ]</juk></b><juk> 方[ち]</juk>",
            "furikanji split": "<b><juk> どっ[何]</juk></b><juk> ち[方]</juk>",
            "kana_only merged": "<b><juk>どっ</juk></b><juk>ち</juk>",
            "furigana merged": "<b><juk> 何[どっ]</juk></b><juk> 方[ち]</juk>",
            "furikanji merged": "<b><juk> どっ[何]</juk></b><juk> ち[方]</juk>",
        },
        id="jukujikun test with small っ - with highlight",
    ),
    pytest.param(
        "",
        "何方[どっち]",
        True,
        {
            "kana_only": "どっち",
            "furigana": " 何方[どっち]",
            "furikanji": " どっち[何方]",
            "kana_only split": "<juk>どっ</juk><juk>ち</juk>",
            "furigana split": "<juk> 何[どっ]</juk><juk> 方[ち]</juk>",
            "furikanji split": "<juk> どっ[何]</juk><juk> ち[方]</juk>",
            "kana_only merged": "<juk>どっち</juk>",
            "furigana merged": "<juk> 何方[どっち]</juk>",
            "furikanji merged": "<juk> どっち[何方]</juk>",
        },
        id="jukujikun test with small っ - no highlight",
    ),
    pytest.param(
        "気",
        "意気地[いくじ]",
        True,
        {
            "kana_only": "イ<b>く</b>ジ",
            "furigana": " 意[イ]<b> 気[く]</b> 地[ジ]",
            "furikanji": " イ[意]<b> く[気]</b> ジ[地]",
            "kana_only split": "<on>イ</on><b><juk>く</juk></b><on>ジ</on>",
            "furigana split": "<on> 意[イ]</on><b><juk> 気[く]</juk></b><on> 地[ジ]</on>",
            "furikanji split": "<on> イ[意]</on><b><juk> く[気]</juk></b><on> ジ[地]</on>",
            "kana_only merged": "<on>イ</on><b><juk>く</juk></b><on>ジ</on>",
            "furigana merged": "<on> 意[イ]</on><b><juk> 気[く]</juk></b><on> 地[ジ]</on>",
            "furikanji merged": "<on> イ[意]</on><b><juk> く[気]</juk></b><on> ジ[地]</on>",
        },
        id="single-kanji juku in middle of word",
    ),
    pytest.param(
        "百",
        # Made up word, are there any multi-kanji jukujikun words used like this?
        "赤百合花壇[あかゆりかだん]",
        True,
        {
            "kana_only": "あか<b>ゆ</b>りカダン",
            "furigana": " 赤[あか]<b> 百[ゆ]</b> 合花壇[りカダン]",
            "furikanji": " あか[赤]<b> ゆ[百]</b> りカダン[合花壇]",
            "kana_only split": "<kun>あか</kun><b><juk>ゆ</juk></b><juk>り</juk><on>カ</on><on>ダン</on>",
            "furigana split": "<kun> 赤[あか]</kun><b><juk> 百[ゆ]</juk></b><juk> 合[り]</juk><on>"
            " 花[カ]</on><on> 壇[ダン]</on>",
            "furikanji split": "<kun> あか[赤]</kun><b><juk> ゆ[百]</juk></b><juk> り[合]</juk><on>"
            " カ[花]</on><on> ダン[壇]</on>",
            "kana_only merged": "<kun>あか</kun><b><juk>ゆ</juk></b><juk>り</juk><on>カダン</on>",
            "furigana merged": "<kun> 赤[あか]</kun><b><juk> 百[ゆ]</juk></b><juk> 合[り]</juk><on>"
            " 花壇[カダン]</on>",
            "furikanji merged": "<kun> あか[赤]</kun><b><juk> ゆ[百]</juk></b><juk> り[合]</juk><on>"
            " カダン[花壇]</on>",
        },
        id="multi-kanji juku in middle of word matched left",
    ),
    pytest.param(
        "合",
        "赤百合花壇[あかゆりかだん]",
        True,
        {
            "kana_only": "あかゆ<b>り</b>カダン",
            "furigana": " 赤百[あかゆ]<b> 合[り]</b> 花壇[カダン]",
            "furikanji": " あかゆ[赤百]<b> り[合]</b> カダン[花壇]",
            "kana_only split": "<kun>あか</kun><juk>ゆ</juk><b><juk>り</juk></b><on>カ</on><on>ダン</on>",
            "furigana split": "<kun> 赤[あか]</kun><juk> 百[ゆ]</juk><b><juk> 合[り]</juk></b><on>"
            " 花[カ]</on><on> 壇[ダン]</on>",
            "furikanji split": "<kun> あか[赤]</kun><juk> ゆ[百]</juk><b><juk> り[合]</juk></b><on>"
            " カ[花]</on><on> ダン[壇]</on>",
            "kana_only merged": "<kun>あか</kun><juk>ゆ</juk><b><juk>り</juk></b><on>カダン</on>",
            "furigana merged": "<kun> 赤[あか]</kun><juk> 百[ゆ]</juk><b><juk> 合[り]</juk></b><on>"
            " 花壇[カダン]</on>",
            "furikanji merged": "<kun> あか[赤]</kun><juk> ゆ[百]</juk><b><juk> り[合]</juk></b><on>"
            " カダン[花壇]</on>",
        },
        id="multi-kanji juku in middle of word matched right",
    ),
    # The next three lock in the property that a partial alignment may not reorder the reading:
    # with onyomi_to_katakana off, the kana_only output has to be the furigana the user wrote,
    # character for character (plus the <b> tags, when a kanji is highlighted). 保 matches ほ in
    # all of them, so the jukujikun mora on either side of it must stay on their own side.
    pytest.param(
        "",
        # Made up word; the point is that 保[ほ] matches while nothing around it does
        "山川保田[ぱぴぷほぺぽ]",
        False,
        {
            "kana_only": "ぱぴぷほぺぽ",
            "kana_only split": "<juk>ぱぴ</juk><juk>ぷ</juk><on>ほ</on><juk>ぺぽ</juk>",
            "kana_only merged": "<juk>ぱぴぷ</juk><on>ほ</on><juk>ぺぽ</juk>",
            "furigana": " 山川保田[ぱぴぷほぺぽ]",
            "furigana split": "<juk> 山[ぱぴ]</juk><juk> 川[ぷ]</juk><on> 保[ほ]</on><juk> 田[ぺぽ]</juk>",
            "furigana merged": "<juk> 山川[ぱぴぷ]</juk><on> 保[ほ]</on><juk> 田[ぺぽ]</juk>",
            "furikanji": " ぱぴぷほぺぽ[山川保田]",
            "furikanji split": "<juk> ぱぴ[山]</juk><juk> ぷ[川]</juk><on> ほ[保]</on><juk> ぺぽ[田]</juk>",
            "furikanji merged": "<juk> ぱぴぷ[山川]</juk><on> ほ[保]</on><juk> ぺぽ[田]</juk>",
        },
        id="jukujikun runs on both sides of a matched kanji keep the reading order",
    ),
    pytest.param(
        "保",
        "山川保田[ぱぴぷほぺぽ]",
        False,
        {
            "kana_only": "ぱぴぷ<b>ほ</b>ぺぽ",
            "kana_only split": "<juk>ぱぴ</juk><juk>ぷ</juk><b><on>ほ</on></b><juk>ぺぽ</juk>",
            "kana_only merged": "<juk>ぱぴぷ</juk><b><on>ほ</on></b><juk>ぺぽ</juk>",
            "furigana": " 山川[ぱぴぷ]<b> 保[ほ]</b> 田[ぺぽ]",
            "furigana split": "<juk> 山[ぱぴ]</juk><juk> 川[ぷ]</juk><b><on> 保[ほ]</on></b><juk> 田[ぺぽ]</juk>",
            "furigana merged": "<juk> 山川[ぱぴぷ]</juk><b><on> 保[ほ]</on></b><juk> 田[ぺぽ]</juk>",
            "furikanji": " ぱぴぷ[山川]<b> ほ[保]</b> ぺぽ[田]",
            "furikanji split": "<juk> ぱぴ[山]</juk><juk> ぷ[川]</juk><b><on> ほ[保]</on></b><juk> ぺぽ[田]</juk>",
            "furikanji merged": "<juk> ぱぴぷ[山川]</juk><b><on> ほ[保]</on></b><juk> ぺぽ[田]</juk>",
        },
        id="jukujikun runs on both sides of a matched kanji keep the order with highlight",
    ),
    pytest.param(
        "",
        # Same, with the match early on so the runs around it have different lengths
        "山保川田[ぱほぴぷぺ]",
        False,
        {
            "kana_only": "ぱほぴぷぺ",
            "kana_only split": "<juk>ぱ</juk><on>ほ</on><juk>ぴぷ</juk><juk>ぺ</juk>",
            "kana_only merged": "<juk>ぱ</juk><on>ほ</on><juk>ぴぷぺ</juk>",
            "furigana": " 山保川田[ぱほぴぷぺ]",
            "furigana split": "<juk> 山[ぱ]</juk><on> 保[ほ]</on><juk> 川[ぴぷ]</juk><juk> 田[ぺ]</juk>",
            "furigana merged": "<juk> 山[ぱ]</juk><on> 保[ほ]</on><juk> 川田[ぴぷぺ]</juk>",
            "furikanji": " ぱほぴぷぺ[山保川田]",
            "furikanji split": "<juk> ぱ[山]</juk><on> ほ[保]</on><juk> ぴぷ[川]</juk><juk> ぺ[田]</juk>",
            "furikanji merged": "<juk> ぱ[山]</juk><on> ほ[保]</on><juk> ぴぷぺ[川田]</juk>",
        },
        id="jukujikun runs of uneven length around a matched kanji keep the reading order",
    ),
    pytest.param(
        "屋",
        "蕎麦屋[そばや]",
        True,
        {
            "kana_only": "そば<b>や</b>",
            "kana_only split": "<juk>そ</juk><juk>ば</juk><b><kun>や</kun></b>",
            "kana_only merged": "<juk>そば</juk><b><kun>や</kun></b>",
            "furigana": " 蕎麦[そば]<b> 屋[や]</b>",
            "furikanji": " そば[蕎麦]<b> や[屋]</b>",
            "furigana split": "<juk> 蕎[そ]</juk><juk> 麦[ば]</juk><b><kun> 屋[や]</kun></b>",
            "furikanji split": "<juk> そ[蕎]</juk><juk> ば[麦]</juk><b><kun> や[屋]</kun></b>",
            "furigana merged": "<juk> 蕎麦[そば]</juk><b><kun> 屋[や]</kun></b>",
            "furikanji merged": "<juk> そば[蕎麦]</juk><b><kun> や[屋]</kun></b>",
        },
        id="jukujikun test 蕎麦 not matched",
    ),
    pytest.param(
        "風",
        # 風 has the kunyomi かぜ, but 風邪 should be read as the jukujikun かぜ
        "風邪[かぜ]",
        True,
        {
            "kana_only": "<b>か</b>ぜ",
            "furigana": "<b> 風[か]</b> 邪[ぜ]",
            "furikanji": "<b> か[風]</b> ぜ[邪]",
            "kana_only split": "<b><juk>か</juk></b><juk>ぜ</juk>",
            "furigana split": "<b><juk> 風[か]</juk></b><juk> 邪[ぜ]</juk>",
            "furikanji split": "<b><juk> か[風]</juk></b><juk> ぜ[邪]</juk>",
            "kana_only merged": "<b><juk>か</juk></b><juk>ぜ</juk>",
            "furigana merged": "<b><juk> 風[か]</juk></b><juk> 邪[ぜ]</juk>",
            "furikanji merged": "<b><juk> か[風]</juk></b><juk> ぜ[邪]</juk>",
        },
        id="jukujikun test 風邪 matched",
    ),
    pytest.param(
        "引",
        # When not matched, jukujikun are automatically merged together
        # This is done intentionally in construct_wrapped_furi_word, so could be changed
        # Kind of makes sense you can't really choose which kanji matches with
        # which part of the furigana
        "風邪[かぜ]を引[ひ]いた。",
        True,
        {
            "kana_only": "かぜを<b>ひいた</b>。",
            "furigana": " 風邪[かぜ]を<b> 引[ひ]いた</b>。",
            "furikanji": " かぜ[風邪]を<b> ひ[引]いた</b>。",
            "kana_only split": "<juk>か</juk><juk>ぜ</juk>を<b><kun>ひ</kun><oku>いた</oku></b>。",
            "furigana split": "<juk> 風[か]</juk><juk> 邪[ぜ]</juk>を<b><kun> 引[ひ]</kun><oku>いた</oku></b>。",
            "furikanji split": "<juk> か[風]</juk><juk> ぜ[邪]</juk>を<b><kun> ひ[引]</kun><oku>いた</oku></b>。",
            "kana_only merged": "<juk>かぜ</juk>を<b><kun>ひ</kun><oku>いた</oku></b>。",
            "furigana merged": "<juk> 風邪[かぜ]</juk>を<b><kun> 引[ひ]</kun><oku>いた</oku></b>。",
            "furikanji merged": "<juk> かぜ[風邪]</juk>を<b><kun> ひ[引]</kun><oku>いた</oku></b>。",
        },
        id="jukujikun test 風邪 not matched",
    ),
    pytest.param(
        "襤",
        # 襤 has the kunyomi ぼろ, but 襤褸 should be read as the jukujikun ぼろ
        "襤褸[ぼろ]",
        True,
        {
            "kana_only": "<b>ぼ</b>ろ",
            "furigana": "<b> 襤[ぼ]</b> 褸[ろ]",
            "furikanji": "<b> ぼ[襤]</b> ろ[褸]",
            "kana_only split": "<b><juk>ぼ</juk></b><juk>ろ</juk>",
            "furigana split": "<b><juk> 襤[ぼ]</juk></b><juk> 褸[ろ]</juk>",
            "furikanji split": "<b><juk> ぼ[襤]</juk></b><juk> ろ[褸]</juk>",
            "kana_only merged": "<b><juk>ぼ</juk></b><juk>ろ</juk>",
            "furigana merged": "<b><juk> 襤[ぼ]</juk></b><juk> 褸[ろ]</juk>",
            "furikanji merged": "<b><juk> ぼ[襤]</juk></b><juk> ろ[褸]</juk>",
        },
        id="jukujikun test 襤褸 matched",
    ),
    pytest.param(
        "",
        "襤褸[ぼろ]",
        True,
        {
            "kana_only": "ぼろ",
            "furigana": " 襤褸[ぼろ]",
            "furikanji": " ぼろ[襤褸]",
            "kana_only split": "<juk>ぼ</juk><juk>ろ</juk>",
            "furigana split": "<juk> 襤[ぼ]</juk><juk> 褸[ろ]</juk>",
            "furikanji split": "<juk> ぼ[襤]</juk><juk> ろ[褸]</juk>",
            "kana_only merged": "<juk>ぼろ</juk>",
            "furigana merged": "<juk> 襤褸[ぼろ]</juk>",
            "furikanji merged": "<juk> ぼろ[襤褸]</juk>",
        },
        id="jukujikun test 襤褸 not matched",
    ),
    pytest.param(
        "",
        "襤褸襤褸[ぼろぼろ]",
        True,
        {
            "kana_only": "ぼろぼろ",
            "furigana": " 襤褸襤褸[ぼろぼろ]",
            "furikanji": " ぼろぼろ[襤褸襤褸]",
            "kana_only split": "<juk>ぼ</juk><juk>ろ</juk><juk>ぼ</juk><juk>ろ</juk>",
            "furigana split": "<juk> 襤[ぼ]</juk><juk> 褸[ろ]</juk><juk> 襤[ぼ]</juk><juk> 褸[ろ]</juk>",
            "furikanji split": "<juk> ぼ[襤]</juk><juk> ろ[褸]</juk><juk> ぼ[襤]</juk><juk> ろ[褸]</juk>",
            "kana_only merged": "<juk>ぼろぼろ</juk>",
            "furigana merged": "<juk> 襤褸襤褸[ぼろぼろ]</juk>",
            "furikanji merged": "<juk> ぼろぼろ[襤褸襤褸]</juk>",
        },
        id="jukujikun test 襤褸襤褸 not matched",
    ),
    pytest.param(
        "",
        "襤褸襤褸[ボロボロ]",
        True,
        {
            "kana_only": "ボロボロ",
            "furigana": " 襤褸襤褸[ボロボロ]",
            "furikanji": " ボロボロ[襤褸襤褸]",
            "kana_only split": "<juk>ボ</juk><juk>ロ</juk><juk>ボ</juk><juk>ロ</juk>",
            "furigana split": "<juk> 襤[ボ]</juk><juk> 褸[ロ]</juk><juk> 襤[ボ]</juk><juk> 褸[ロ]</juk>",
            "furikanji split": "<juk> ボ[襤]</juk><juk> ロ[褸]</juk><juk> ボ[襤]</juk><juk> ロ[褸]</juk>",
            "kana_only merged": "<juk>ボロボロ</juk>",
            "furigana merged": "<juk> 襤褸襤褸[ボロボロ]</juk>",
            "furikanji merged": "<juk> ボロボロ[襤褸襤褸]</juk>",
        },
        id="jukujikun test 襤褸襤褸 as katakana not matched",
    ),
    pytest.param(
        "買",
        "風邪薬[かぜぐすり]を買[か]った",
        True,
        {
            "kana_only": "かぜぐすりを<b>かった</b>",
            "furigana": " 風邪薬[かぜぐすり]を<b> 買[か]った</b>",
            "furikanji": " かぜぐすり[風邪薬]を<b> か[買]った</b>",
            "kana_only split": "<juk>か</juk><juk>ぜ</juk><kun>ぐすり</kun>を<b><kun>か</kun><oku>った</oku></b>",
            "furigana split": "<juk> 風[か]</juk><juk> 邪[ぜ]</juk><kun> 薬[ぐすり]</kun>を<b><kun>"
            " 買[か]</kun><oku>った</oku></b>",
            "furikanji split": "<juk> か[風]</juk><juk> ぜ[邪]</juk><kun> ぐすり[薬]</kun>を<b><kun>"
            " か[買]</kun><oku>った</oku></b>",
            "kana_only merged": "<juk>かぜ</juk><kun>ぐすり</kun>を<b><kun>か</kun><oku>った</oku></b>",
            "furigana merged": "<juk> 風邪[かぜ]</juk><kun> 薬[ぐすり]</kun>を<b><kun> 買[か]</kun><oku>った</oku></b>",
            "furikanji merged": "<juk> かぜ[風邪]</juk><kun> ぐすり[薬]</kun>を<b><kun> か[買]</kun><oku>った</oku></b>",
        },
        id="jukujikun test with other readings after juku word /1",
    ),
    pytest.param(
        "色",
        "薔薇色[ばらいろ]",
        True,
        {
            "kana_only": "ばら<b>いろ</b>",
            "furigana": " 薔薇[ばら]<b> 色[いろ]</b>",
            "furikanji": " ばら[薔薇]<b> いろ[色]</b>",
            "kana_only split": "<juk>ば</juk><juk>ら</juk><b><kun>いろ</kun></b>",
            "furigana split": "<juk> 薔[ば]</juk><juk> 薇[ら]</juk><b><kun> 色[いろ]</kun></b>",
            "furikanji split": "<juk> ば[薔]</juk><juk> ら[薇]</juk><b><kun> いろ[色]</kun></b>",
            "kana_only merged": "<juk>ばら</juk><b><kun>いろ</kun></b>",
            "furigana merged": "<juk> 薔薇[ばら]</juk><b><kun> 色[いろ]</kun></b>",
            "furikanji merged": "<juk> ばら[薔薇]</juk><b><kun> いろ[色]</kun></b>",
        },
        id="jukujikun test with other readings after juku word /2",
    ),
    pytest.param(
        "",
        # 路 has the kunyomi じ so this should be used to match over こうじ, so that that only juku
        # portion becomes うじ that would be assigned to 小
        "袋小路[ふくろこうじ]",
        True,
        {
            "kana_only": "ふくろこうじ",
            "furigana": " 袋小路[ふくろこうじ]",
            "furikanji": " ふくろこうじ[袋小路]",
            "kana_only split": "<kun>ふくろ</kun><juk>こう</juk><kun>じ</kun>",
            "furigana split": "<kun> 袋[ふくろ]</kun><juk> 小[こう]</juk><kun> 路[じ]</kun>",
            "furikanji split": "<kun> ふくろ[袋]</kun><juk> こう[小]</juk><kun> じ[路]</kun>",
            "kana_only merged": "<kun>ふくろ</kun><juk>こう</juk><kun>じ</kun>",
            "furigana merged": "<kun> 袋[ふくろ]</kun><juk> 小[こう]</juk><kun> 路[じ]</kun>",
            "furikanji merged": "<kun> ふくろ[袋]</kun><juk> こう[小]</juk><kun> じ[路]</kun>",
        },
        id="jukujikun test with other readings after juku word /3",
    ),
    pytest.param(
        "目",
        "真面目[まじめ]",
        True,
        {
            "kana_only": "まじ<b>め</b>",
            "furigana": " 真面[まじ]<b> 目[め]</b>",
            "furikanji": " まじ[真面]<b> め[目]</b>",
            "kana_only split": "<juk>ま</juk><juk>じ</juk><b><kun>め</kun></b>",
            "furigana split": "<juk> 真[ま]</juk><juk> 面[じ]</juk><b><kun> 目[め]</kun></b>",
            "furikanji split": "<juk> ま[真]</juk><juk> じ[面]</juk><b><kun> め[目]</kun></b>",
            "kana_only merged": "<juk>まじ</juk><b><kun>め</kun></b>",
            "furigana merged": "<juk> 真面[まじ]</juk><b><kun> 目[め]</kun></b>",
            "furikanji merged": "<juk> まじ[真面]</juk><b><kun> め[目]</kun></b>",
        },
        id="multi-kanji jukujikun word with other readings after juku word non-matched",
    ),
    pytest.param(
        "真",
        "真面目[まじめ]",
        True,
        {
            "kana_only": "<b>ま</b>じめ",
            "furigana": "<b> 真[ま]</b> 面目[じめ]",
            "furikanji": "<b> ま[真]</b> じめ[面目]",
            "kana_only split": "<b><juk>ま</juk></b><juk>じ</juk><kun>め</kun>",
            "furigana split": "<b><juk> 真[ま]</juk></b><juk> 面[じ]</juk><kun> 目[め]</kun>",
            "furikanji split": "<b><juk> ま[真]</juk></b><juk> じ[面]</juk><kun> め[目]</kun>",
            "kana_only merged": "<b><juk>ま</juk></b><juk>じ</juk><kun>め</kun>",
            "furigana merged": "<b><juk> 真[ま]</juk></b><juk> 面[じ]</juk><kun> 目[め]</kun>",
            "furikanji merged": "<b><juk> ま[真]</juk></b><juk> じ[面]</juk><kun> め[目]</kun>",
        },
        id="multi-kanji jukujikun word with other readings after juku word matched left ",
    ),
    pytest.param(
        "面",
        "真面目[まじめ]",
        True,
        {
            "kana_only": "ま<b>じ</b>め",
            "furigana": " 真[ま]<b> 面[じ]</b> 目[め]",
            "furikanji": " ま[真]<b> じ[面]</b> め[目]",
            "kana_only split": "<juk>ま</juk><b><juk>じ</juk></b><kun>め</kun>",
            "furigana split": "<juk> 真[ま]</juk><b><juk> 面[じ]</juk></b><kun> 目[め]</kun>",
            "furikanji split": "<juk> ま[真]</juk><b><juk> じ[面]</juk></b><kun> め[目]</kun>",
            "kana_only merged": "<juk>ま</juk><b><juk>じ</juk></b><kun>め</kun>",
            "furigana merged": "<juk> 真[ま]</juk><b><juk> 面[じ]</juk></b><kun> 目[め]</kun>",
            "furikanji merged": "<juk> ま[真]</juk><b><juk> じ[面]</juk></b><kun> め[目]</kun>",
        },
        id="multi-kanji jukujikun word with other readings after juku word matched right",
    ),
    pytest.param(
        "揶",
        "揶揄[からか]う",
        True,
        {
            "kana_only": "<b>から</b>かう",
            "furigana": "<b> 揶[から]</b> 揄[か]う",
            "furikanji": "<b> から[揶]</b> か[揄]う",
            "kana_only split": "<b><juk>から</juk></b><juk>か</juk><oku>う</oku>",
            "furigana split": "<b><juk> 揶[から]</juk></b><juk> 揄[か]</juk><oku>う</oku>",
            "furikanji split": "<b><juk> から[揶]</juk></b><juk> か[揄]</juk><oku>う</oku>",
            "kana_only merged": "<b><juk>から</juk></b><juk>か</juk><oku>う</oku>",
            "furigana merged": "<b><juk> 揶[から]</juk></b><juk> 揄[か]</juk><oku>う</oku>",
            "furikanji merged": "<b><juk> から[揶]</juk></b><juk> か[揄]</juk><oku>う</oku>",
        },
        id="multi-kanji jukujikun verb reading matched left",
    ),
    pytest.param(
        "揄",
        "揶揄[からか]う",
        True,
        {
            "kana_only": "から<b>かう</b>",
            "furigana": " 揶[から]<b> 揄[か]う</b>",
            "furikanji": " から[揶]<b> か[揄]う</b>",
            "kana_only split": "<juk>から</juk><b><juk>か</juk><oku>う</oku></b>",
            "furigana split": "<juk> 揶[から]</juk><b><juk> 揄[か]</juk><oku>う</oku></b>",
            "furikanji split": "<juk> から[揶]</juk><b><juk> か[揄]</juk><oku>う</oku></b>",
            "kana_only merged": "<juk>から</juk><b><juk>か</juk><oku>う</oku></b>",
            "furigana merged": "<juk> 揶[から]</juk><b><juk> 揄[か]</juk><oku>う</oku></b>",
            "furikanji merged": "<juk> から[揶]</juk><b><juk> か[揄]</juk><oku>う</oku></b>",
        },
        id="multi-kanji jukujikun verb reading matched right",
    ),
    pytest.param(
        "",
        "聴牌[テンパ]ってた",
        True,
        {
            "kana_only": "テンパってた",
            "furigana": " 聴牌[テンパ]ってた",
            "furikanji": " テンパ[聴牌]ってた",
            "kana_only split": "<juk>テン</juk><juk>パ</juk><oku>ってた</oku>",
            "furigana split": "<juk> 聴[テン]</juk><juk> 牌[パ]</juk><oku>ってた</oku>",
            "furikanji split": "<juk> テン[聴]</juk><juk> パ[牌]</juk><oku>ってた</oku>",
            "kana_only merged": "<juk>テンパ</juk><oku>ってた</oku>",
            "furigana merged": "<juk> 聴牌[テンパ]</juk><oku>ってた</oku>",
            "furikanji merged": "<juk> テンパ[聴牌]</juk><oku>ってた</oku>",
        },
        id="multi-kanji jukujikun verb okurigana - not matched",
    ),
    pytest.param(
        "端",
        "端折[はしょ]る",
        True,
        {
            "kana_only": "<b>はし</b>ょる",
            "kana_only split": "<b><kun>はし</kun></b><kun>ょ</kun><oku>る</oku>",
            "kana_only merged": "<b><kun>はし</kun></b><kun>ょ</kun><oku>る</oku>",
            "furigana": "<b> 端[はし]</b> 折[ょ]る",
            "furigana split": "<b><kun> 端[はし]</kun></b><kun> 折[ょ]</kun><oku>る</oku>",
            "furigana merged": "<b><kun> 端[はし]</kun></b><kun> 折[ょ]</kun><oku>る</oku>",
            "furikanji": "<b> はし[端]</b> ょ[折]る",
            "furikanji split": "<b><kun> はし[端]</kun></b><kun> ょ[折]</kun><oku>る</oku>",
            "furikanji merged": "<b><kun> はし[端]</kun></b><kun> ょ[折]</kun><oku>る</oku>",
        },
        id="Should be able to handle vowel change /1",
    ),
    pytest.param(
        "逆",
        # No kunyomi to match, the okurigana would need to be analyzed to get the dictionary form
        # and then determine where the okurigana ends
        "逆上[のぼ]せる",
        True,
        {
            # Only dictionary forms can be handled for now
            "kana_only": "<b>の</b>ぼせる",
            "furigana": "<b> 逆[の]</b> 上[ぼ]せる",
            "furikanji": "<b> の[逆]</b> ぼ[上]せる",
            "kana_only split": "<b><juk>の</juk></b><juk>ぼ</juk><oku>せる</oku>",
            "furigana split": "<b><juk> 逆[の]</juk></b><juk> 上[ぼ]</juk><oku>せる</oku>",
            "furikanji split": "<b><juk> の[逆]</juk></b><juk> ぼ[上]</juk><oku>せる</oku>",
            "kana_only merged": "<b><juk>の</juk></b><juk>ぼ</juk><oku>せる</oku>",
            "furigana merged": "<b><juk> 逆[の]</juk></b><juk> 上[ぼ]</juk><oku>せる</oku>",
            "furikanji merged": "<b><juk> の[逆]</juk></b><juk> ぼ[上]</juk><oku>せる</oku>",
        },
        id="Should be able to get dictionary form okurigana of jukujikun reading",
    ),
    pytest.param(
        "逆",
        "逆上[のぼ]せたので",
        True,
        {
            "kana_only": "<b>の</b>ぼせたので",
            "furigana": "<b> 逆[の]</b> 上[ぼ]せたので",
            "furikanji": "<b> の[逆]</b> ぼ[上]せたので",
            "kana_only split": "<b><juk>の</juk></b><juk>ぼ</juk><oku>せた</oku>ので",
            "furigana split": "<b><juk> 逆[の]</juk></b><juk> 上[ぼ]</juk><oku>せた</oku>ので",
            "furikanji split": "<b><juk> の[逆]</juk></b><juk> ぼ[上]</juk><oku>せた</oku>ので",
            "kana_only merged": "<b><juk>の</juk></b><juk>ぼ</juk><oku>せた</oku>ので",
            "furigana merged": "<b><juk> 逆[の]</juk></b><juk> 上[ぼ]</juk><oku>せた</oku>ので",
            "furikanji merged": "<b><juk> の[逆]</juk></b><juk> ぼ[上]</juk><oku>せた</oku>ので",
        },
        id="Should be able to get inflected okurigana of jukujikun reading",
    ),
    pytest.param(
        "",
        "不甲斐[ふがい]ない",
        False,
        {
            "kana_only": "ふがいない",
            "furigana": " 不甲斐[ふがい]ない",
            "furikanji": " ふがい[不甲斐]ない",
            "kana_only split": "<on>ふ</on><juk>が</juk><juk>い</juk>ない",
            "furigana split": "<on> 不[ふ]</on><juk> 甲[が]</juk><juk> 斐[い]</juk>ない",
            "furikanji split": "<on> ふ[不]</on><juk> が[甲]</juk><juk> い[斐]</juk>ない",
            "kana_only merged": "<on>ふ</on><juk>がい</juk>ない",
            "furigana merged": "<on> 不[ふ]</on><juk> 甲斐[がい]</juk>ない",
            "furikanji merged": "<on> ふ[不]</on><juk> がい[甲斐]</juk>ない",
        },
        id="Should not consider ない as okurigana in 不甲斐ない jukujikun reading",
    ),
    pytest.param(
        "",
        "美味[おい]しい",
        True,
        {
            "kana_only": "おいしい",
            "furigana": " 美味[おい]しい",
            "furikanji": " おい[美味]しい",
            "kana_only split": "<juk>お</juk><juk>い</juk><oku>しい</oku>",
            "furigana split": "<juk> 美[お]</juk><juk> 味[い]</juk><oku>しい</oku>",
            "furikanji split": "<juk> お[美]</juk><juk> い[味]</juk><oku>しい</oku>",
            "kana_only merged": "<juk>おい</juk><oku>しい</oku>",
            "furigana merged": "<juk> 美味[おい]</juk><oku>しい</oku>",
            "furikanji merged": "<juk> おい[美味]</juk><oku>しい</oku>",
        },
        id="Should be able to get okurigana for 美味しい jukujikun reading - no highlight /1",
    ),
    pytest.param(
        "",
        "美味[おい]しさがいい",
        True,
        {
            "kana_only": "おいしさがいい",
            "furigana": " 美味[おい]しさがいい",
            "furikanji": " おい[美味]しさがいい",
            "kana_only split": "<juk>お</juk><juk>い</juk><oku>しさ</oku>がいい",
            "furigana split": "<juk> 美[お]</juk><juk> 味[い]</juk><oku>しさ</oku>がいい",
            "furikanji split": "<juk> お[美]</juk><juk> い[味]</juk><oku>しさ</oku>がいい",
            "kana_only merged": "<juk>おい</juk><oku>しさ</oku>がいい",
            "furigana merged": "<juk> 美味[おい]</juk><oku>しさ</oku>がいい",
            "furikanji merged": "<juk> おい[美味]</juk><oku>しさ</oku>がいい",
        },
        id="Should be able to get okurigana for 美味しい jukujikun reading - no highlight /2",
    ),
    pytest.param(
        "釣",
        "釣瓶落[つるべお]とし",
        True,
        {
            "kana_only": "<b>つる</b>べおとし",
            "furigana": "<b> 釣[つる]</b> 瓶落[べお]とし",
            "furikanji": "<b> つる[釣]</b> べお[瓶落]とし",
            "kana_only split": "<b><kun>つる</kun></b><juk>べ</juk><kun>お</kun><oku>とし</oku>",
            "furigana split": "<b><kun> 釣[つる]</kun></b><juk> 瓶[べ]</juk><kun> 落[お]</kun><oku>とし</oku>",
            "furikanji split": "<b><kun> つる[釣]</kun></b><juk> べ[瓶]</juk><kun> お[落]</kun><oku>とし</oku>",
            "kana_only merged": "<b><kun>つる</kun></b><juk>べ</juk><kun>お</kun><oku>とし</oku>",
            "furigana merged": "<b><kun> 釣[つる]</kun></b><juk> 瓶[べ]</juk><kun> 落[お]</kun><oku>とし</oku>",
            "furikanji merged": "<b><kun> つる[釣]</kun></b><juk> べ[瓶]</juk><kun> お[落]</kun><oku>とし</oku>",
        },
        id="Match 釣瓶落とし jukujikun reading - with highlight",
    ),
    pytest.param(
        "",
        "釣瓶落[つるべお]とし",
        True,
        {
            "kana_only": "つるべおとし",
            "furigana": " 釣瓶落[つるべお]とし",
            "furikanji": " つるべお[釣瓶落]とし",
            "kana_only split": "<kun>つる</kun><juk>べ</juk><kun>お</kun><oku>とし</oku>",
            "furigana split": "<kun> 釣[つる]</kun><juk> 瓶[べ]</juk><kun> 落[お]</kun><oku>とし</oku>",
            "furikanji split": "<kun> つる[釣]</kun><juk> べ[瓶]</juk><kun> お[落]</kun><oku>とし</oku>",
            "kana_only merged": "<kun>つる</kun><juk>べ</juk><kun>お</kun><oku>とし</oku>",
            "furigana merged": "<kun> 釣[つる]</kun><juk> 瓶[べ]</juk><kun> 落[お]</kun><oku>とし</oku>",
            "furikanji merged": "<kun> つる[釣]</kun><juk> べ[瓶]</juk><kun> お[落]</kun><oku>とし</oku>",
        },
        id="Match 釣瓶落とし jukujikun reading - no highlight",
    ),
    pytest.param(
        "",
        # 菠 has onyomi reading ほ which should not match in this case
        "<k> 菠薐[ほうれん]</k> 草[そう]",
        False,
        {
            "kana_only": "<k> ほうれん</k> そう",
            "furigana": "<k> 菠薐[ほうれん]</k> 草[そう]",
            "furikanji": "<k> ほうれん[菠薐]</k> そう[草]",
            "kana_only split": "<k> <juk>ほう</juk><juk>れん</juk></k> <on>そう</on>",
            "furigana split": "<k><juk> 菠[ほう]</juk><juk> 薐[れん]</juk></k><on> 草[そう]</on>",
            "furikanji split": "<k><juk> ほう[菠]</juk><juk> れん[薐]</juk></k><on> そう[草]</on>",
            "kana_only merged": "<k> <juk>ほうれん</juk></k> <on>そう</on>",
            "furigana merged": "<k><juk> 菠薐[ほうれん]</juk></k><on> 草[そう]</on>",
            "furikanji merged": "<k><juk> ほうれん[菠薐]</juk></k><on> そう[草]</on>",
        },
        id="Should handle 菠薐草 correctly as jukujikun",
    ),
    pytest.param(
        "稚",
        "少[すこ]し 幼稚[ようち]だ",
        True,
        {
            "kana_only": "すこし ヨウ<b>チ</b>だ",
            "furigana": " 少[すこ]し 幼[ヨウ]<b> 稚[チ]</b>だ",
            "furikanji": " すこ[少]し ヨウ[幼]<b> チ[稚]</b>だ",
            "kana_only split": "<kun>すこ</kun><oku>し</oku> <on>ヨウ</on><b><on>チ</on></b>だ",
            "furigana split": "<kun> 少[すこ]</kun><oku>し</oku><on> 幼[ヨウ]</on><b><on> 稚[チ]</on></b>だ",
            "furikanji split": "<kun> すこ[少]</kun><oku>し</oku><on> ヨウ[幼]</on><b><on> チ[稚]</on></b>だ",
            "kana_only merged": "<kun>すこ</kun><oku>し</oku> <on>ヨウ</on><b><on>チ</on></b>だ",
            "furigana merged": "<kun> 少[すこ]</kun><oku>し</oku><on> 幼[ヨウ]</on><b><on> 稚[チ]</on></b>だ",
            "furikanji merged": "<kun> すこ[少]</kun><oku>し</oku><on> ヨウ[幼]</on><b><on> チ[稚]</on></b>だ",
        },
        id="Should not consider だ as okuri after onyomi noun - with highlight",
    ),
    pytest.param(
        "",
        "少[すこ]し 幼稚[ようち]だ",
        True,
        {
            "kana_only": "すこし ヨウチだ",
            "furigana": " 少[すこ]し 幼稚[ヨウチ]だ",
            "furikanji": " すこ[少]し ヨウチ[幼稚]だ",
            "kana_only split": "<kun>すこ</kun><oku>し</oku> <on>ヨウ</on><on>チ</on>だ",
            "furigana split": "<kun> 少[すこ]</kun><oku>し</oku><on> 幼[ヨウ]</on><on> 稚[チ]</on>だ",
            "furikanji split": "<kun> すこ[少]</kun><oku>し</oku><on> ヨウ[幼]</on><on> チ[稚]</on>だ",
            "kana_only merged": "<kun>すこ</kun><oku>し</oku> <on>ヨウチ</on>だ",
            "furigana merged": "<kun> 少[すこ]</kun><oku>し</oku><on> 幼稚[ヨウチ]</on>だ",
            "furikanji merged": "<kun> すこ[少]</kun><oku>し</oku><on> ヨウチ[幼稚]</on>だ",
        },
        id="Should not consider だ as okuri after onyomi noun - no highlight",
    ),
    pytest.param(
        "",
        # reading in katakana, with ー replacing ウ in the コウ onyomi for 高
        # the reading should be matched correctly but also preserved
        " 最高[サイコー]",
        False,
        {
            "kana_only": " サイコー",
            "furigana": " 最高[サイコー]",
            "furikanji": " サイコー[最高]",
            "kana_only split": " <on>サイ</on><on>コー</on>",
            "furigana split": "<on> 最[サイ]</on><on> 高[コー]</on>",
            "furikanji split": "<on> サイ[最]</on><on> コー[高]</on>",
            "kana_only merged": " <on>サイコー</on>",
            "furigana merged": "<on> 最高[サイコー]</on>",
            "furikanji merged": "<on> サイコー[最高]</on>",
        },
        id="Should convert long vowel mark ー to vowel kana in any readings, katakana furigana",
    ),
    pytest.param(
        "",
        " 最高[さいこー]",
        False,
        {
            "kana_only": " さいこー",
            "furigana": " 最高[さいこー]",
            "furikanji": " さいこー[最高]",
            "kana_only split": " <on>さい</on><on>こー</on>",
            "furigana split": "<on> 最[さい]</on><on> 高[こー]</on>",
            "furikanji split": "<on> さい[最]</on><on> こー[高]</on>",
            "kana_only merged": " <on>さいこー</on>",
            "furigana merged": "<on> 最高[さいこー]</on>",
            "furikanji merged": "<on> さいこー[最高]</on>",
        },
        id="Should convert long vowel mark ー to vowel kana in any readings, hiragana furigana",
    ),
    pytest.param(
        "高",
        " 最高[サイコー]",
        False,
        {
            "kana_only": " サイ<b>コー</b>",
            "furigana": " 最[サイ]<b> 高[コー]</b>",
            "furikanji": " サイ[最]<b> コー[高]</b>",
            "kana_only split": " <on>サイ</on><b><on>コー</on></b>",
            "furigana split": "<on> 最[サイ]</on><b><on> 高[コー]</on></b>",
            "furikanji split": "<on> サイ[最]</on><b><on> コー[高]</on></b>",
            "kana_only merged": " <on>サイ</on><b><on>コー</on></b>",
            "furigana merged": "<on> 最[サイ]</on><b><on> 高[コー]</on></b>",
            "furikanji merged": "<on> サイ[最]</on><b><on> コー[高]</on></b>",
        },
        id="Should convert long vowel mark ー to vowel kana in any readings, katakana furigana -"
        " with highlight",
    ),
    pytest.param(
        "高",
        " 最高[さいこー]",
        False,
        {
            "kana_only": " さい<b>こー</b>",
            "furigana": " 最[さい]<b> 高[こー]</b>",
            "furikanji": " さい[最]<b> こー[高]</b>",
            "kana_only split": " <on>さい</on><b><on>こー</on></b>",
            "furigana split": "<on> 最[さい]</on><b><on> 高[こー]</on></b>",
            "furikanji split": "<on> さい[最]</on><b><on> こー[高]</on></b>",
            "kana_only merged": " <on>さい</on><b><on>こー</on></b>",
            "furigana merged": "<on> 最[さい]</on><b><on> 高[こー]</on></b>",
            "furikanji merged": "<on> さい[最]</on><b><on> こー[高]</on></b>",
        },
        id="Should convert long vowel mark ー to vowel kana in any readings, hiragana furigana -"
        " with highlight",
    ),
    pytest.param(
        "生",
        "先生[せんせー]",
        False,
        {
            "furigana": " 先[せん]<b> 生[せー]</b>",
            "furigana split": "<on> 先[せん]</on><b><on> 生[せー]</on></b>",
            "furigana merged": "<on> 先[せん]</on><b><on> 生[せー]</on></b>",
            "furikanji": " せん[先]<b> せー[生]</b>",
            "furikanji split": "<on> せん[先]</on><b><on> せー[生]</on></b>",
            "furikanji merged": "<on> せん[先]</on><b><on> せー[生]</on></b>",
            "kana_only": "せん<b>せー</b>",
            "kana_only split": "<on>せん</on><b><on>せー</on></b>",
            "kana_only merged": "<on>せん</on><b><on>せー</on></b>",
        },
        id="Long vowel mark ー after an え-row kana matches an えい onyomi",
    ),
    pytest.param(
        "",
        "計画[けーかく]",
        True,
        {
            "furigana": " 計画[ケーカク]",
            "furigana split": "<on> 計[ケー]</on><on> 画[カク]</on>",
            "furigana merged": "<on> 計画[ケーカク]</on>",
            "furikanji": " ケーカク[計画]",
            "furikanji split": "<on> ケー[計]</on><on> カク[画]</on>",
            "furikanji merged": "<on> ケーカク[計画]</on>",
            "kana_only": "ケーカク",
            "kana_only split": "<on>ケー</on><on>カク</on>",
            "kana_only merged": "<on>ケーカク</on>",
        },
        id="Long vowel mark ー after け matches a けい onyomi",
    ),
    pytest.param(
        "婆",
        "お婆[ばー]ちゃん",
        True,
        {
            "furigana": "お<b> 婆[ばー]</b>ちゃん",
            "furigana split": "お<b><kun> 婆[ばー]</kun></b>ちゃん",
            "furigana merged": "お<b><kun> 婆[ばー]</kun></b>ちゃん",
            "furikanji": "お<b> ばー[婆]</b>ちゃん",
            "furikanji split": "お<b><kun> ばー[婆]</kun></b>ちゃん",
            "furikanji merged": "お<b><kun> ばー[婆]</kun></b>ちゃん",
            "kana_only": "お<b>ばー</b>ちゃん",
            "kana_only split": "お<b><kun>ばー</kun></b>ちゃん",
            "kana_only merged": "お<b><kun>ばー</kun></b>ちゃん",
        },
        id="Long vowel mark ー after an あ-row kana matches an ああ kunyomi",
    ),
    pytest.param(
        "",
        "東京[とーきょー]",
        True,
        {
            "furigana": " 東京[トーキョー]",
            "furigana split": "<on> 東[トー]</on><on> 京[キョー]</on>",
            "furigana merged": "<on> 東京[トーキョー]</on>",
            "furikanji": " トーキョー[東京]",
            "furikanji split": "<on> トー[東]</on><on> キョー[京]</on>",
            "furikanji merged": "<on> トーキョー[東京]</on>",
            "kana_only": "トーキョー",
            "kana_only split": "<on>トー</on><on>キョー</on>",
            "kana_only merged": "<on>トーキョー</on>",
        },
        id="Long vowel mark ー after a small ょ lengthens the palatalized mora",
    ),
    pytest.param(
        "",
        "炒麺[ちゃーめん]",
        True,
        {
            "kana_only": "ちゃーメン",
            "furigana": " 炒麺[ちゃーメン]",
            "furikanji": " ちゃーメン[炒麺]",
            "kana_only split": "<juk>ちゃー</juk><on>メン</on>",
            "furigana split": "<juk> 炒[ちゃー]</juk><on> 麺[メン]</on>",
            "furikanji split": "<juk> ちゃー[炒]</juk><on> メン[麺]</on>",
            "kana_only merged": "<juk>ちゃー</juk><on>メン</on>",
            "furigana merged": "<juk> 炒[ちゃー]</juk><on> 麺[メン]</on>",
            "furikanji merged": "<juk> ちゃー[炒]</juk><on> メン[麺]</on>",
        },
        id="jukujikun test with ー long vowel mark",
    ),
    pytest.param(
        "",
        "嗚呼[あー]",
        True,
        {
            "kana_only": "ああ",
            "furigana": " 嗚呼[ああ]",
            "furikanji": " ああ[嗚呼]",
            "kana_only split": "<juk>あ</juk><juk>あ</juk>",
            "furigana split": "<juk> 嗚[あ]</juk><juk> 呼[あ]</juk>",
            "furikanji split": "<juk> あ[嗚]</juk><juk> あ[呼]</juk>",
            "kana_only merged": "<juk>ああ</juk>",
            "furigana merged": "<juk> 嗚呼[ああ]</juk>",
            "furikanji merged": "<juk> ああ[嗚呼]</juk>",
        },
        id="should convert long vowel mark ー to vowel kana if not enough mora otherwise",
    ),
    pytest.param(
        "麻",
        "麻雀[まーじゃん]",
        True,
        {
            "kana_only": "<b>まー</b>じゃん",
            "furigana": "<b> 麻[まー]</b> 雀[じゃん]",
            "furikanji": "<b> まー[麻]</b> じゃん[雀]",
            "kana_only split": "<b><juk>まー</juk></b><juk>じゃん</juk>",
            "furigana split": "<b><juk> 麻[まー]</juk></b><juk> 雀[じゃん]</juk>",
            "furikanji split": "<b><juk> まー[麻]</juk></b><juk> じゃん[雀]</juk>",
            "kana_only merged": "<b><juk>まー</juk></b><juk>じゃん</juk>",
            "furigana merged": "<b><juk> 麻[まー]</juk></b><juk> 雀[じゃん]</juk>",
            "furikanji merged": "<b><juk> まー[麻]</juk></b><juk> じゃん[雀]</juk>",
        },
        id="ん should be combined with previous mora in jukujikun and handle long vowel mark ー",
    ),
    pytest.param(
        "曳",
        # ひ.く is a kunyomi for 曳 and both 曳き舟 and 曳船 are valid readings
        "曳船[ひきふね]",
        True,
        {
            "kana_only": "<b>ひき</b>ふね",
            "furigana": "<b> 曳[ひき]</b> 船[ふね]",
            "furikanji": "<b> ひき[曳]</b> ふね[船]",
            "kana_only split": "<b><kun>ひき</kun></b><kun>ふね</kun>",
            "furigana split": "<b><kun> 曳[ひき]</kun></b><kun> 船[ふね]</kun>",
            "furikanji split": "<b><kun> ひき[曳]</kun></b><kun> ふね[船]</kun>",
            "kana_only merged": "<b><kun>ひき</kun></b><kun>ふね</kun>",
            "furigana merged": "<b><kun> 曳[ひき]</kun></b><kun> 船[ふね]</kun>",
            "furikanji merged": "<b><kun> ひき[曳]</kun></b><kun> ふね[船]</kun>",
        },
        id="Should be able match noun form okuriganaless kunyomi reading 1/",
    ),
    pytest.param(
        "留",
        "書留[かきとめ]",
        True,
        {
            "kana_only": "かき<b>とめ</b>",
            "furigana": " 書[かき]<b> 留[とめ]</b>",
            "furikanji": " かき[書]<b> とめ[留]</b>",
            "kana_only split": "<kun>かき</kun><b><kun>とめ</kun></b>",
            "furigana split": "<kun> 書[かき]</kun><b><kun> 留[とめ]</kun></b>",
            "furikanji split": "<kun> かき[書]</kun><b><kun> とめ[留]</kun></b>",
            "kana_only merged": "<kun>かき</kun><b><kun>とめ</kun></b>",
            "furigana merged": "<kun> 書[かき]</kun><b><kun> 留[とめ]</kun></b>",
            "furikanji merged": "<kun> かき[書]</kun><b><kun> とめ[留]</kun></b>",
        },
        id="Should be able match noun form okuriganaless kunyomi reading 2/",
    ),
    pytest.param(
        "詣",
        "初詣[はつもうで]",
        True,
        {
            "kana_only": "はつ<b>もうで</b>",
            "kana_only split": "<kun>はつ</kun><b><kun>もうで</kun></b>",
            "kana_only merged": "<kun>はつ</kun><b><kun>もうで</kun></b>",
            "furigana": " 初[はつ]<b> 詣[もうで]</b>",
            "furigana split": "<kun> 初[はつ]</kun><b><kun> 詣[もうで]</kun></b>",
            "furigana merged": "<kun> 初[はつ]</kun><b><kun> 詣[もうで]</kun></b>",
            "furikanji": " はつ[初]<b> もうで[詣]</b>",
            "furikanji split": "<kun> はつ[初]</kun><b><kun> もうで[詣]</kun></b>",
            "furikanji merged": "<kun> はつ[初]</kun><b><kun> もうで[詣]</kun></b>",
        },
        id="Should be able match noun form okuriganaless kunyomi reading 3/",
    ),
    pytest.param(
        "刳",
        "刳[えぐ]み",
        True,
        {
            "kana_only": "<b>えぐみ</b>",
            "furigana": "<b> 刳[えぐ]み</b>",
            "furikanji": "<b> えぐ[刳]み</b>",
            "kana_only split": "<b><kun>えぐ</kun><oku>み</oku></b>",
            "furigana split": "<b><kun> 刳[えぐ]</kun><oku>み</oku></b>",
            "furikanji split": "<b><kun> えぐ[刳]</kun><oku>み</oku></b>",
            "kana_only merged": "<b><kun>えぐ</kun><oku>み</oku></b>",
            "furigana merged": "<b><kun> 刳[えぐ]</kun><oku>み</oku></b>",
            "furikanji merged": "<b><kun> えぐ[刳]</kun><oku>み</oku></b>",
        },
        id="Should match noun form okuri for 刳い",
    ),
    pytest.param(
        "脹",
        # The reading ふくら is part of the kunyomi ふく.らむ but isn't noun-form (ふくらみ) nor
        # just the stem (ふく) but should be matched as kunyomi nonetheless as it is effectively
        # a portion of the base form reading
        "脹脛[ふくらはぎ]",
        True,
        {
            "kana_only": "<b>ふくら</b>はぎ",
            "kana_only split": "<b><kun>ふくら</kun></b><kun>はぎ</kun>",
            "kana_only merged": "<b><kun>ふくら</kun></b><kun>はぎ</kun>",
            "furigana": "<b> 脹[ふくら]</b> 脛[はぎ]",
            "furigana split": "<b><kun> 脹[ふくら]</kun></b><kun> 脛[はぎ]</kun>",
            "furigana merged": "<b><kun> 脹[ふくら]</kun></b><kun> 脛[はぎ]</kun>",
            "furikanji": "<b> ふくら[脹]</b> はぎ[脛]",
            "furikanji split": "<b><kun> ふくら[脹]</kun></b><kun> はぎ[脛]</kun>",
            "furikanji merged": "<b><kun> ふくら[脹]</kun></b><kun> はぎ[脛]</kun>",
        },
        id="Should be able match kunyomi reading with partial okurigana match /1",
    ),
    pytest.param(
        "語",
        "物語[ものがたり]",
        True,
        {
            "kana_only": "もの<b>がたり</b>",
            "furigana": " 物[もの]<b> 語[がたり]</b>",
            "furikanji": " もの[物]<b> がたり[語]</b>",
            "kana_only split": "<kun>もの</kun><b><kun>がたり</kun></b>",
            "furigana split": "<kun> 物[もの]</kun><b><kun> 語[がたり]</kun></b>",
            "furikanji split": "<kun> もの[物]</kun><b><kun> がたり[語]</kun></b>",
            "kana_only merged": "<kun>もの</kun><b><kun>がたり</kun></b>",
            "furigana merged": "<kun> 物[もの]</kun><b><kun> 語[がたり]</kun></b>",
            "furikanji merged": "<kun> もの[物]</kun><b><kun> がたり[語]</kun></b>",
        },
        id="Should be able match noun form okuriganaless kunyomi reading 4/",
    ),
    pytest.param(
        "",
        "物語[モノガタリ]",
        True,
        {
            "kana_only": "モノガタリ",
            "furigana": " 物語[モノガタリ]",
            "furikanji": " モノガタリ[物語]",
            "kana_only split": "<kun>モノ</kun><kun>ガタリ</kun>",
            "furigana split": "<kun> 物[モノ]</kun><kun> 語[ガタリ]</kun>",
            "furikanji split": "<kun> モノ[物]</kun><kun> ガタリ[語]</kun>",
            "kana_only merged": "<kun>モノガタリ</kun>",
            "furigana merged": "<kun> 物語[モノガタリ]</kun>",
            "furikanji merged": "<kun> モノガタリ[物語]</kun>",
        },
        id="Preserve katakana in furigana /1",
    ),
    pytest.param(
        "",
        "馬鹿者[バカもの]",
        False,
        {
            "kana_only": "バカもの",
            "furigana": " 馬鹿者[バカもの]",
            "furikanji": " バカもの[馬鹿者]",
            "kana_only split": "<on>バ</on><kun>カ</kun><kun>もの</kun>",
            "furigana split": "<on> 馬[バ]</on><kun> 鹿[カ]</kun><kun> 者[もの]</kun>",
            "furikanji split": "<on> バ[馬]</on><kun> カ[鹿]</kun><kun> もの[者]</kun>",
            "kana_only merged": "<on>バ</on><kun>カもの</kun>",
            "furigana merged": "<on> 馬[バ]</on><kun> 鹿者[カもの]</kun>",
            "furikanji merged": "<on> バ[馬]</on><kun> カもの[鹿者]</kun>",
        },
        id="Preserve mixed katakana in furigana /1",
    ),
    pytest.param(
        "",
        # An entirely unlikely random mix of katakana and hiragana
        # The jukujikun 大和 should be split into やま and と when tags are split
        # たましい is a kunyomi reading for 魂
        "大和魂[やマとダまシい]",
        False,
        {
            "kana_only": "やマとダまシい",
            "furigana": " 大和魂[やマとダまシい]",
            "furikanji": " やマとダまシい[大和魂]",
            "kana_only split": "<juk>やマ</juk><juk>と</juk><kun>ダまシい</kun>",
            "furigana split": "<juk> 大[やマ]</juk><juk> 和[と]</juk><kun> 魂[ダまシい]</kun>",
            "furikanji split": "<juk> やマ[大]</juk><juk> と[和]</juk><kun> ダまシい[魂]</kun>",
            "kana_only merged": "<juk>やマと</juk><kun>ダまシい</kun>",
            "furigana merged": "<juk> 大和[やマと]</juk><kun> 魂[ダまシい]</kun>",
            "furikanji merged": "<juk> やマと[大和]</juk><kun> ダまシい[魂]</kun>",
        },
        id="Preserve mixed katakana in furigana /2",
    ),
    pytest.param(
        "置",
        " 風上[かざかみ]にも 置[お]けない",
        True,
        {
            "kana_only": " かざかみにも <b>おけない</b>",
            "furigana": " 風上[かざかみ]にも<b> 置[お]けない</b>",
            "furikanji": " かざかみ[風上]にも<b> お[置]けない</b>",
            "kana_only split": " <kun>かざ</kun><kun>かみ</kun>にも <b><kun>お</kun><oku>けない</oku></b>",
            "furigana split": "<kun> 風[かざ]</kun><kun> 上[かみ]</kun>にも<b><kun> 置[お]</kun><oku>けない</oku></b>",
            "furikanji split": "<kun> かざ[風]</kun><kun> かみ[上]</kun>にも<b><kun> お[置]</kun><oku>けない</oku></b>",
            "kana_only merged": " <kun>かざかみ</kun>にも <b><kun>お</kun><oku>けない</oku></b>",
            "furigana merged": "<kun> 風上[かざかみ]</kun>にも<b><kun> 置[お]</kun><oku>けない</oku></b>",
            "furikanji merged": "<kun> かざかみ[風上]</kun>にも<b><kun> お[置]</kun><oku>けない</oku></b>",
        },
        id="Should be able to get okurigana of kunyomi reading 1/",
    ),
    pytest.param(
        "来",
        "今[いま]に 来[きた]るべし",
        True,
        {
            "kana_only": "いまに <b>きたる</b>べし",
            "furigana": " 今[いま]に<b> 来[きた]る</b>べし",
            "furikanji": " いま[今]に<b> きた[来]る</b>べし",
            "kana_only split": "<kun>いま</kun>に <b><kun>きた</kun><oku>る</oku></b>べし",
            "furigana split": "<kun> 今[いま]</kun>に<b><kun> 来[きた]</kun><oku>る</oku></b>べし",
            "furikanji split": "<kun> いま[今]</kun>に<b><kun> きた[来]</kun><oku>る</oku></b>べし",
            "kana_only merged": "<kun>いま</kun>に <b><kun>きた</kun><oku>る</oku></b>べし",
            "furigana merged": "<kun> 今[いま]</kun>に<b><kun> 来[きた]</kun><oku>る</oku></b>べし",
            "furikanji merged": "<kun> いま[今]</kun>に<b><kun> きた[来]</kun><oku>る</oku></b>べし",
        },
        id="Verb okurigana test 1/",
    ),
    pytest.param(
        "書",
        "日記[にっき]を 書[か]いた。",
        True,
        {
            "kana_only": "ニッキを <b>かいた</b>。",
            "furigana": " 日記[ニッキ]を<b> 書[か]いた</b>。",
            "furikanji": " ニッキ[日記]を<b> か[書]いた</b>。",
            "kana_only split": "<on>ニッ</on><on>キ</on>を <b><kun>か</kun><oku>いた</oku></b>。",
            "furigana split": "<on> 日[ニッ]</on><on> 記[キ]</on>を<b><kun> 書[か]</kun><oku>いた</oku></b>。",
            "furikanji split": "<on> ニッ[日]</on><on> キ[記]</on>を<b><kun> か[書]</kun><oku>いた</oku></b>。",
            "kana_only merged": "<on>ニッキ</on>を <b><kun>か</kun><oku>いた</oku></b>。",
            "furigana merged": "<on> 日記[ニッキ]</on>を<b><kun> 書[か]</kun><oku>いた</oku></b>。",
            "furikanji merged": "<on> ニッキ[日記]</on>を<b><kun> か[書]</kun><oku>いた</oku></b>。",
        },
        id="Verb okurigana test 2/",
    ),
    pytest.param(
        "話",
        "友達[ともだち]と 話[はな]している。",
        True,
        {
            "kana_only": "ともダチと <b>はなして</b>いる。",
            "furigana": " 友達[ともダチ]と<b> 話[はな]して</b>いる。",
            "furikanji": " ともダチ[友達]と<b> はな[話]して</b>いる。",
            "kana_only split": "<kun>とも</kun><on>ダチ</on>と <b><kun>はな</kun><oku>して</oku></b>いる。",
            "furigana split": "<kun> 友[とも]</kun><on> 達[ダチ]</on>と<b><kun> 話[はな]</kun><oku>して</oku></b>いる。",
            "furikanji split": "<kun> とも[友]</kun><on> ダチ[達]</on>と<b><kun> はな[話]</kun><oku>して</oku></b>いる。",
            "kana_only merged": "<kun>とも</kun><on>ダチ</on>と <b><kun>はな</kun><oku>して</oku></b>いる。",
            "furigana merged": "<kun> 友[とも]</kun><on> 達[ダチ]</on>と<b><kun> 話[はな]</kun><oku>して</oku></b>いる。",
            "furikanji merged": "<kun> とも[友]</kun><on> ダチ[達]</on>と<b><kun> はな[話]</kun><oku>して</oku></b>いる。",
        },
        id="Verb okurigana test 3/",
    ),
    pytest.param(
        "聞",
        "ニュースを 聞[き]きました。",
        True,
        {
            "kana_only": "ニュースを <b>ききました</b>。",
            "furigana": "ニュースを<b> 聞[き]きました</b>。",
            "furikanji": "ニュースを<b> き[聞]きました</b>。",
            "kana_only split": "ニュースを <b><kun>き</kun><oku>きました</oku></b>。",
            "furigana split": "ニュースを<b><kun> 聞[き]</kun><oku>きました</oku></b>。",
            "furikanji split": "ニュースを<b><kun> き[聞]</kun><oku>きました</oku></b>。",
            "kana_only merged": "ニュースを <b><kun>き</kun><oku>きました</oku></b>。",
            "furigana merged": "ニュースを<b><kun> 聞[き]</kun><oku>きました</oku></b>。",
            "furikanji merged": "ニュースを<b><kun> き[聞]</kun><oku>きました</oku></b>。",
        },
        id="Verb okurigana test 4/",
    ),
    pytest.param(
        "走",
        "公園[こうえん]で 走[はし]ろう。",
        True,
        {
            "kana_only": "コウエンで <b>はしろう</b>。",
            "furigana": " 公園[コウエン]で<b> 走[はし]ろう</b>。",
            "furikanji": " コウエン[公園]で<b> はし[走]ろう</b>。",
            "kana_only split": "<on>コウ</on><on>エン</on>で <b><kun>はし</kun><oku>ろう</oku></b>。",
            "furigana split": "<on> 公[コウ]</on><on> 園[エン]</on>で<b><kun> 走[はし]</kun><oku>ろう</oku></b>。",
            "furikanji split": "<on> コウ[公]</on><on> エン[園]</on>で<b><kun> はし[走]</kun><oku>ろう</oku></b>。",
            "kana_only merged": "<on>コウエン</on>で <b><kun>はし</kun><oku>ろう</oku></b>。",
            "furigana merged": "<on> 公園[コウエン]</on>で<b><kun> 走[はし]</kun><oku>ろう</oku></b>。",
            "furikanji merged": "<on> コウエン[公園]</on>で<b><kun> はし[走]</kun><oku>ろう</oku></b>。",
        },
        id="Verb okurigana test 5/",
    ),
    pytest.param(
        "待",
        "友達[ともだち]を 待[ま]つ。",
        True,
        {
            "kana_only": "ともダチを <b>まつ</b>。",
            "furigana": " 友達[ともダチ]を<b> 待[ま]つ</b>。",
            "furikanji": " ともダチ[友達]を<b> ま[待]つ</b>。",
            "kana_only split": "<kun>とも</kun><on>ダチ</on>を <b><kun>ま</kun><oku>つ</oku></b>。",
            "furigana split": "<kun> 友[とも]</kun><on> 達[ダチ]</on>を<b><kun> 待[ま]</kun><oku>つ</oku></b>。",
            "furikanji split": "<kun> とも[友]</kun><on> ダチ[達]</on>を<b><kun> ま[待]</kun><oku>つ</oku></b>。",
            "kana_only merged": "<kun>とも</kun><on>ダチ</on>を <b><kun>ま</kun><oku>つ</oku></b>。",
            "furigana merged": "<kun> 友[とも]</kun><on> 達[ダチ]</on>を<b><kun> 待[ま]</kun><oku>つ</oku></b>。",
            "furikanji merged": "<kun> とも[友]</kun><on> ダチ[達]</on>を<b><kun> ま[待]</kun><oku>つ</oku></b>。",
        },
        id="Verb okurigana test 6/",
    ),
    pytest.param(
        "泳",
        "海[うみ]で 泳[およ]ぐ。",
        True,
        {
            "kana_only": "うみで <b>およぐ</b>。",
            "furigana": " 海[うみ]で<b> 泳[およ]ぐ</b>。",
            "furikanji": " うみ[海]で<b> およ[泳]ぐ</b>。",
            "kana_only split": "<kun>うみ</kun>で <b><kun>およ</kun><oku>ぐ</oku></b>。",
            "furigana split": "<kun> 海[うみ]</kun>で<b><kun> 泳[およ]</kun><oku>ぐ</oku></b>。",
            "furikanji split": "<kun> うみ[海]</kun>で<b><kun> およ[泳]</kun><oku>ぐ</oku></b>。",
            "kana_only merged": "<kun>うみ</kun>で <b><kun>およ</kun><oku>ぐ</oku></b>。",
            "furigana merged": "<kun> 海[うみ]</kun>で<b><kun> 泳[およ]</kun><oku>ぐ</oku></b>。",
            "furikanji merged": "<kun> うみ[海]</kun>で<b><kun> およ[泳]</kun><oku>ぐ</oku></b>。",
        },
        id="Verb okurigana test 7/",
    ),
    pytest.param(
        "作",
        "料理[りょうり]を 作[つく]る。",
        True,
        {
            "kana_only": "リョウリを <b>つくる</b>。",
            "furigana": " 料理[リョウリ]を<b> 作[つく]る</b>。",
            "furikanji": " リョウリ[料理]を<b> つく[作]る</b>。",
            "kana_only split": "<on>リョウ</on><on>リ</on>を <b><kun>つく</kun><oku>る</oku></b>。",
            "furigana split": "<on> 料[リョウ]</on><on> 理[リ]</on>を<b><kun> 作[つく]</kun><oku>る</oku></b>。",
            "furikanji split": "<on> リョウ[料]</on><on> リ[理]</on>を<b><kun> つく[作]</kun><oku>る</oku></b>。",
            "kana_only merged": "<on>リョウリ</on>を <b><kun>つく</kun><oku>る</oku></b>。",
            "furigana merged": "<on> 料理[リョウリ]</on>を<b><kun> 作[つく]</kun><oku>る</oku></b>。",
            "furikanji merged": "<on> リョウリ[料理]</on>を<b><kun> つく[作]</kun><oku>る</oku></b>。",
        },
        id="Verb okurigana test 8/",
    ),
    pytest.param(
        "遊",
        "子供[こども]と 遊[あそ]んでいるぞ。",
        True,
        {
            "kana_only": "こどもと <b>あそんで</b>いるぞ。",
            "furigana": " 子供[こども]と<b> 遊[あそ]んで</b>いるぞ。",
            "furikanji": " こども[子供]と<b> あそ[遊]んで</b>いるぞ。",
            "kana_only split": "<kun>こ</kun><kun>ども</kun>と <b><kun>あそ</kun><oku>んで</oku></b>いるぞ。",
            "furigana split": "<kun> 子[こ]</kun><kun> 供[ども]</kun>と<b><kun> 遊[あそ]</kun><oku>んで</oku></b>いるぞ。",
            "furikanji split": "<kun> こ[子]</kun><kun> ども[供]</kun>と<b><kun> あそ[遊]</kun><oku>んで</oku></b>いるぞ。",
            "kana_only merged": "<kun>こども</kun>と <b><kun>あそ</kun><oku>んで</oku></b>いるぞ。",
            "furigana merged": "<kun> 子供[こども]</kun>と<b><kun> 遊[あそ]</kun><oku>んで</oku></b>いるぞ。",
            "furikanji merged": "<kun> こども[子供]</kun>と<b><kun> あそ[遊]</kun><oku>んで</oku></b>いるぞ。",
        },
        id="Verb okurigana test 9/",
    ),
    pytest.param(
        "聞",
        # Both 聞く and 聞こえる will produce an okuri match but the correct should be 聞こえる
        "音[おと]を 聞[き]こえたか？何[なに]も 聞[き]いていないよ",
        True,
        {
            "kana_only": "おとを <b>きこえた</b>か？なにも <b>きいて</b>いないよ",
            "furigana": " 音[おと]を<b> 聞[き]こえた</b>か？ 何[なに]も<b> 聞[き]いて</b>いないよ",
            "furikanji": " おと[音]を<b> き[聞]こえた</b>か？ なに[何]も<b> き[聞]いて</b>いないよ",
            "kana_only split": "<kun>おと</kun>を <b><kun>き</kun><oku>こえた</oku></b>か？<kun>なに</kun>も"
            " <b><kun>き</kun><oku>いて</oku></b>いないよ",
            "furigana split": "<kun> 音[おと]</kun>を<b><kun> 聞[き]</kun><oku>こえた</oku></b>か？<kun>"
            " 何[なに]</kun>も"
            "<b><kun> 聞[き]</kun><oku>いて</oku></b>いないよ",
            "furikanji split": "<kun> おと[音]</kun>を<b><kun> き[聞]</kun><oku>こえた</oku></b>か？<kun>"
            " なに[何]</kun>も"
            "<b><kun> き[聞]</kun><oku>いて</oku></b>いないよ",
            "kana_only merged": "<kun>おと</kun>を <b><kun>き</kun><oku>こえた</oku></b>か？<kun>なに</kun>も"
            " <b><kun>き</kun><oku>いて</oku></b>いないよ",
            "furigana merged": "<kun> 音[おと]</kun>を<b><kun> 聞[き]</kun><oku>こえた</oku></b>か？<kun>"
            " 何[なに]</kun>も"
            "<b><kun> 聞[き]</kun><oku>いて</oku></b>いないよ",
            "furikanji merged": "<kun> おと[音]</kun>を<b><kun> き[聞]</kun><oku>こえた</oku></b>か？<kun>"
            " なに[何]</kun>も"
            "<b><kun> き[聞]</kun><oku>いて</oku></b>いないよ",
        },
        id="Verb okurigana test 10/",
    ),
    pytest.param(
        "抑",
        "俳句[はいく]は 言葉[ことば]が 最小限[さいしょうげん]に 抑[おさ]えられている。",
        True,
        {
            "kana_only": "ハイクは ことばが サイショウゲンに <b>おさえられて</b>いる。",
            "furigana": " 俳句[ハイク]は 言葉[ことば]が 最小限[サイショウゲン]に<b> 抑[おさ]えられて</b>いる。",
            "furikanji": " ハイク[俳句]は ことば[言葉]が サイショウゲン[最小限]に<b> おさ[抑]えられて</b>いる。",
            "kana_only split": "<on>ハイ</on><on>ク</on>は <kun>こと</kun><kun>ば</kun>が <on>サイ</on><on>ショウ</on>"
            "<on>ゲン</on>に <b><kun>おさ</kun><oku>えられて</oku></b>いる。",
            "furigana split": "<on> 俳[ハイ]</on><on> 句[ク]</on>は<kun> 言[こと]</kun><kun> 葉[ば]</kun>が<on>"
            " 最[サイ]</on><on>"
            " 小[ショウ]</on><on> 限[ゲン]</on>に<b><kun> 抑[おさ]</kun><oku>えられて</oku></b>いる。",
            "furikanji split": "<on> ハイ[俳]</on><on> ク[句]</on>は<kun> こと[言]</kun><kun> ば[葉]</kun>が<on>"
            " サイ[最]</on><on>"
            " ショウ[小]</on><on> ゲン[限]</on>に<b><kun> おさ[抑]</kun><oku>えられて</oku></b>いる。",
            "kana_only merged": "<on>ハイク</on>は <kun>ことば</kun>が <on>サイショウゲン</on>に"
            " <b><kun>おさ</kun><oku>えられて</oku></b>いる。",
            "furigana merged": "<on> 俳句[ハイク]</on>は<kun> 言葉[ことば]</kun>が<on> 最小限[サイショウゲン]</on>に"
            "<b><kun> 抑[おさ]</kun><oku>えられて</oku></b>いる。",
            "furikanji merged": "<on> ハイク[俳句]</on>は<kun> ことば[言葉]</kun>が<on> サイショウゲン[最小限]</on>に"
            "<b><kun> おさ[抑]</kun><oku>えられて</oku></b>いる。",
        },
        id="Verb okurigana test 11/",
    ),
    pytest.param(
        "染",
        "幼馴染[おさななじ]みと 久[ひさ]しぶりに 会[あ]った。",
        True,
        {
            "kana_only": "おさなな<b>じみ</b>と ひさしぶりに あった。",
            "furigana": " 幼馴[おさなな]<b> 染[じ]み</b>と 久[ひさ]しぶりに 会[あ]った。",
            "furikanji": " おさなな[幼馴]<b> じ[染]み</b>と ひさ[久]しぶりに あ[会]った。",
            "kana_only split": "<kun>おさな</kun><kun>な</kun><b><kun>じ</kun><oku>み</oku></b>と"
            " <kun>ひさ</kun><oku>し</oku>ぶりに <kun>あ</kun><oku>った</oku>。",
            "furigana split": "<kun> 幼[おさな]</kun><kun> 馴[な]</kun><b><kun> 染[じ]</kun><oku>み</oku></b>と<kun>"
            " 久[ひさ]</kun><oku>し</oku>ぶりに<kun> 会[あ]</kun><oku>った</oku>。",
            "furikanji split": "<kun> おさな[幼]</kun><kun> な[馴]</kun><b><kun> じ[染]</kun><oku>み</oku></b>と<kun>"
            " ひさ[久]</kun><oku>し</oku>ぶりに<kun> あ[会]</kun><oku>った</oku>。",
            "kana_only merged": "<kun>おさなな</kun><b><kun>じ</kun><oku>み</oku></b>と <kun>ひさ</kun><oku>し</oku>ぶりに"
            " <kun>あ</kun><oku>った</oku>。",
            "furigana merged": "<kun> 幼馴[おさなな]</kun><b><kun> 染[じ]</kun><oku>み</oku></b>と<kun>"
            " 久[ひさ]</kun><oku>し</oku>ぶりに<kun> 会[あ]</kun><oku>った</oku>。",
            "furikanji merged": "<kun> おさなな[幼馴]</kun><b><kun> じ[染]</kun><oku>み</oku></b>と<kun>"
            " ひさ[久]</kun><oku>し</oku>ぶりに<kun> あ[会]</kun><oku>った</oku>。",
        },
        id="Verb okurigana test 12/",
    ),
    pytest.param(
        "試",
        "試[こころ]みる",
        True,
        {
            "kana_only": "<b>こころみる</b>",
            "furigana": "<b> 試[こころ]みる</b>",
            "furikanji": "<b> こころ[試]みる</b>",
            "kana_only split": "<b><kun>こころ</kun><oku>みる</oku></b>",
            "furigana split": "<b><kun> 試[こころ]</kun><oku>みる</oku></b>",
            "furikanji split": "<b><kun> こころ[試]</kun><oku>みる</oku></b>",
            "kana_only merged": "<b><kun>こころ</kun><oku>みる</oku></b>",
            "furigana merged": "<b><kun> 試[こころ]</kun><oku>みる</oku></b>",
            "furikanji merged": "<b><kun> こころ[試]</kun><oku>みる</oku></b>",
        },
        id="Verb okurigana test /13",
    ),
    pytest.param(
        "掛",
        # 掛 has both onyomi カ and kunyomi か.ける, should use the kunyomi if there is okurigana
        "掛[か]ける。",
        True,
        {
            "kana_only": "<b>かける</b>。",
            "furigana": "<b> 掛[か]ける</b>。",
            "furikanji": "<b> か[掛]ける</b>。",
            "kana_only split": "<b><kun>か</kun><oku>ける</oku></b>。",
            "furigana split": "<b><kun> 掛[か]</kun><oku>ける</oku></b>。",
            "furikanji split": "<b><kun> か[掛]</kun><oku>ける</oku></b>。",
            "kana_only merged": "<b><kun>か</kun><oku>ける</oku></b>。",
            "furigana merged": "<b><kun> 掛[か]</kun><oku>ける</oku></b>。",
            "furikanji merged": "<b><kun> か[掛]</kun><oku>ける</oku></b>。",
        },
        id="Verb okurigana test 14/",
    ),
    pytest.param(
        "掛",
        # Same if 掛ける is used in a compound word
        "仕[し] 掛[か]ける。",
        True,
        {
            "kana_only": "シ <b>かける</b>。",
            "furigana": " 仕[シ]<b> 掛[か]ける</b>。",
            "furikanji": " シ[仕]<b> か[掛]ける</b>。",
            "kana_only split": "<on>シ</on> <b><kun>か</kun><oku>ける</oku></b>。",
            "furigana split": "<on> 仕[シ]</on><b><kun> 掛[か]</kun><oku>ける</oku></b>。",
            "furikanji split": "<on> シ[仕]</on><b><kun> か[掛]</kun><oku>ける</oku></b>。",
            "kana_only merged": "<on>シ</on> <b><kun>か</kun><oku>ける</oku></b>。",
            "furigana merged": "<on> 仕[シ]</on><b><kun> 掛[か]</kun><oku>ける</oku></b>。",
            "furikanji merged": "<on> シ[仕]</on><b><kun> か[掛]</kun><oku>ける</oku></b>。",
        },
        id="Verb okurigana test 15/",
    ),
    pytest.param(
        "見",
        "見[み]たい",
        True,
        {
            "kana_only": "<b>みたい</b>",
            "furigana": "<b> 見[み]たい</b>",
            "furikanji": "<b> み[見]たい</b>",
            "kana_only split": "<b><kun>み</kun><oku>たい</oku></b>",
            "furigana split": "<b><kun> 見[み]</kun><oku>たい</oku></b>",
            "furikanji split": "<b><kun> み[見]</kun><oku>たい</oku></b>",
            "kana_only merged": "<b><kun>み</kun><oku>たい</oku></b>",
            "furigana merged": "<b><kun> 見[み]</kun><oku>たい</oku></b>",
            "furikanji merged": "<b><kun> み[見]</kun><oku>たい</oku></b>",
        },
        id="Verb たい inflection 1/",
    ),
    pytest.param(
        "",
        "試[ため]したい",
        True,
        {
            "kana_only": "ためしたい",
            "furigana": " 試[ため]したい",
            "furikanji": " ため[試]したい",
            "kana_only split": "<kun>ため</kun><oku>したい</oku>",
            "furigana split": "<kun> 試[ため]</kun><oku>したい</oku>",
            "furikanji split": "<kun> ため[試]</kun><oku>したい</oku>",
            "kana_only merged": "<kun>ため</kun><oku>したい</oku>",
            "furigana merged": "<kun> 試[ため]</kun><oku>したい</oku>",
            "furikanji merged": "<kun> ため[試]</kun><oku>したい</oku>",
        },
        id="Verb たい inflection 2/",
    ),
    pytest.param(
        "泳",
        "泳[およ]がれたいかな",
        True,
        {
            "kana_only": "<b>およがれたい</b>かな",
            "furigana": "<b> 泳[およ]がれたい</b>かな",
            "furikanji": "<b> およ[泳]がれたい</b>かな",
            "kana_only split": "<b><kun>およ</kun><oku>がれたい</oku></b>かな",
            "furigana split": "<b><kun> 泳[およ]</kun><oku>がれたい</oku></b>かな",
            "furikanji split": "<b><kun> およ[泳]</kun><oku>がれたい</oku></b>かな",
            "kana_only merged": "<b><kun>およ</kun><oku>がれたい</oku></b>かな",
            "furigana merged": "<b><kun> 泳[およ]</kun><oku>がれたい</oku></b>かな",
            "furikanji merged": "<b><kun> およ[泳]</kun><oku>がれたい</oku></b>かな",
        },
        id="Verb たい inflection 3/",
    ),
    pytest.param(
        "飲",
        "飲[の]みたい",
        True,
        {
            "kana_only": "<b>のみたい</b>",
            "furigana": "<b> 飲[の]みたい</b>",
            "furikanji": "<b> の[飲]みたい</b>",
            "kana_only split": "<b><kun>の</kun><oku>みたい</oku></b>",
            "furigana split": "<b><kun> 飲[の]</kun><oku>みたい</oku></b>",
            "furikanji split": "<b><kun> の[飲]</kun><oku>みたい</oku></b>",
            "kana_only merged": "<b><kun>の</kun><oku>みたい</oku></b>",
            "furigana merged": "<b><kun> 飲[の]</kun><oku>みたい</oku></b>",
            "furikanji merged": "<b><kun> の[飲]</kun><oku>みたい</oku></b>",
        },
        id="Verb たい inflection 4/",
    ),
    pytest.param(
        "論",
        # 論 uses the onyomi ろ in 目論む and is an unusual of a godan mu verb
        "目論[もくろ]む",
        True,
        {
            "kana_only": "モク<b>ロむ</b>",
            "furigana": " 目[モク]<b> 論[ロ]む</b>",
            "furikanji": " モク[目]<b> ロ[論]む</b>",
            "kana_only split": "<on>モク</on><b><on>ロ</on><oku>む</oku></b>",
            "furigana split": "<on> 目[モク]</on><b><on> 論[ロ]</on><oku>む</oku></b>",
            "furikanji split": "<on> モク[目]</on><b><on> ロ[論]</on><oku>む</oku></b>",
            "kana_only merged": "<on>モク</on><b><on>ロ</on><oku>む</oku></b>",
            "furigana merged": "<on> 目[モク]</on><b><on> 論[ロ]</on><oku>む</oku></b>",
            "furikanji merged": "<on> モク[目]</on><b><on> ロ[論]</on><oku>む</oku></b>",
        },
        id="Onyomi multi-kanji verb okurigana - with highlight",
    ),
    pytest.param(
        "",
        "目論[もくろ]む",
        True,
        {
            "kana_only": "モクロむ",
            "furigana": " 目論[モクロ]む",
            "furikanji": " モクロ[目論]む",
            "kana_only split": "<on>モク</on><on>ロ</on><oku>む</oku>",
            "furigana split": "<on> 目[モク]</on><on> 論[ロ]</on><oku>む</oku>",
            "furikanji split": "<on> モク[目]</on><on> ロ[論]</on><oku>む</oku>",
            "kana_only merged": "<on>モクロ</on><oku>む</oku>",
            "furigana merged": "<on> 目論[モクロ]</on><oku>む</oku>",
            "furikanji merged": "<on> モクロ[目論]</on><oku>む</oku>",
        },
        id="Onyomi multi-kanji verb okurigana - no highlight",
    ),
    pytest.param(
        "",
        "餡[あん]こ",
        True,
        {
            "kana_only": "あんこ",
            "furigana": " 餡[あん]こ",
            "furikanji": " あん[餡]こ",
            "kana_only split": "<kun>あん</kun>こ",
            "furigana split": "<kun> 餡[あん]</kun>こ",
            "furikanji split": "<kun> あん[餡]</kun>こ",
            "kana_only merged": "<kun>あん</kun>こ",
            "furigana merged": "<kun> 餡[あん]</kun>こ",
            "furikanji merged": "<kun> あん[餡]</kun>こ",
        },
        id="Should not match okurigana in 餡こ",
    ),
    pytest.param(
        "悲",
        "彼[かれ]は 悲[かな]しくすぎるので、 悲[かな]しみの 悲[かな]しさを 悲[かな]しんでいる。",
        True,
        {
            "kana_only": "かれは <b>かなしく</b>すぎるので、 <b>かなしみ</b>の <b>かなしさ</b>を"
            " <b>かなしんで</b>いる。",
            "furigana": " 彼[かれ]は<b> 悲[かな]しく</b>すぎるので、<b> 悲[かな]しみ</b>の<b>"
            " 悲[かな]しさ</b>を<b> 悲[かな]しんで</b>いる。",
            "furikanji": " かれ[彼]は<b> かな[悲]しく</b>すぎるので、<b> かな[悲]しみ</b>の<b>"
            " かな[悲]しさ</b>を<b> かな[悲]しんで</b>いる。",
            "kana_only split": "<kun>かれ</kun>は <b><kun>かな</kun><oku>しく</oku></b>すぎるので、"
            " <b><kun>かな</kun><oku>しみ</oku></b>の <b><kun>かな</kun><oku>しさ</oku></b>を"
            " <b><kun>かな</kun><oku>しんで</oku></b>いる。",
            "furigana split": "<kun> 彼[かれ]</kun>は<b><kun> 悲[かな]</kun><oku>しく</oku></b>すぎるので、<b><kun>"
            " 悲[かな]</kun><oku>しみ</oku></b>の<b><kun> 悲[かな]</kun><oku>しさ</oku></b>を"
            "<b><kun> 悲[かな]</kun><oku>しんで</oku></b>いる。",
            "furikanji split": "<kun> かれ[彼]</kun>は<b><kun> かな[悲]</kun><oku>しく</oku></b>すぎるので、<b><kun>"
            " かな[悲]</kun><oku>しみ</oku></b>の<b><kun> かな[悲]</kun><oku>しさ</oku></b>を"
            "<b><kun> かな[悲]</kun><oku>しんで</oku></b>いる。",
            "kana_only merged": "<kun>かれ</kun>は <b><kun>かな</kun><oku>しく</oku></b>すぎるので、"
            " <b><kun>かな</kun><oku>しみ</oku></b>の <b><kun>かな</kun><oku>しさ</oku></b>を"
            " <b><kun>かな</kun><oku>しんで</oku></b>いる。",
            "furigana merged": "<kun> 彼[かれ]</kun>は<b><kun> 悲[かな]</kun><oku>しく</oku></b>すぎるので、<b><kun>"
            " 悲[かな]</kun><oku>しみ</oku></b>の<b><kun> 悲[かな]</kun><oku>しさ</oku></b>を"
            "<b><kun> 悲[かな]</kun><oku>しんで</oku></b>いる。",
            "furikanji merged": "<kun> かれ[彼]</kun>は<b><kun> かな[悲]</kun><oku>しく</oku></b>すぎるので、<b><kun>"
            " かな[悲]</kun><oku>しみ</oku></b>の<b><kun> かな[悲]</kun><oku>しさ</oku></b>を"
            "<b><kun> かな[悲]</kun><oku>しんで</oku></b>いる。",
        },
        id="Adjective okurigana test 1/",
    ),
    pytest.param(
        "青",
        "空[そら]が 青[あお]かったら、 青[あお]くない 海[うみ]に 行[い]こう",
        True,
        {
            "kana_only": "そらが <b>あおかったら</b>、 <b>あおくない</b> うみに いこう",
            "furigana": " 空[そら]が<b> 青[あお]かったら</b>、<b> 青[あお]くない</b> 海[うみ]に 行[い]こう",
            "furikanji": " そら[空]が<b> あお[青]かったら</b>、<b> あお[青]くない</b> うみ[海]に い[行]こう",
            "kana_only split": "<kun>そら</kun>が <b><kun>あお</kun><oku>かったら</oku></b>、"
            " <b><kun>あお</kun><oku>くない</oku></b> <kun>うみ</kun>に <kun>い</kun><oku>こう</oku>",
            "furigana split": "<kun> 空[そら]</kun>が<b><kun> 青[あお]</kun><oku>かったら</oku></b>、<b><kun>"
            " 青[あお]</kun><oku>くない</oku></b><kun> 海[うみ]</kun>に<kun>"
            " 行[い]</kun><oku>こう</oku>",
            "furikanji split": "<kun> そら[空]</kun>が<b><kun> あお[青]</kun><oku>かったら</oku></b>、<b><kun>"
            " あお[青]</kun><oku>くない</oku></b><kun> うみ[海]</kun>に<kun>"
            " い[行]</kun><oku>こう</oku>",
            "kana_only merged": "<kun>そら</kun>が <b><kun>あお</kun><oku>かったら</oku></b>、"
            " <b><kun>あお</kun><oku>くない</oku></b> <kun>うみ</kun>に <kun>い</kun><oku>こう</oku>",
            "furigana merged": "<kun> 空[そら]</kun>が<b><kun> 青[あお]</kun><oku>かったら</oku></b>、<b><kun>"
            " 青[あお]</kun><oku>くない</oku></b><kun> 海[うみ]</kun>に<kun>"
            " 行[い]</kun><oku>こう</oku>",
            "furikanji merged": "<kun> そら[空]</kun>が<b><kun> あお[青]</kun><oku>かったら</oku></b>、<b><kun>"
            " あお[青]</kun><oku>くない</oku></b><kun> うみ[海]</kun>に<kun>"
            " い[行]</kun><oku>こう</oku>",
        },
        id="Adjective okurigana test 2/",
    ),
    pytest.param(
        "高",
        "山[やま]が 高[たか]ければ、 高層[こうそう]ビルが 高[たか]めてと 高[たか]ぶり",
        True,
        {
            "kana_only": "やまが <b>たかければ</b>、 <b>コウ</b>ソウビルが <b>たかめて</b>と <b>たかぶり</b>",
            "furigana": " 山[やま]が<b> 高[たか]ければ</b>、<b> 高[コウ]</b> 層[ソウ]ビルが<b>"
            " 高[たか]めて</b>と<b> 高[たか]ぶり</b>",
            "furikanji": " やま[山]が<b> たか[高]ければ</b>、<b> コウ[高]</b> ソウ[層]ビルが<b>"
            " たか[高]めて</b>と<b> たか[高]ぶり</b>",
            "kana_only split": "<kun>やま</kun>が <b><kun>たか</kun><oku>ければ</oku></b>、"
            " <b><on>コウ</on></b><on>ソウ</on>ビルが <b><kun>たか</kun><oku>めて</oku></b>と"
            " <b><kun>たか</kun><oku>ぶり</oku></b>",
            "furigana split": "<kun> 山[やま]</kun>が<b><kun> 高[たか]</kun><oku>ければ</oku></b>、"
            "<b><on> 高[コウ]</on></b><on> 層[ソウ]</on>ビルが<b><kun>"
            " 高[たか]</kun><oku>めて</oku></b>と"
            "<b><kun> 高[たか]</kun><oku>ぶり</oku></b>",
            "furikanji split": "<kun> やま[山]</kun>が<b><kun> たか[高]</kun><oku>ければ</oku></b>、"
            "<b><on> コウ[高]</on></b><on> ソウ[層]</on>ビルが<b><kun>"
            " たか[高]</kun><oku>めて</oku></b>と"
            "<b><kun> たか[高]</kun><oku>ぶり</oku></b>",
            "kana_only merged": "<kun>やま</kun>が <b><kun>たか</kun><oku>ければ</oku></b>、"
            " <b><on>コウ</on></b><on>ソウ</on>ビルが <b><kun>たか</kun><oku>めて</oku></b>と"
            " <b><kun>たか</kun><oku>ぶり</oku></b>",
            "furigana merged": "<kun> 山[やま]</kun>が<b><kun> 高[たか]</kun><oku>ければ</oku></b>、"
            "<b><on> 高[コウ]</on></b><on> 層[ソウ]</on>ビルが<b><kun>"
            " 高[たか]</kun><oku>めて</oku></b>と"
            "<b><kun> 高[たか]</kun><oku>ぶり</oku></b>",
            "furikanji merged": "<kun> やま[山]</kun>が<b><kun> たか[高]</kun><oku>ければ</oku></b>、"
            "<b><on> コウ[高]</on></b><on> ソウ[層]</on>ビルが<b><kun>"
            " たか[高]</kun><oku>めて</oku></b>と"
            "<b><kun> たか[高]</kun><oku>ぶり</oku></b>",
        },
        id="Adjective okurigana test 3/",
    ),
    pytest.param(
        "厚",
        "彼[かれ]は 厚かましい[あつかましい]。",
        True,
        {
            "kana_only": "かれは <b>あつかましい</b>。",
            "furigana": " 彼[かれ]は<b> 厚[あつ]かましい</b>。",
            "furikanji": " かれ[彼]は<b> あつ[厚]かましい</b>。",
            "kana_only split": "<kun>かれ</kun>は <b><kun>あつ</kun><oku>かましい</oku></b>。",
            "furigana split": "<kun> 彼[かれ]</kun>は<b><kun> 厚[あつ]</kun><oku>かましい</oku></b>。",
            "furikanji split": "<kun> かれ[彼]</kun>は<b><kun> あつ[厚]</kun><oku>かましい</oku></b>。",
            "kana_only merged": "<kun>かれ</kun>は <b><kun>あつ</kun><oku>かましい</oku></b>。",
            "furigana merged": "<kun> 彼[かれ]</kun>は<b><kun> 厚[あつ]</kun><oku>かましい</oku></b>。",
            "furikanji merged": "<kun> かれ[彼]</kun>は<b><kun> あつ[厚]</kun><oku>かましい</oku></b>。",
        },
        id="Adjective okurigana test 4/",
    ),
    pytest.param(
        "恥",
        "恥[は]ずかしげな 顔[かお]で 恥[はじ]を 知[し]らない 振[ふ]りで 恥[は]じらってください。",
        True,
        {
            "kana_only": "<b>はずかし</b>げな かおで <b>はじ</b>を しらない ふりで <b>はじらって</b>ください。",
            "furigana": "<b> 恥[は]ずかし</b>げな 顔[かお]で<b> 恥[はじ]</b>を 知[し]らない"
            " 振[ふ]りで<b> 恥[は]じらって</b>ください。",
            "furikanji": "<b> は[恥]ずかし</b>げな かお[顔]で<b> はじ[恥]</b>を し[知]らない"
            " ふ[振]りで<b> は[恥]じらって</b>ください。",
            "kana_only split": "<b><kun>は</kun><oku>ずかし</oku></b>げな <kun>かお</kun>で"
            " <b><kun>はじ</kun></b>を <kun>し</kun><oku>らない</oku>"
            " <kun>ふ</kun><oku>り</oku>で <b><kun>は</kun><oku>じらって</oku></b>ください。",
            "furigana split": "<b><kun> 恥[は]</kun><oku>ずかし</oku></b>げな<kun> 顔[かお]</kun>で<b><kun>"
            " 恥[はじ]</kun></b>を<kun> 知[し]</kun><oku>らない</oku><kun>"
            " 振[ふ]</kun><oku>り</oku>で<b><kun> 恥[は]</kun><oku>じらって</oku></b>ください。",
            "furikanji split": "<b><kun> は[恥]</kun><oku>ずかし</oku></b>げな<kun> かお[顔]</kun>で<b><kun>"
            " はじ[恥]</kun></b>を<kun> し[知]</kun><oku>らない</oku><kun>"
            " ふ[振]</kun><oku>り</oku>で<b><kun> は[恥]</kun><oku>じらって</oku></b>"
            "ください。",
            "kana_only merged": "<b><kun>は</kun><oku>ずかし</oku></b>げな <kun>かお</kun>で"
            " <b><kun>はじ</kun></b>を <kun>し</kun><oku>らない</oku>"
            " <kun>ふ</kun><oku>り</oku>で <b><kun>は</kun><oku>じらって</oku></b>ください。",
            "furigana merged": "<b><kun> 恥[は]</kun><oku>ずかし</oku></b>げな<kun> 顔[かお]</kun>で<b><kun>"
            " 恥[はじ]</kun></b>を<kun> 知[し]</kun><oku>らない</oku><kun>"
            " 振[ふ]</kun><oku>り</oku>で<b><kun> 恥[は]</kun><oku>じらって</oku></b>ください。",
            "furikanji merged": "<b><kun> は[恥]</kun><oku>ずかし</oku></b>げな<kun> かお[顔]</kun>で<b><kun>"
            " はじ[恥]</kun></b>を<kun> し[知]</kun><oku>らない</oku><kun>"
            " ふ[振]</kun><oku>り</oku>で<b><kun> は[恥]</kun><oku>じらって</oku></b>ください。",
        },
        id="Adjective okurigana test 5/",
    ),
    pytest.param(
        "刳",
        "刳[えぐ]かったよな",
        True,
        {
            "kana_only": "<b>えぐかった</b>よな",
            "furigana": "<b> 刳[えぐ]かった</b>よな",
            "furikanji": "<b> えぐ[刳]かった</b>よな",
            "kana_only split": "<b><kun>えぐ</kun><oku>かった</oku></b>よな",
            "furigana split": "<b><kun> 刳[えぐ]</kun><oku>かった</oku></b>よな",
            "furikanji split": "<b><kun> えぐ[刳]</kun><oku>かった</oku></b>よな",
            "kana_only merged": "<b><kun>えぐ</kun><oku>かった</oku></b>よな",
            "furigana merged": "<b><kun> 刳[えぐ]</kun><oku>かった</oku></b>よな",
            "furikanji merged": "<b><kun> えぐ[刳]</kun><oku>かった</oku></b>よな",
        },
        id="adjective okurigana test 6/",
    ),
    pytest.param(
        "良",
        "良[よ]かろう",
        True,
        {
            "kana_only": "<b>よかろう</b>",
            "furigana": "<b> 良[よ]かろう</b>",
            "furikanji": "<b> よ[良]かろう</b>",
            "kana_only split": "<b><kun>よ</kun><oku>かろう</oku></b>",
            "furigana split": "<b><kun> 良[よ]</kun><oku>かろう</oku></b>",
            "furikanji split": "<b><kun> よ[良]</kun><oku>かろう</oku></b>",
            "kana_only merged": "<b><kun>よ</kun><oku>かろう</oku></b>",
            "furigana merged": "<b><kun> 良[よ]</kun><oku>かろう</oku></b>",
            "furikanji merged": "<b><kun> よ[良]</kun><oku>かろう</oku></b>",
        },
        id="adjective okurigana test 7/",
    ),
    pytest.param(
        "",
        "馴染[なじ]む",
        True,
        {
            "kana_only": "なじむ",
            "furigana": " 馴染[なじ]む",
            "furikanji": " なじ[馴染]む",
            "kana_only split": "<kun>な</kun><kun>じ</kun><oku>む</oku>",
            "furigana split": "<kun> 馴[な]</kun><kun> 染[じ]</kun><oku>む</oku>",
            "furikanji split": "<kun> な[馴]</kun><kun> じ[染]</kun><oku>む</oku>",
            "kana_only merged": "<kun>なじ</kun><oku>む</oku>",
            "furigana merged": "<kun> 馴染[なじ]</kun><oku>む</oku>",
            "furikanji merged": "<kun> なじ[馴染]</kun><oku>む</oku>",
        },
        id="adjective okurigana test 8/",
    ),
    pytest.param(
        "染",
        "馴染[なじ]む",
        True,
        {
            "kana_only": "な<b>じむ</b>",
            "furigana": " 馴[な]<b> 染[じ]む</b>",
            "furikanji": " な[馴]<b> じ[染]む</b>",
            "kana_only split": "<kun>な</kun><b><kun>じ</kun><oku>む</oku></b>",
            "furigana split": "<kun> 馴[な]</kun><b><kun> 染[じ]</kun><oku>む</oku></b>",
            "furikanji split": "<kun> な[馴]</kun><b><kun> じ[染]</kun><oku>む</oku></b>",
            "kana_only merged": "<kun>な</kun><b><kun>じ</kun><oku>む</oku></b>",
            "furigana merged": "<kun> 馴[な]</kun><b><kun> 染[じ]</kun><oku>む</oku></b>",
            "furikanji merged": "<kun> な[馴]</kun><b><kun> じ[染]</kun><oku>む</oku></b>",
        },
        id="adjective okurigana test 9/",
    ),
    pytest.param(
        "暖",
        "暖[あたた]かい、温[あたた]かく",
        True,
        {
            "kana_only": "<b>あたたかい</b>、あたたかく",
            "furigana": "<b> 暖[あたた]かい</b>、 温[あたた]かく",
            "furikanji": "<b> あたた[暖]かい</b>、 あたた[温]かく",
            "kana_only split": "<b><kun>あたた</kun><oku>かい</oku></b>、<kun>あたた</kun><oku>かく</oku>",
            "furigana split": "<b><kun> 暖[あたた]</kun><oku>かい</oku></b>、<kun> 温[あたた]</kun><oku>かく</oku>",
            "furikanji split": "<b><kun> あたた[暖]</kun><oku>かい</oku></b>、<kun> あたた[温]</kun><oku>かく</oku>",
            "kana_only merged": "<b><kun>あたた</kun><oku>かい</oku></b>、<kun>あたた</kun><oku>かく</oku>",
            "furigana merged": "<b><kun> 暖[あたた]</kun><oku>かい</oku></b>、<kun> 温[あたた]</kun><oku>かく</oku>",
            "furikanji merged": "<b><kun> あたた[暖]</kun><oku>かい</oku></b>、<kun> あたた[温]</kun><oku>かく</oku>",
        },
        id="adjective okurigana test 10/",
    ),
    pytest.param(
        "一",
        "一人[ひとり]",
        True,
        {
            "kana_only": "<b>ひと</b>り",
            "furigana": "<b> 一[ひと]</b> 人[り]",
            "furikanji": "<b> ひと[一]</b> り[人]",
            "kana_only split": "<b><kun>ひと</kun></b><kun>り</kun>",
            "furigana split": "<b><kun> 一[ひと]</kun></b><kun> 人[り]</kun>",
            "furikanji split": "<b><kun> ひと[一]</kun></b><kun> り[人]</kun>",
            "kana_only merged": "<b><kun>ひと</kun></b><kun>り</kun>",
            "furigana merged": "<b><kun> 一[ひと]</kun></b><kun> 人[り]</kun>",
            "furikanji merged": "<b><kun> ひと[一]</kun></b><kun> り[人]</kun>",
        },
        id="numbers of people /1",
    ),
    pytest.param(
        "沁",
        "二人[ふたり]でしみじみと 語り合[かたりあ]った。",
        True,
        {
            "kana_only": "ふたりでしみじみと かたりあった。",
            "furigana": " 二人[ふたり]でしみじみと 語[かた]り 合[あ]った。",
            "furikanji": " ふたり[二人]でしみじみと かた[語]り あ[合]った。",
            "kana_only split": "<kun>ふた</kun><kun>り</kun>でしみじみと"
            " <kun>かた</kun><oku>り</oku><kun>あ</kun><oku>った</oku>。",
            "furigana split": "<kun> 二[ふた]</kun><kun> 人[り]</kun>でしみじみと<kun>"
            " 語[かた]</kun><oku>り</oku><kun> 合[あ]</kun><oku>った</oku>。",
            "furikanji split": "<kun> ふた[二]</kun><kun> り[人]</kun>でしみじみと<kun>"
            " かた[語]</kun><oku>り</oku><kun> あ[合]</kun><oku>った</oku>。",
            "kana_only merged": "<kun>ふたり</kun>でしみじみと <kun>かた</kun><oku>り</oku><kun>あ</kun><oku>った</oku>。",
            "furigana merged": "<kun> 二人[ふたり]</kun>でしみじみと<kun> 語[かた]</kun><oku>り</oku><kun>"
            " 合[あ]</kun><oku>った</oku>。",
            "furikanji merged": "<kun> ふたり[二人]</kun>でしみじみと<kun> かた[語]</kun><oku>り</oku><kun>"
            " あ[合]</kun><oku>った</oku>。",
        },
        id="numbers of people /2",
    ),
    pytest.param(
        "三",
        "三人[さんにん]",
        True,
        {
            "kana_only": "<b>サン</b>ニン",
            "furigana": "<b> 三[サン]</b> 人[ニン]",
            "furikanji": "<b> サン[三]</b> ニン[人]",
            "kana_only split": "<b><on>サン</on></b><on>ニン</on>",
            "furigana split": "<b><on> 三[サン]</on></b><on> 人[ニン]</on>",
            "furikanji split": "<b><on> サン[三]</on></b><on> ニン[人]</on>",
            "kana_only merged": "<b><on>サン</on></b><on>ニン</on>",
            "furigana merged": "<b><on> 三[サン]</on></b><on> 人[ニン]</on>",
            "furikanji merged": "<b><on> サン[三]</on></b><on> ニン[人]</on>",
        },
        id="numbers of people /3",
    ),
    pytest.param(
        "生",
        "生粋[きっすい]",
        True,
        {
            "kana_only": "<b>きっ</b>スイ",
            "furigana": "<b> 生[きっ]</b> 粋[スイ]",
            "furikanji": "<b> きっ[生]</b> スイ[粋]",
            "kana_only split": "<b><kun>きっ</kun></b><on>スイ</on>",
            "furigana split": "<b><kun> 生[きっ]</kun></b><on> 粋[スイ]</on>",
            "furikanji split": "<b><kun> きっ[生]</kun></b><on> スイ[粋]</on>",
            "kana_only merged": "<b><kun>きっ</kun></b><on>スイ</on>",
            "furigana merged": "<b><kun> 生[きっ]</kun></b><on> 粋[スイ]</on>",
            "furikanji merged": "<b><kun> きっ[生]</kun></b><on> スイ[粋]</on>",
        },
        id="生 readings /1",
    ),
    pytest.param(
        "生",
        "生地[きじ]",
        True,
        {
            "kana_only": "<b>き</b>ジ",
            "furigana": "<b> 生[き]</b> 地[ジ]",
            "furikanji": "<b> き[生]</b> ジ[地]",
            "kana_only split": "<b><kun>き</kun></b><on>ジ</on>",
            "furigana split": "<b><kun> 生[き]</kun></b><on> 地[ジ]</on>",
            "furikanji split": "<b><kun> き[生]</kun></b><on> ジ[地]</on>",
            "kana_only merged": "<b><kun>き</kun></b><on>ジ</on>",
            "furigana merged": "<b><kun> 生[き]</kun></b><on> 地[ジ]</on>",
            "furikanji merged": "<b><kun> き[生]</kun></b><on> ジ[地]</on>",
        },
        id="生 readings /2",
    ),
    pytest.param(
        "生",
        "弥生[やよい]",
        True,
        {
            "kana_only": "や<b>よい</b>",
            "furigana": " 弥[や]<b> 生[よい]</b>",
            "furikanji": " や[弥]<b> よい[生]</b>",
            "kana_only split": "<kun>や</kun><b><kun>よい</kun></b>",
            "furigana split": "<kun> 弥[や]</kun><b><kun> 生[よい]</kun></b>",
            "furikanji split": "<kun> や[弥]</kun><b><kun> よい[生]</kun></b>",
            "kana_only merged": "<kun>や</kun><b><kun>よい</kun></b>",
            "furigana merged": "<kun> 弥[や]</kun><b><kun> 生[よい]</kun></b>",
            "furikanji merged": "<kun> や[弥]</kun><b><kun> よい[生]</kun></b>",
        },
        id="生 readings /3",
    ),
    pytest.param(
        "生",
        "芝生[しばふ]",
        True,
        {
            "kana_only": "しば<b>ふ</b>",
            "furigana": " 芝[しば]<b> 生[ふ]</b>",
            "furikanji": " しば[芝]<b> ふ[生]</b>",
            "kana_only split": "<kun>しば</kun><b><kun>ふ</kun></b>",
            "furigana split": "<kun> 芝[しば]</kun><b><kun> 生[ふ]</kun></b>",
            "furikanji split": "<kun> しば[芝]</kun><b><kun> ふ[生]</kun></b>",
            "kana_only merged": "<kun>しば</kun><b><kun>ふ</kun></b>",
            "furigana merged": "<kun> 芝[しば]</kun><b><kun> 生[ふ]</kun></b>",
            "furikanji merged": "<kun> しば[芝]</kun><b><kun> ふ[生]</kun></b>",
        },
        id="生 readings /4",
    ),
    pytest.param(
        "生",
        "生憎[あいにく]",
        True,
        {
            "kana_only": "<b>あい</b>にく",
            "furigana": "<b> 生[あい]</b> 憎[にく]",
            "furikanji": "<b> あい[生]</b> にく[憎]",
            "kana_only split": "<b><kun>あい</kun></b><kun>にく</kun>",
            "furigana split": "<b><kun> 生[あい]</kun></b><kun> 憎[にく]</kun>",
            "furikanji split": "<b><kun> あい[生]</kun></b><kun> にく[憎]</kun>",
            "kana_only merged": "<b><kun>あい</kun></b><kun>にく</kun>",
            "furigana merged": "<b><kun> 生[あい]</kun></b><kun> 憎[にく]</kun>",
            "furikanji merged": "<b><kun> あい[生]</kun></b><kun> にく[憎]</kun>",
        },
        id="生 readings /5",
    ),
    pytest.param(
        None,
        "１０分[じゅっぷん]と10分[じっぷん]と10冊[じゅっさつ]",
        True,
        {
            "kana_only": "ジュップンとジップンとジュッサツ",
            "furigana": " １０分[ジュップン]と 10分[ジップン]と 10冊[ジュッサツ]",
            "furikanji": " ジュップン[１０分]と ジップン[10分]と ジュッサツ[10冊]",
            "kana_only split": "<on>ジュッ</on><on>プン</on>と<on>ジッ</on><on>プン</on>と<on>ジュッ</on><on>サツ</on>",
            "furigana split": "<on> １０[ジュッ]</on><on> 分[プン]</on>と<on> 10[ジッ]</on><on> 分[プン]</on>と<on>"
            " 10[ジュッ]</on><on> 冊[サツ]</on>",
            "furikanji split": "<on> ジュッ[１０]</on><on> プン[分]</on>と<on> ジッ[10]</on><on> プン[分]</on>と<on>"
            " ジュッ[10]</on><on> サツ[冊]</on>",
            "kana_only merged": "<on>ジュップン</on>と<on>ジップン</on>と<on>ジュッサツ</on>",
            "furigana merged": "<on> １０分[ジュップン]</on>と<on> 10分[ジップン]</on>と<on> 10冊[ジュッサツ]</on>",
            "furikanji merged": "<on> ジュップン[１０分]</on>と<on> ジップン[10分]</on>と<on> ジュッサツ[10冊]</on>",
        },
        id="10 and １０ read as じっ or じゅっ no highlight",
    ),
    pytest.param(
        "分",
        "１０分[じゅっぷん]と10分[じっぷん]と１０冊[じゅっさつ]",
        True,
        {
            "kana_only": "ジュッ<b>プン</b>とジッ<b>プン</b>とジュッサツ",
            "furigana": " １０[ジュッ]<b> 分[プン]</b>と 10[ジッ]<b> 分[プン]</b>と １０冊[ジュッサツ]",
            "furikanji": " ジュッ[１０]<b> プン[分]</b>と ジッ[10]<b> プン[分]</b>と ジュッサツ[１０冊]",
            "kana_only split": "<on>ジュッ</on><b><on>プン</on></b>と<on>ジッ</on><b><on>プン</on></b>と<on>ジュッ</on>"
            "<on>サツ</on>",
            "furigana split": "<on> １０[ジュッ]</on><b><on> 分[プン]</on></b>と<on> 10[ジッ]</on><b><on>"
            " 分[プン]</on></b>と<on> １０[ジュッ]</on><on> 冊[サツ]</on>",
            "furikanji split": "<on> ジュッ[１０]</on><b><on> プン[分]</on></b>と<on> ジッ[10]</on><b><on>"
            " プン[分]</on></b>と<on> ジュッ[１０]</on><on> サツ[冊]</on>",
            # fmt: off
            "kana_only merged": "<on>ジュッ</on><b><on>プン</on></b>と<on>ジッ</on><b><on>プン</on></b>と"
            "<on>ジュッサツ</on>",
            # fmt: on
            "furigana merged": "<on> １０[ジュッ]</on><b><on> 分[プン]</on></b>と<on> 10[ジッ]</on><b><on>"
            " 分[プン]</on></b>と<on> １０冊[ジュッサツ]</on>",
            "furikanji merged": "<on> ジュッ[１０]</on><b><on> プン[分]</on></b>と<on> ジッ[10]</on><b><on>"
            " プン[分]</on></b>と<on> ジュッサツ[１０冊]</on>",
        },
        id="10 and １０ read as じっ or じゅっ highlight",
    ),
    pytest.param(
        "",
        "１[いち] ２[に] ３[さん] ４[よん] ０[ぜろ]",
        True,
        {
            "kana_only": "イチ ニ サン よん ぜろ",
            "furigana": " １[イチ] ２[ニ] ３[サン] ４[よん] ０[ぜろ]",
            "furikanji": " イチ[１] ニ[２] サン[３] よん[４] ぜろ[０]",
            "kana_only split": "<on>イチ</on> <on>ニ</on> <on>サン</on> <kun>よん</kun> <kun>ぜろ</kun>",
            "furigana split": "<on> １[イチ]</on><on> ２[ニ]</on><on> ３[サン]</on><kun> ４[よん]</kun><kun>"
            " ０[ぜろ]</kun>",
            "furikanji split": "<on> イチ[１]</on><on> ニ[２]</on><on> サン[３]</on><kun> よん[４]</kun><kun>"
            " ぜろ[０]</kun>",
            "kana_only merged": "<on>イチ</on> <on>ニ</on> <on>サン</on> <kun>よん</kun> <kun>ぜろ</kun>",
            "furigana merged": "<on> １[イチ]</on><on> ２[ニ]</on><on> ３[サン]</on><kun> ４[よん]</kun><kun>"
            " ０[ぜろ]</kun>",
            "furikanji merged": "<on> イチ[１]</on><on> ニ[２]</on><on> サン[３]</on><kun> よん[４]</kun><kun>"
            " ぜろ[０]</kun>",
        },
        id="More numbers with furigana /1",
    ),
    pytest.param(
        "",
        "３０分[さんじゅっぷん] 40分[よんじゅっぷん] １０時間[じゅうじかん] ５冊[ごさつ]",
        True,
        {
            "kana_only": "サンジュップン よんジュップン ジュウジカン ゴサツ",
            "furigana": " ３０分[サンジュップン] 40分[よんジュップン] １０時間[ジュウジカン] ５冊[ゴサツ]",
            "furikanji": " サンジュップン[３０分] よんジュップン[40分] ジュウジカン[１０時間] ゴサツ[５冊]",
            "kana_only split": "<on>サン</on><on>ジュッ</on><on>プン</on> <kun>よん</kun><on>ジュッ</on><on>プン</on>"
            " <on>"
            "ジュウ</on><on>ジ</on><on>カン</on> <on>ゴ</on><on>サツ</on>",
            "furigana split": "<on> ３０[サンジュッ]</on><on> 分[プン]</on><mix> 40[よんジュッ]</mix><on>"
            " 分[プン]</on><on> １０[ジュウ]</on><on> 時[ジ]</on><on> 間[カン]</on><on>"
            " ５[ゴ]</on><on>"
            " 冊[サツ]</on>",
            "furikanji split": "<on> サンジュッ[３０]</on><on> プン[分]</on><mix> よんジュッ[40]</mix><on>"
            " プン[分]</on><on> ジュウ[１０]</on><on> ジ[時]</on><on> カン[間]</on><on>"
            " ゴ[５]</on><on> サツ[冊]</on>",
            "kana_only merged": "<on>サンジュップン</on> <kun>よん</kun><on>ジュップン</on> <on>ジュウジカン</on>"
            " <on>ゴサツ</on>",
            "furigana merged": "<on> ３０分[サンジュップン]</on><mix> 40[よんジュッ]</mix><on> 分[プン]</on><on>"
            " １０時間[ジュウジカン]</on><on> ５冊[ゴサツ]</on>",
            "furikanji merged": "<on> サンジュップン[３０分]</on><mix> よんジュッ[40]</mix><on> プン[分]</on><on>"
            " ジュウジカン[１０時間]</on><on> ゴサツ[５冊]</on>",
        },
        id="Small tens",
    ),
    pytest.param(
        "",
        "15歳[じゅうごさい]に １１個[じゅういっこ]の ７番目[ななばんめ]をもらった。",
        True,
        {
            "kana_only": "ジュウゴサイに ジュウイッコの ななバンめをもらった。",
            "furigana": " 15歳[ジュウゴサイ]に １１個[ジュウイッコ]の ７番目[ななバンめ]をもらった。",
            "furikanji": " ジュウゴサイ[15歳]に ジュウイッコ[１１個]の ななバンめ[７番目]をもらった。",
            "kana_only split": "<on>ジュウ</on><on>ゴ</on><on>サイ</on>に <on>ジュウ</on><on>イッ</on><on>コ</on>の"
            " <kun>なな</kun><on>バン</on><kun>め</kun>をもらった。",
            "furigana split": "<on> 15[ジュウゴ]</on><on> 歳[サイ]</on>に<on> １１[ジュウイッ]</on><on>"
            " 個[コ]</on>の<kun> ７[なな]</kun><on> 番[バン]</on><kun> 目[め]</kun>をもらった。",
            "furikanji split": "<on> ジュウゴ[15]</on><on> サイ[歳]</on>に<on> ジュウイッ[１１]</on><on>"
            " コ[個]</on>の<kun> なな[７]</kun><on> バン[番]</on><kun> め[目]</kun>をもらった。",
            "kana_only merged": "<on>ジュウゴサイ</on>に <on>ジュウイッコ</on>の"
            " <kun>なな</kun><on>バン</on><kun>め</kun>をもらった。",
            "furigana merged": "<on> 15歳[ジュウゴサイ]</on>に<on> １１個[ジュウイッコ]</on>の"
            "<kun> ７[なな]</kun><on> 番[バン]</on><kun> 目[め]</kun>をもらった。",
            "furikanji merged": "<on> ジュウゴサイ[15歳]</on>に<on> ジュウイッコ[１１個]</on>の"
            "<kun> なな[７]</kun><on> バン[番]</on><kun> め[目]</kun>をもらった。",
        },
        id="Small teens",
    ),
    pytest.param(
        "",
        "123[ひゃくにじゅうさん] 402[よんひゃくに] ３２０[さんびゃくにじゅう]"
        " 888[はっぴゃくはちじゅうはち]"
        " ４６６０[よんせんろっぴゃくろくじゅう]",
        True,
        {
            "kana_only": "ヒャクニジュウサン よんヒャクニ サンビャクニジュウ ハッピャクハチジュウハチ"
            " よんセンロッピャクロクジュウ",
            "furigana": " 123[ヒャクニジュウサン] 402[よんヒャクニ] ３２０[サンビャクニジュウ]"
            " 888[ハッピャクハチジュウハチ] ４６６０[よんセンロッピャクロクジュウ]",
            "furikanji": " ヒャクニジュウサン[123] よんヒャクニ[402] サンビャクニジュウ[３２０]"
            " ハッピャクハチジュウハチ[888] よんセンロッピャクロクジュウ[４６６０]",
            "kana_only split": "<on>ヒャク</on><on>ニ</on><on>ジュウ</on><on>サン</on> <kun>よん</kun><on>ヒャク</on>"
            "<on>ニ</on> <on>サン</on><on>ビャク</on><on>ニ</on><on>ジュウ</on> <on>ハッ</on>"
            "<on>ピャク</on><on>ハチ</on><on>ジュウ</on><on>ハチ</on> <kun>よん</kun><on>"
            "セン</on><on>ロッ</on><on>ピャク</on><on>ロク</on><on>ジュウ</on>",
            "furigana split": "<mix> 123[ヒャクニジュウサン]</mix><mix> 402[よんヒャクニ]</mix><mix>"
            " ３２０[サンビャクニジュウ]</mix><mix> 888[ハッピャクハチジュウハチ]</mix>"
            "<mix> ４６６０[よんセンロッピャクロクジュウ]</mix>",
            "furikanji split": "<mix> ヒャクニジュウサン[123]</mix><mix> よんヒャクニ[402]</mix><mix>"
            " サンビャクニジュウ[３２０]</mix><mix> ハッピャクハチジュウハチ[888]</mix>"
            "<mix> よんセンロッピャクロクジュウ[４６６０]</mix>",
            "kana_only merged": "<on>ヒャクニジュウサン</on> <kun>よん</kun><on>ヒャクニ</on> <on>サンビャクニジュウ</on>"
            " <on>ハッピャクハチジュウハチ</on> <kun>よん</kun><on>センロッピャクロクジュウ</on>",
            "furigana merged": "<on> 123[ヒャクニジュウサン]</on><mix> 402[よんヒャクニ]</mix><on>"
            " ３２０[サンビャクニジュウ]</on><on> 888[ハッピャクハチジュウハチ]</on><mix> ４６６０[よんセンロッピャクロクジュウ]</mix>",
            "furikanji merged": "<on> ヒャクニジュウサン[123]</on><mix> よんヒャクニ[402]</mix><on>"
            " サンビャクニジュウ[３２０]</on><on> ハッピャクハチジュウハチ[888]</on><mix> よんセンロッピャクロクジュウ[４６６０]</mix>",
        },
        id="Three digit numbers",
    ),
    # A digit run is converted to kanji to be read, and 24 is three kanji for two digits, so the
    # reading of that third kanji had no position in the two characters the rest of the pipeline
    # was given: it was dropped from the output, and a reading with fewer mora than the converted
    # word has kanji raised. The whole run is one chunk either way, tagged mix where it reads
    # both ways, so only the kana-only modes show a reading per kanji.
    pytest.param(
        "",
        "24[にじゅうよん]",
        True,
        {
            "furigana": " 24[ニジュウよん]",
            "furigana split": "<mix> 24[ニジュウよん]</mix>",
            "furigana merged": "<mix> 24[ニジュウよん]</mix>",
            "furikanji": " ニジュウよん[24]",
            "furikanji split": "<mix> ニジュウよん[24]</mix>",
            "furikanji merged": "<mix> ニジュウよん[24]</mix>",
            "kana_only": "ニジュウよん",
            "kana_only split": "<on>ニ</on><on>ジュウ</on><kun>よん</kun>",
            "kana_only merged": "<on>ニジュウ</on><kun>よん</kun>",
        },
        id="two digits read as three kanji, the last one kun",
    ),
    pytest.param(
        "",
        "77[しちじゅうなな]",
        True,
        {
            "furigana": " 77[シチジュウなな]",
            "furigana split": "<mix> 77[シチジュウなな]</mix>",
            "furigana merged": "<mix> 77[シチジュウなな]</mix>",
            "furikanji": " シチジュウなな[77]",
            "furikanji split": "<mix> シチジュウなな[77]</mix>",
            "furikanji merged": "<mix> シチジュウなな[77]</mix>",
            "kana_only": "シチジュウなな",
            "kana_only split": "<on>シチ</on><on>ジュウ</on><kun>なな</kun>",
            "kana_only merged": "<on>シチジュウ</on><kun>なな</kun>",
        },
        id="the same digit read two ways, the on reading first",
    ),
    # Too few mora for the kanji the digits convert into is nothing a reading can be made of,
    # so this only asks that the digits and the whole reading survive it.
    pytest.param(
        "",
        "77[ひと]",
        True,
        {
            "furigana": " 77[ひと]",
            "furigana split": "<mix> 77[ひと]</mix>",
            "furigana merged": "<mix> 77[ひと]</mix>",
            "furikanji": " ひと[77]",
            "furikanji split": "<mix> ひと[77]</mix>",
            "furikanji merged": "<mix> ひと[77]</mix>",
            "kana_only": "ひと",
            "kana_only split": "<kun>ひ</kun><juk>と</juk>",
            "kana_only merged": "<kun>ひ</kun><juk>と</juk>",
        },
        id="fewer mora than the digits convert into kanji",
    ),
    # The kanji to highlight is one the digits convert into, not one the sentence writes: the run
    # is a single chunk, so the modes that show a surface bold all of it and only the kana-only
    # ones bold that kanji's own reading.
    pytest.param(
        "十",
        "24[にじゅうよん]",
        True,
        {
            "furigana": "<b> 24[ニジュウよん]</b>",
            "furigana split": "<b><mix> 24[ニジュウよん]</mix></b>",
            "furigana merged": "<b><mix> 24[ニジュウよん]</mix></b>",
            "furikanji": "<b> ニジュウよん[24]</b>",
            "furikanji split": "<b><mix> ニジュウよん[24]</mix></b>",
            "furikanji merged": "<b><mix> ニジュウよん[24]</mix></b>",
            "kana_only": "ニ<b>ジュウ</b>よん",
            "kana_only split": "<on>ニ</on><b><on>ジュウ</on></b><kun>よん</kun>",
            "kana_only merged": "<on>ニ</on><b><on>ジュウ</on></b><kun>よん</kun>",
        },
        id="a highlighted kanji in the middle of a digit run",
    ),
    pytest.param(
        "四",
        "24[にじゅうよん]",
        True,
        {
            "furigana": "<b> 24[ニジュウよん]</b>",
            "furigana split": "<b><mix> 24[ニジュウよん]</mix></b>",
            "furigana merged": "<b><mix> 24[ニジュウよん]</mix></b>",
            "furikanji": "<b> ニジュウよん[24]</b>",
            "furikanji split": "<b><mix> ニジュウよん[24]</mix></b>",
            "furikanji merged": "<b><mix> ニジュウよん[24]</mix></b>",
            "kana_only": "ニジュウ<b>よん</b>",
            "kana_only split": "<on>ニ</on><on>ジュウ</on><b><kun>よん</kun></b>",
            "kana_only merged": "<on>ニジュウ</on><b><kun>よん</kun></b>",
        },
        id="a highlighted kanji at the end of a digit run",
    ),
    pytest.param(
        "十",
        "24[にじゅうよん]と 十[じゅう]",
        True,
        {
            "furigana": "<b> 24[ニジュウよん]</b>と<b> 十[ジュウ]</b>",
            "furigana split": "<b><mix> 24[ニジュウよん]</mix></b>と<b><on> 十[ジュウ]</on></b>",
            "furigana merged": "<b><mix> 24[ニジュウよん]</mix></b>と<b><on> 十[ジュウ]</on></b>",
            "furikanji": "<b> ニジュウよん[24]</b>と<b> ジュウ[十]</b>",
            "furikanji split": "<b><mix> ニジュウよん[24]</mix></b>と<b><on> ジュウ[十]</on></b>",
            "furikanji merged": "<b><mix> ニジュウよん[24]</mix></b>と<b><on> ジュウ[十]</on></b>",
            "kana_only": "ニ<b>ジュウ</b>よんと <b>ジュウ</b>",
            "kana_only split": "<on>ニ</on><b><on>ジュウ</on></b><kun>よん</kun>と <b><on>ジュウ</on></b>",
            "kana_only merged": "<on>ニ</on><b><on>ジュウ</on></b><kun>よん</kun>と <b><on>ジュウ</on></b>",
        },
        id="the same kanji inside a digit run and written out",
    ),
    pytest.param(
        "円",
        "10000円[いちまんえん]",
        True,
        {
            "furigana": " 10000[イチマン]<b> 円[エン]</b>",
            "furigana split": "<mix> 10000[イチマン]</mix><b><on> 円[エン]</on></b>",
            "furigana merged": "<on> 10000[イチマン]</on><b><on> 円[エン]</on></b>",
            "furikanji": " イチマン[10000]<b> エン[円]</b>",
            "furikanji split": "<mix> イチマン[10000]</mix><b><on> エン[円]</on></b>",
            "furikanji merged": "<on> イチマン[10000]</on><b><on> エン[円]</on></b>",
            "kana_only": "イチマン<b>エン</b>",
            "kana_only split": "<on>イチ</on><on>マン</on><b><on>エン</on></b>",
            "kana_only merged": "<on>イチマン</on><b><on>エン</on></b>",
        },
        id="Myriad numbers keep the 一 - with highlight",
    ),
    # The 万 of 10000 has no digit of its own either, so the whole run bolds - and the run reads
    # on all through, so it keeps its <on> where the merged modes do not force a mix.
    pytest.param(
        "万",
        "10000円[いちまんえん]",
        True,
        {
            "furigana": "<b> 10000[イチマン]</b> 円[エン]",
            "furigana split": "<b><mix> 10000[イチマン]</mix></b><on> 円[エン]</on>",
            "furigana merged": "<b><on> 10000[イチマン]</on></b><on> 円[エン]</on>",
            "furikanji": "<b> イチマン[10000]</b> エン[円]",
            "furikanji split": "<b><mix> イチマン[10000]</mix></b><on> エン[円]</on>",
            "furikanji merged": "<b><on> イチマン[10000]</on></b><on> エン[円]</on>",
            "kana_only": "イチ<b>マン</b>エン",
            "kana_only split": "<on>イチ</on><b><on>マン</on></b><on>エン</on>",
            "kana_only merged": "<on>イチ</on><b><on>マン</on></b><on>エン</on>",
        },
        id="Myriad numbers keep the 一 - the 万 highlighted inside the digits",
    ),
    pytest.param(
        "",
        "10000000[いっせんまん] 100000000[いちおく] 1000000000000[いっちょう]",
        True,
        {
            "furigana": " 10000000[イッセンマン] 100000000[イチオク] 1000000000000[イッチョウ]",
            "furigana split": "<mix> 10000000[イッセンマン]</mix><mix> 100000000[イチオク]</mix>"
            "<mix> 1000000000000[イッチョウ]</mix>",
            "furigana merged": "<on> 10000000[イッセンマン]</on><on> 100000000[イチオク]</on>"
            "<on> 1000000000000[イッチョウ]</on>",
            "furikanji": " イッセンマン[10000000] イチオク[100000000] イッチョウ[1000000000000]",
            "furikanji split": "<mix> イッセンマン[10000000]</mix><mix> イチオク[100000000]</mix>"
            "<mix> イッチョウ[1000000000000]</mix>",
            "furikanji merged": "<on> イッセンマン[10000000]</on><on> イチオク[100000000]</on>"
            "<on> イッチョウ[1000000000000]</on>",
            "kana_only": "イッセンマン イチオク イッチョウ",
            "kana_only split": "<on>イッ</on><on>セン</on><on>マン</on> <on>イチ</on><on>オク</on>"
            " <on>イッ</on><on>チョウ</on>",
            "kana_only merged": "<on>イッセンマン</on> <on>イチオク</on> <on>イッチョウ</on>",
        },
        id="Myriad numbers keep the 一 - 一千万, 一億, 一兆",
    ),
    pytest.param(
        "",
        "1000[せん] 1000000[ひゃくまん]",
        True,
        {
            "furigana": " 1000[セン] 1000000[ヒャクマン]",
            "furigana split": "<on> 1000[セン]</on><mix> 1000000[ヒャクマン]</mix>",
            "furigana merged": "<on> 1000[セン]</on><on> 1000000[ヒャクマン]</on>",
            "furikanji": " セン[1000] ヒャクマン[1000000]",
            "furikanji split": "<on> セン[1000]</on><mix> ヒャクマン[1000000]</mix>",
            "furikanji merged": "<on> セン[1000]</on><on> ヒャクマン[1000000]</on>",
            "kana_only": "セン ヒャクマン",
            "kana_only split": "<on>セン</on> <on>ヒャク</on><on>マン</on>",
            "kana_only merged": "<on>セン</on> <on>ヒャクマン</on>",
        },
        id="十, 百 and a lone 千 still drop the 一",
    ),
    pytest.param(
        "",
        "為[し]て 為[し]た 為[し]ました 為[さ]れる 為[し]ろ 為[し]ません それを為[し]",
        True,
        {
            "kana_only": "して した しました される しろ しません それをし",
            "furigana": " 為[し]て 為[し]た 為[し]ました 為[さ]れる 為[し]ろ 為[し]ません それを 為[し]",
            "furikanji": " し[為]て し[為]た し[為]ました さ[為]れる し[為]ろ し[為]ません それを し[為]",
            "kana_only split": "<kun>し</kun><oku>て</oku> <kun>し</kun><oku>た</oku> <kun>し</kun><oku>ました</oku>"
            " <kun>さ</kun><oku>れる</oku> <kun>し</kun><oku>ろ</oku> <kun>し</kun><oku>ません</oku>"
            " それを<kun>し</kun>",
            "furigana split": "<kun> 為[し]</kun><oku>て</oku><kun> 為[し]</kun><oku>た</oku><kun>"
            " 為[し]</kun><oku>ました</oku><kun> 為[さ]</kun><oku>れる</oku><kun> 為[し]</kun><oku>ろ</oku>"
            "<kun> 為[し]</kun><oku>ません</oku> それを<kun> 為[し]</kun>",
            "furikanji split": "<kun> し[為]</kun><oku>て</oku><kun> し[為]</kun><oku>た</oku><kun>"
            " し[為]</kun><oku>ました</oku><kun> さ[為]</kun><oku>れる</oku><kun> し[為]</kun><oku>ろ</oku>"
            "<kun> し[為]</kun><oku>ません</oku> それを<kun> し[為]</kun>",
            "kana_only merged": "<kun>し</kun><oku>て</oku> <kun>し</kun><oku>た</oku> <kun>し</kun>"
            "<oku>ました</oku> <kun>さ</kun><oku>れる</oku> <kun>し</kun><oku>ろ</oku> <kun>し</kun>"
            "<oku>ません</oku> それを<kun>し</kun>",
            "furigana merged": "<kun> 為[し]</kun><oku>て</oku><kun> 為[し]</kun><oku>た</oku><kun>"
            " 為[し]</kun><oku>ました</oku><kun> 為[さ]</kun><oku>れる</oku><kun> 為[し]</kun><oku>ろ</oku>"
            "<kun> 為[し]</kun><oku>ません</oku> それを<kun> 為[し]</kun>",
            "furikanji merged": "<kun> し[為]</kun><oku>て</oku><kun> し[為]</kun><oku>た</oku><kun>"
            " し[為]</kun><oku>ました</oku><kun> さ[為]</kun><oku>れる</oku><kun> し[為]</kun><oku>ろ</oku>"
            "<kun> し[為]</kun><oku>ません</oku> それを<kun> し[為]</kun>",
        },
        id="為る conjugations /1",
    ),
    pytest.param(
        "",
        "為[し]まった 為[し]ない 為[し]なかった 為[さ]せない 為[さ]せた 為[さ]せました",
        True,
        {
            "kana_only": "しまった しない しなかった させない させた させました",
            "furigana": " 為[し]まった 為[し]ない 為[し]なかった 為[さ]せない 為[さ]せた 為[さ]せました",
            "furikanji": " し[為]まった し[為]ない し[為]なかった さ[為]せない さ[為]せた さ[為]せました",
            "kana_only split": "<kun>し</kun><oku>まった</oku> <kun>し</kun><oku>ない</oku>"
            " <kun>し</kun><oku>なかった</oku>"
            " <kun>さ</kun><oku>せない</oku> <kun>さ</kun><oku>せた</oku>"
            " <kun>さ</kun><oku>せました</oku>",
            "furigana split": "<kun> 為[し]</kun><oku>まった</oku><kun> 為[し]</kun><oku>ない</oku><kun>"
            " 為[し]</kun><oku>なかった</oku><kun> 為[さ]</kun><oku>せない</oku><kun> 為[さ]</kun><oku>せた</oku>"
            "<kun> 為[さ]</kun><oku>せました</oku>",
            "furikanji split": "<kun> し[為]</kun><oku>まった</oku><kun> し[為]</kun><oku>ない</oku><kun>"
            " し[為]</kun><oku>なかった</oku><kun> さ[為]</kun><oku>せない</oku><kun> さ[為]</kun><oku>せた</oku>"
            "<kun> さ[為]</kun><oku>せました</oku>",
            "kana_only merged": "<kun>し</kun><oku>まった</oku> <kun>し</kun><oku>ない</oku> <kun>し</kun>"
            "<oku>なかった</oku> <kun>さ</kun><oku>せない</oku> <kun>さ</kun><oku>せた</oku> <kun>さ</kun>"
            "<oku>せました</oku>",
            "furigana merged": "<kun> 為[し]</kun><oku>まった</oku><kun> 為[し]</kun><oku>ない</oku><kun>"
            " 為[し]</kun><oku>なかった</oku><kun> 為[さ]</kun><oku>せない</oku><kun> 為[さ]</kun><oku>せた</oku>"
            "<kun> 為[さ]</kun><oku>せました</oku>",
            "furikanji merged": "<kun> し[為]</kun><oku>まった</oku><kun> し[為]</kun><oku>ない</oku><kun>"
            " し[為]</kun><oku>なかった</oku><kun> さ[為]</kun><oku>せない</oku><kun> さ[為]</kun><oku>せた</oku>"
            "<kun> さ[為]</kun><oku>せました</oku>",
        },
        id="為る conjugations /2",
    ),
    pytest.param(
        "",
        "為[さ]せて 為[さ]せられ 為[さ]せろ 為[さ]せません 為[さ]せて 為[さ]せられた",
        True,
        {
            "kana_only": "させて させられ させろ させません させて させられた",
            "furigana": " 為[さ]せて 為[さ]せられ 為[さ]せろ 為[さ]せません 為[さ]せて 為[さ]せられた",
            "furikanji": " さ[為]せて さ[為]せられ さ[為]せろ さ[為]せません さ[為]せて さ[為]せられた",
            "kana_only split": "<kun>さ</kun><oku>せて</oku> <kun>さ</kun><oku>せられ</oku> <kun>さ</kun><oku>せろ</oku>"
            " <kun>さ</kun><oku>せません</oku> <kun>さ</kun><oku>せて</oku>"
            " <kun>さ</kun><oku>せられた</oku>",
            "furigana split": "<kun> 為[さ]</kun><oku>せて</oku><kun> 為[さ]</kun><oku>せられ</oku><kun>"
            " 為[さ]</kun><oku>せろ</oku><kun> 為[さ]</kun><oku>せません</oku><kun> 為[さ]</kun><oku>せて</oku>"
            "<kun> 為[さ]</kun><oku>せられた</oku>",
            "furikanji split": "<kun> さ[為]</kun><oku>せて</oku><kun> さ[為]</kun><oku>せられ</oku><kun>"
            " さ[為]</kun><oku>せろ</oku><kun> さ[為]</kun><oku>せません</oku><kun> さ[為]</kun><oku>せて</oku>"
            "<kun> さ[為]</kun><oku>せられた</oku>",
            "kana_only merged": "<kun>さ</kun><oku>せて</oku> <kun>さ</kun><oku>せられ</oku> <kun>さ</kun>"
            "<oku>せろ</oku> <kun>さ</kun><oku>せません</oku> <kun>さ</kun><oku>せて</oku> <kun>さ</kun>"
            "<oku>せられた</oku>",
            "furigana merged": "<kun> 為[さ]</kun><oku>せて</oku><kun> 為[さ]</kun><oku>せられ</oku><kun>"
            " 為[さ]</kun><oku>せろ</oku><kun> 為[さ]</kun><oku>せません</oku><kun> 為[さ]</kun><oku>せて</oku>"
            "<kun> 為[さ]</kun><oku>せられた</oku>",
            "furikanji merged": "<kun> さ[為]</kun><oku>せて</oku><kun> さ[為]</kun><oku>せられ</oku><kun>"
            " さ[為]</kun><oku>せろ</oku><kun> さ[為]</kun><oku>せません</oku><kun> さ[為]</kun><oku>せて</oku>"
            "<kun> さ[為]</kun><oku>せられた</oku>",
        },
        id="為る conjugations /3",
    ),
    pytest.param(
        "",
        "為[し]よう 為[さ]せよう 為[し]ましょう 為[せ]ずに 為[さ]せずに",
        True,
        {
            "kana_only": "しよう させよう しましょう せずに させずに",
            "furigana": " 為[し]よう 為[さ]せよう 為[し]ましょう 為[せ]ずに 為[さ]せずに",
            "furikanji": " し[為]よう さ[為]せよう し[為]ましょう せ[為]ずに さ[為]せずに",
            "kana_only split": "<kun>し</kun><oku>よう</oku> <kun>さ</kun><oku>せよう</oku>"
            " <kun>し</kun><oku>ましょう</oku> <kun>せ</kun><oku>ず</oku>に"
            " <kun>さ</kun><oku>せず</oku>に",
            "furigana split": "<kun> 為[し]</kun><oku>よう</oku><kun> 為[さ]</kun><oku>せよう</oku><kun>"
            " 為[し]</kun><oku>ましょう</oku><kun> 為[せ]</kun><oku>ず</oku>に<kun> 為[さ]</kun><oku>せず</oku>に",
            "furikanji split": "<kun> し[為]</kun><oku>よう</oku><kun> さ[為]</kun><oku>せよう</oku><kun>"
            " し[為]</kun><oku>ましょう</oku><kun> せ[為]</kun><oku>ず</oku>に<kun> さ[為]</kun><oku>せず</oku>に",
            "kana_only merged": "<kun>し</kun><oku>よう</oku> <kun>さ</kun><oku>せよう</oku> <kun>し</kun>"
            "<oku>ましょう</oku> <kun>せ</kun><oku>ず</oku>に <kun>さ</kun><oku>せず</oku>に",
            "furigana merged": "<kun> 為[し]</kun><oku>よう</oku><kun> 為[さ]</kun><oku>せよう</oku><kun>"
            " 為[し]</kun><oku>ましょう</oku><kun> 為[せ]</kun><oku>ず</oku>に<kun> 為[さ]</kun><oku>せず</oku>に",
            "furikanji merged": "<kun> し[為]</kun><oku>よう</oku><kun> さ[為]</kun><oku>せよう</oku><kun>"
            " し[為]</kun><oku>ましょう</oku><kun> せ[為]</kun><oku>ず</oku>に<kun> さ[為]</kun><oku>せず</oku>に",
        },
        id="為る conjugations /4",
    ),
    pytest.param(
        "不",
        # The shorter onyomi フ should be matched instead of フツ
        "不都合[ふつごう]",
        True,
        {
            "kana_only": "<b>フ</b>ツゴウ",
            "furigana": "<b> 不[フ]</b> 都合[ツゴウ]",
            "furikanji": "<b> フ[不]</b> ツゴウ[都合]",
            "kana_only split": "<b><on>フ</on></b><on>ツ</on><on>ゴウ</on>",
            "furigana split": "<b><on> 不[フ]</on></b><on> 都[ツ]</on><on> 合[ゴウ]</on>",
            "furikanji split": "<b><on> フ[不]</on></b><on> ツ[都]</on><on> ゴウ[合]</on>",
            "kana_only merged": "<b><on>フ</on></b><on>ツゴウ</on>",
            "furigana merged": "<b><on> 不[フ]</on></b><on> 都合[ツゴウ]</on>",
            "furikanji merged": "<b><on> フ[不]</on></b><on> ツゴウ[都合]</on>",
        },
        id="correct onyomi for 不 in 不都合",
    ),
    pytest.param(
        "",
        "嗅[か]がせろって",
        True,
        {
            "kana_only": "かがせろって",
            "furigana": " 嗅[か]がせろって",
            "furikanji": " か[嗅]がせろって",
            "kana_only split": "<kun>か</kun><oku>がせろ</oku>って",
            "furigana split": "<kun> 嗅[か]</kun><oku>がせろ</oku>って",
            "furikanji split": "<kun> か[嗅]</kun><oku>がせろ</oku>って",
            "kana_only merged": "<kun>か</kun><oku>がせろ</oku>って",
            "furigana merged": "<kun> 嗅[か]</kun><oku>がせろ</oku>って",
            "furikanji merged": "<kun> か[嗅]</kun><oku>がせろ</oku>って",
        },
        id="matches okuri for causative imperative godan gu verb",
    ),
    pytest.param(
        "",
        "飲[の]ませろ!",
        True,
        {
            "kana_only": "のませろ!",
            "furigana": " 飲[の]ませろ!",
            "furikanji": " の[飲]ませろ!",
            "kana_only split": "<kun>の</kun><oku>ませろ</oku>!",
            "furigana split": "<kun> 飲[の]</kun><oku>ませろ</oku>!",
            "furikanji split": "<kun> の[飲]</kun><oku>ませろ</oku>!",
            "kana_only merged": "<kun>の</kun><oku>ませろ</oku>!",
            "furigana merged": "<kun> 飲[の]</kun><oku>ませろ</oku>!",
            "furikanji merged": "<kun> の[飲]</kun><oku>ませろ</oku>!",
        },
        id="matches okuri for causative imperative godan mu verb",
    ),
    pytest.param(
        "",
        "話[はな]させろ!",
        True,
        {
            "kana_only": "はなさせろ!",
            "furigana": " 話[はな]させろ!",
            "furikanji": " はな[話]させろ!",
            "kana_only split": "<kun>はな</kun><oku>させろ</oku>!",
            "furigana split": "<kun> 話[はな]</kun><oku>させろ</oku>!",
            "furikanji split": "<kun> はな[話]</kun><oku>させろ</oku>!",
            "kana_only merged": "<kun>はな</kun><oku>させろ</oku>!",
            "furigana merged": "<kun> 話[はな]</kun><oku>させろ</oku>!",
            "furikanji merged": "<kun> はな[話]</kun><oku>させろ</oku>!",
        },
        id="matches okuri for causative imperative godan su verb",
    ),
    pytest.param(
        "",
        "食[た]べさせろ!",
        True,
        {
            "kana_only": "たべさせろ!",
            "furigana": " 食[た]べさせろ!",
            "furikanji": " た[食]べさせろ!",
            "kana_only split": "<kun>た</kun><oku>べさせろ</oku>!",
            "furigana split": "<kun> 食[た]</kun><oku>べさせろ</oku>!",
            "furikanji split": "<kun> た[食]</kun><oku>べさせろ</oku>!",
            "kana_only merged": "<kun>た</kun><oku>べさせろ</oku>!",
            "furigana merged": "<kun> 食[た]</kun><oku>べさせろ</oku>!",
            "furikanji merged": "<kun> た[食]</kun><oku>べさせろ</oku>!",
        },
        id="matches okuri for causative imperative ichidan verb",
    ),
    pytest.param(
        "",
        "有[あ]らせろ!",
        True,
        {
            "kana_only": "あらせろ!",
            "furigana": " 有[あ]らせろ!",
            "furikanji": " あ[有]らせろ!",
            "kana_only split": "<kun>あ</kun><oku>らせろ</oku>!",
            "furigana split": "<kun> 有[あ]</kun><oku>らせろ</oku>!",
            "furikanji split": "<kun> あ[有]</kun><oku>らせろ</oku>!",
            "kana_only merged": "<kun>あ</kun><oku>らせろ</oku>!",
            "furigana merged": "<kun> 有[あ]</kun><oku>らせろ</oku>!",
            "furikanji merged": "<kun> あ[有]</kun><oku>らせろ</oku>!",
        },
        id="matches okuri for causative imperative godan aru verb",
    ),
    pytest.param(
        "",
        "博[はく]している",
        False,
        {
            "kana_only": "はくしている",
            "furigana": " 博[はく]している",
            "furikanji": " はく[博]している",
            "kana_only split": "<on>はく</on><oku>している</oku>",
            "furigana split": "<on> 博[はく]</on><oku>している</oku>",
            "furikanji split": "<on> はく[博]</on><oku>している</oku>",
            "kana_only merged": "<on>はく</on><oku>している</oku>",
            "furigana merged": "<on> 博[はく]</on><oku>している</oku>",
            "furikanji merged": "<on> はく[博]</on><oku>している</oku>",
        },
        id="matches single-kanji onyomi す/する verbs okuri /1",
    ),
    pytest.param(
        "愛",
        "愛[あい]せるか？",
        False,
        {
            "kana_only": "<b>あいせる</b>か？",
            "furigana": "<b> 愛[あい]せる</b>か？",
            "furikanji": "<b> あい[愛]せる</b>か？",
            "kana_only split": "<b><on>あい</on><oku>せる</oku></b>か？",
            "furigana split": "<b><on> 愛[あい]</on><oku>せる</oku></b>か？",
            "furikanji split": "<b><on> あい[愛]</on><oku>せる</oku></b>か？",
            "kana_only merged": "<b><on>あい</on><oku>せる</oku></b>か？",
            "furigana merged": "<b><on> 愛[あい]</on><oku>せる</oku></b>か？",
            "furikanji merged": "<b><on> あい[愛]</on><oku>せる</oku></b>か？",
        },
        id="matches single-kanji onyomi す/する verbs okuri /2",
    ),
    pytest.param(
        "",
        "化[か]させない",
        False,
        {
            "kana_only": "かさせない",
            "furigana": " 化[か]させない",
            "furikanji": " か[化]させない",
            "kana_only split": "<on>か</on><oku>させない</oku>",
            "furigana split": "<on> 化[か]</on><oku>させない</oku>",
            "furikanji split": "<on> か[化]</on><oku>させない</oku>",
            "kana_only merged": "<on>か</on><oku>させない</oku>",
            "furigana merged": "<on> 化[か]</on><oku>させない</oku>",
            "furikanji merged": "<on> か[化]</on><oku>させない</oku>",
        },
        id="matches single-kanji onyomi す/する verbs okuri /3",
    ),
    pytest.param(
        "呈",
        "呈[てい]さなかった",
        False,
        {
            "kana_only": "<b>ていさなかった</b>",
            "furigana": "<b> 呈[てい]さなかった</b>",
            "furikanji": "<b> てい[呈]さなかった</b>",
            "kana_only split": "<b><on>てい</on><oku>さなかった</oku></b>",
            "furigana split": "<b><on> 呈[てい]</on><oku>さなかった</oku></b>",
            "furikanji split": "<b><on> てい[呈]</on><oku>さなかった</oku></b>",
            "kana_only merged": "<b><on>てい</on><oku>さなかった</oku></b>",
            "furigana merged": "<b><on> 呈[てい]</on><oku>さなかった</oku></b>",
            "furikanji merged": "<b><on> てい[呈]</on><oku>さなかった</oku></b>",
        },
        id="matches single-kanji onyomi す/する verbs okuri /4",
    ),
    pytest.param(
        "察",
        "察[さっ]していなかった",
        False,
        {
            "kana_only": "<b>さっしていなかった</b>",
            "furigana": "<b> 察[さっ]していなかった</b>",
            "furikanji": "<b> さっ[察]していなかった</b>",
            "kana_only split": "<b><on>さっ</on><oku>していなかった</oku></b>",
            "furigana split": "<b><on> 察[さっ]</on><oku>していなかった</oku></b>",
            "furikanji split": "<b><on> さっ[察]</on><oku>していなかった</oku></b>",
            "kana_only merged": "<b><on>さっ</on><oku>していなかった</oku></b>",
            "furigana merged": "<b><on> 察[さっ]</on><oku>していなかった</oku></b>",
            "furikanji merged": "<b><on> さっ[察]</on><oku>していなかった</oku></b>",
        },
        id="matches single-kanji onyomi small tsu す verbs okuri /1",
    ),
    pytest.param(
        "察",
        "察[さっ]されるかも",
        False,
        {
            "kana_only": "<b>さっされる</b>かも",
            "furigana": "<b> 察[さっ]される</b>かも",
            "furikanji": "<b> さっ[察]される</b>かも",
            "kana_only split": "<b><on>さっ</on><oku>される</oku></b>かも",
            "furigana split": "<b><on> 察[さっ]</on><oku>される</oku></b>かも",
            "furikanji split": "<b><on> さっ[察]</on><oku>される</oku></b>かも",
            "kana_only merged": "<b><on>さっ</on><oku>される</oku></b>かも",
            "furigana merged": "<b><on> 察[さっ]</on><oku>される</oku></b>かも",
            "furikanji merged": "<b><on> さっ[察]</on><oku>される</oku></b>かも",
        },
        id="matches single-kanji onyomi small tsu す verbs okuri /2",
    ),
    pytest.param(
        "欲",
        "欲[ほっ]すれば、欲[ほ]しがれば、呉[く]れましょう",
        False,
        {
            "kana_only": "<b>ほっすれば</b>、<b>ほしがれば</b>、くれましょう",
            "furigana": "<b> 欲[ほっ]すれば</b>、<b> 欲[ほ]しがれば</b>、 呉[く]れましょう",
            "furikanji": "<b> ほっ[欲]すれば</b>、<b> ほ[欲]しがれば</b>、 く[呉]れましょう",
            "kana_only split": "<b><kun>ほっ</kun><oku>すれば</oku></b>、<b><kun>ほ</kun><oku>しがれば</oku></b>、"
            "<kun>く</kun><oku>れましょう</oku>",
            "furigana split": "<b><kun> 欲[ほっ]</kun><oku>すれば</oku></b>、<b><kun>"
            " 欲[ほ]</kun><oku>しがれば</oku></b>"
            "、<kun> 呉[く]</kun><oku>れましょう</oku>",
            "furikanji split": "<b><kun> ほっ[欲]</kun><oku>すれば</oku></b>、<b><kun>"
            " ほ[欲]</kun><oku>しがれば</oku></b>"
            "、<kun> く[呉]</kun><oku>れましょう</oku>",
            "kana_only merged": "<b><kun>ほっ</kun><oku>すれば</oku></b>、<b><kun>ほ</kun>"
            "<oku>しがれば</oku></b>、<kun>く</kun><oku>れましょう</oku>",
            "furigana merged": "<b><kun> 欲[ほっ]</kun><oku>すれば</oku></b>、<b><kun> 欲[ほ]</kun><oku>"
            "しがれば</oku></b>、<kun> 呉[く]</kun><oku>れましょう</oku>",
            "furikanji merged": "<b><kun> ほっ[欲]</kun><oku>すれば</oku></b>、<b><kun> ほ[欲]</kun><oku>"
            "しがれば</oku></b>、<kun> く[呉]</kun><oku>れましょう</oku>",
        },
        id="matches single-kanji small tsu す verbs okuri /3",
    ),
    pytest.param(
        "強",
        "勉強[べんきょう]しません！",
        False,
        {
            "kana_only": "べん<b>きょう</b>しません！",
            "furigana": " 勉[べん]<b> 強[きょう]</b>しません！",
            "furikanji": " べん[勉]<b> きょう[強]</b>しません！",
            "kana_only split": "<on>べん</on><b><on>きょう</on></b><oku>しません</oku>！",
            "furigana split": "<on> 勉[べん]</on><b><on> 強[きょう]</on></b><oku>しません</oku>！",
            "furikanji split": "<on> べん[勉]</on><b><on> きょう[強]</on></b><oku>しません</oku>！",
            "kana_only merged": "<on>べん</on><b><on>きょう</on></b><oku>しません</oku>！",
            "furigana merged": "<on> 勉[べん]</on><b><on> 強[きょう]</on></b><oku>しません</oku>！",
            "furikanji merged": "<on> べん[勉]</on><b><on> きょう[強]</on></b><oku>しません</oku>！",
        },
        id="should not include suru okuri in multi-kanji suru verb highlight /1",
    ),
    pytest.param(
        "強",
        "勉強[べんきょう]していません！",
        False,
        {
            "kana_only": "べん<b>きょう</b>していません！",
            "furigana": " 勉[べん]<b> 強[きょう]</b>していません！",
            "furikanji": " べん[勉]<b> きょう[強]</b>していません！",
            "kana_only split": "<on>べん</on><b><on>きょう</on></b><oku>していません</oku>！",
            "furigana split": "<on> 勉[べん]</on><b><on> 強[きょう]</on></b><oku>していません</oku>！",
            "furikanji split": "<on> べん[勉]</on><b><on> きょう[強]</on></b><oku>していません</oku>！",
            "kana_only merged": "<on>べん</on><b><on>きょう</on></b><oku>していません</oku>！",
            "furigana merged": "<on> 勉[べん]</on><b><on> 強[きょう]</on></b><oku>していません</oku>！",
            "furikanji merged": "<on> べん[勉]</on><b><on> きょう[強]</on></b><oku>していません</oku>！",
        },
        id="should not include suru okuri in multi-kanji suru verb highlight /2",
    ),
    pytest.param(
        "",
        "勉強[べんきょう]できるかい？",
        False,
        {
            "kana_only": "べんきょうできるかい？",
            "furigana": " 勉強[べんきょう]できるかい？",
            "furikanji": " べんきょう[勉強]できるかい？",
            "kana_only split": "<on>べん</on><on>きょう</on>できるかい？",
            "furigana split": "<on> 勉[べん]</on><on> 強[きょう]</on>できるかい？",
            "furikanji split": "<on> べん[勉]</on><on> きょう[強]</on>できるかい？",
            "kana_only merged": "<on>べんきょう</on>できるかい？",
            "furigana merged": "<on> 勉強[べんきょう]</on>できるかい？",
            "furikanji merged": "<on> べんきょう[勉強]</on>できるかい？",
        },
        id="should not include できる okuri in suru verb okuri /1",
    ),
    pytest.param(
        "爺",
        "好々爺[こうこうや]です",
        True,
        {
            "kana_only": "コウコウ<b>ヤ</b>です",
            "furigana": " 好々[コウコウ]<b> 爺[ヤ]</b>です",
            "furikanji": " コウコウ[好々]<b> ヤ[爺]</b>です",
            "kana_only split": "<on>コウコウ</on><b><on>ヤ</on></b>です",
            "furigana split": "<on> 好々[コウコウ]</on><b><on> 爺[ヤ]</on></b>です",
            "furikanji split": "<on> コウコウ[好々]</on><b><on> ヤ[爺]</on></b>です",
            "kana_only merged": "<on>コウコウ</on><b><on>ヤ</on></b>です",
            "furigana merged": "<on> 好々[コウコウ]</on><b><on> 爺[ヤ]</on></b>です",
            "furikanji merged": "<on> コウコウ[好々]</on><b><on> ヤ[爺]</on></b>です",
        },
        id="Should not include です in okurigana",
    ),
    pytest.param(
        "",
        "有難[ありがと]う 御座[ござ]います",
        False,
        {
            "kana_only": "ありがとう ございます",
            "furigana": " 有難[ありがと]う 御座[ござ]います",
            "furikanji": " ありがと[有難]う ござ[御座]います",
            "kana_only split": "<kun>あり</kun><kun>がと</kun><oku>う</oku> <on>ご</on><on>ざ</on><oku>います</oku>",
            "furigana split": "<kun> 有[あり]</kun><kun> 難[がと]</kun><oku>う</oku><on> 御[ご]</on><on>"
            " 座[ざ]</on><oku>います</oku>",
            "furikanji split": "<kun> あり[有]</kun><kun> がと[難]</kun><oku>う</oku><on> ご[御]</on><on>"
            " ざ[座]</on><oku>います</oku>",
            "kana_only merged": "<kun>ありがと</kun><oku>う</oku> <on>ござ</on><oku>います</oku>",
            "furigana merged": "<kun> 有難[ありがと]</kun><oku>う</oku><on> 御座[ござ]</on><oku>います</oku>",
            "furikanji merged": "<kun> ありがと[有難]</kun><oku>う</oku><on> ござ[御座]</on><oku>います</oku>",
        },
        id="有難う should be all kunyomi",
    ),
    pytest.param(
        "",
        "僧ヶ岳[そうがだけ]",
        False,
        {
            "kana_only": "そうがだけ",
            "furigana": " 僧ヶ岳[そうがだけ]",
            "furikanji": " そうがだけ[僧ヶ岳]",
            "kana_only split": "<on>そう</on><on>が</on><kun>だけ</kun>",
            "furigana split": "<on> 僧[そう]</on><on> ヶ[が]</on><kun> 岳[だけ]</kun>",
            "furikanji split": "<on> そう[僧]</on><on> が[ヶ]</on><kun> だけ[岳]</kun>",
            "kana_only merged": "<on>そうが</on><kun>だけ</kun>",
            "furigana merged": "<on> 僧ヶ[そうが]</on><kun> 岳[だけ]</kun>",
            "furikanji merged": "<on> そうが[僧ヶ]</on><kun> だけ[岳]</kun>",
        },
        id="small ヶ should be processed as kanji - no highlight",
    ),
    pytest.param(
        "",
        "ヶ月[かげつ]",
        False,
        {
            "kana_only": "かげつ",
            "furigana": " ヶ月[かげつ]",
            "furikanji": " かげつ[ヶ月]",
            "kana_only split": "<on>か</on><on>げつ</on>",
            "furigana split": "<on> ヶ[か]</on><on> 月[げつ]</on>",
            "furikanji split": "<on> か[ヶ]</on><on> げつ[月]</on>",
            "kana_only merged": "<on>かげつ</on>",
            "furigana merged": "<on> ヶ月[かげつ]</on>",
            "furikanji merged": "<on> かげつ[ヶ月]</on>",
        },
        id="small ヶ should be processed as kanji - no highlight, start of word",
    ),
    pytest.param(
        "駒",
        "駒ヶ岳[こまがだけ]",
        False,
        {
            "kana_only": "<b>こま</b>がだけ",
            "furigana": "<b> 駒[こま]</b> ヶ岳[がだけ]",
            "furikanji": "<b> こま[駒]</b> がだけ[ヶ岳]",
            "kana_only split": "<b><kun>こま</kun></b><on>が</on><kun>だけ</kun>",
            "furigana split": "<b><kun> 駒[こま]</kun></b><on> ヶ[が]</on><kun> 岳[だけ]</kun>",
            "furikanji split": "<b><kun> こま[駒]</kun></b><on> が[ヶ]</on><kun> だけ[岳]</kun>",
            "kana_only merged": "<b><kun>こま</kun></b><on>が</on><kun>だけ</kun>",
            "furigana merged": "<b><kun> 駒[こま]</kun></b><on> ヶ[が]</on><kun> 岳[だけ]</kun>",
            "furikanji merged": "<b><kun> こま[駒]</kun></b><on> が[ヶ]</on><kun> だけ[岳]</kun>",
        },
        id="small ケ should be processed as kanji - with highlight",
    ),
    pytest.param(
        "",
        "１ヶ所[いっかしょ]",
        False,
        {
            "kana_only": "いっかしょ",
            "furigana": " １ヶ所[いっかしょ]",
            "furikanji": " いっかしょ[１ヶ所]",
            "kana_only split": "<on>いっ</on><on>か</on><on>しょ</on>",
            "furigana split": "<on> １[いっ]</on><on> ヶ[か]</on><on> 所[しょ]</on>",
            "furikanji split": "<on> いっ[１]</on><on> か[ヶ]</on><on> しょ[所]</on>",
            "kana_only merged": "<on>いっかしょ</on>",
            "furigana merged": "<on> １ヶ所[いっかしょ]</on>",
            "furikanji merged": "<on> いっかしょ[１ヶ所]</on>",
        },
        id="small ケ should be processed as kanji - with number and no highlight",
    ),
    pytest.param(
        "一",
        "１ヶ所[いっかしょ]",
        False,
        {
            "kana_only": "<b>いっ</b>かしょ",
            "furigana": "<b> １[いっ]</b> ヶ所[かしょ]",
            "furikanji": "<b> いっ[１]</b> かしょ[ヶ所]",
            "kana_only split": "<b><on>いっ</on></b><on>か</on><on>しょ</on>",
            "furigana split": "<b><on> １[いっ]</on></b><on> ヶ[か]</on><on> 所[しょ]</on>",
            "furikanji split": "<b><on> いっ[１]</on></b><on> か[ヶ]</on><on> しょ[所]</on>",
            "kana_only merged": "<b><on>いっ</on></b><on>かしょ</on>",
            "furigana merged": "<b><on> １[いっ]</on></b><on> ヶ所[かしょ]</on>",
            "furikanji merged": "<b><on> いっ[１]</on></b><on> かしょ[ヶ所]</on>",
        },
        id="small ケ should be processed as kanji - with number and highlight",
    ),
    pytest.param(
        "月",
        "三ヵ月[みっかげつ]",
        False,
        {
            "kana_only": "みっか<b>げつ</b>",
            "furigana": " 三ヵ[みっか]<b> 月[げつ]</b>",
            "furikanji": " みっか[三ヵ]<b> げつ[月]</b>",
            "kana_only split": "<kun>みっ</kun><on>か</on><b><on>げつ</on></b>",
            "furigana split": "<kun> 三[みっ]</kun><on> ヵ[か]</on><b><on> 月[げつ]</on></b>",
            "furikanji split": "<kun> みっ[三]</kun><on> か[ヵ]</on><b><on> げつ[月]</on></b>",
            "kana_only merged": "<kun>みっ</kun><on>か</on><b><on>げつ</on></b>",
            "furigana merged": "<kun> 三[みっ]</kun><on> ヵ[か]</on><b><on> 月[げつ]</on></b>",
            "furikanji merged": "<kun> みっ[三]</kun><on> か[ヵ]</on><b><on> げつ[月]</on></b>",
        },
        id="small カ should be processed as kanji - with highlight",
    ),
    # Kana that carry no reading of their own - a leading っ, a small vowel on its own, an
    # iteration mark - are taken out of the way before the reading is matched and written back
    # afterwards. Every case below asserts that the furigana comes back out with the characters it
    # went in with, and the tag says whether taking them out let the reading be recognised.
    pytest.param(
        "",
        "振[っぷり]",
        True,
        {
            "furigana": " 振[っぷり]",
            "furigana split": "<kun> 振[っぷり]</kun>",
            "furigana merged": "<kun> 振[っぷり]</kun>",
            "furikanji": " っぷり[振]",
            "furikanji split": "<kun> っぷり[振]</kun>",
            "furikanji merged": "<kun> っぷり[振]</kun>",
            "kana_only": "っぷり",
            "kana_only split": "<kun>っぷり</kun>",
            "kana_only merged": "<kun>っぷり</kun>",
        },
        id="furigana starting with small tsu - no highlight",
    ),
    pytest.param(
        "振",
        "振[っぷり]",
        True,
        {
            "furigana": "<b> 振[っぷり]</b>",
            "furigana split": "<b><kun> 振[っぷり]</kun></b>",
            "furigana merged": "<b><kun> 振[っぷり]</kun></b>",
            "furikanji": "<b> っぷり[振]</b>",
            "furikanji split": "<b><kun> っぷり[振]</kun></b>",
            "furikanji merged": "<b><kun> っぷり[振]</kun></b>",
            "kana_only": "<b>っぷり</b>",
            "kana_only split": "<b><kun>っぷり</kun></b>",
            "kana_only merged": "<b><kun>っぷり</kun></b>",
        },
        id="furigana starting with small tsu - with highlight",
    ),
    pytest.param(
        "",
        "全[った]く",
        True,
        {
            "furigana": " 全[った]く",
            "furigana split": "<juk> 全[った]</juk>く",
            "furigana merged": "<juk> 全[った]</juk>く",
            "furikanji": " った[全]く",
            "furikanji split": "<juk> った[全]</juk>く",
            "furikanji merged": "<juk> った[全]</juk>く",
            "kana_only": "ったく",
            "kana_only split": "<juk>った</juk>く",
            "kana_only merged": "<juk>った</juk>く",
        },
        id="furigana starting with small tsu, with okurigana",
    ),
    pytest.param(
        "",
        "丈[ったけ]",
        True,
        {
            "furigana": " 丈[ったけ]",
            "furigana split": "<kun> 丈[ったけ]</kun>",
            "furigana merged": "<kun> 丈[ったけ]</kun>",
            "furikanji": " ったけ[丈]",
            "furikanji split": "<kun> ったけ[丈]</kun>",
            "furikanji merged": "<kun> ったけ[丈]</kun>",
            "kana_only": "ったけ",
            "kana_only split": "<kun>ったけ</kun>",
            "kana_only merged": "<kun>ったけ</kun>",
        },
        id="furigana starting with small tsu, three mora",
    ),
    pytest.param(
        "",
        "煩[うるせぇ]",
        True,
        {
            "furigana": " 煩[うるせぇ]",
            "furigana split": "<juk> 煩[うるせぇ]</juk>",
            "furigana merged": "<juk> 煩[うるせぇ]</juk>",
            "furikanji": " うるせぇ[煩]",
            "furikanji split": "<juk> うるせぇ[煩]</juk>",
            "furikanji merged": "<juk> うるせぇ[煩]</juk>",
            "kana_only": "うるせぇ",
            "kana_only split": "<juk>うるせぇ</juk>",
            "kana_only merged": "<juk>うるせぇ</juk>",
        },
        id="furigana ending in a small vowel",
    ),
    pytest.param(
        # The small vowel is only folded into the mora before it when there are mora to spare,
        # so both kanji here still get one rather than 呼 being left with empty furigana
        "",
        "嗚呼[あぁ]",
        True,
        {
            "furigana": " 嗚呼[あぁ]",
            "furigana split": "<juk> 嗚[あ]</juk><juk> 呼[ぁ]</juk>",
            "furigana merged": "<juk> 嗚呼[あぁ]</juk>",
            "furikanji": " あぁ[嗚呼]",
            "furikanji split": "<juk> あ[嗚]</juk><juk> ぁ[呼]</juk>",
            "furikanji merged": "<juk> あぁ[嗚呼]</juk>",
            "kana_only": "あぁ",
            "kana_only split": "<juk>あ</juk><juk>ぁ</juk>",
            "kana_only merged": "<juk>あぁ</juk>",
        },
        id="furigana ending in a small vowel, one mora per kanji",
    ),
    pytest.param(
        "",
        "儘[まゝ]",
        True,
        {
            "furigana": " 儘[まゝ]",
            "furigana split": "<kun> 儘[まゝ]</kun>",
            "furigana merged": "<kun> 儘[まゝ]</kun>",
            "furikanji": " まゝ[儘]",
            "furikanji split": "<kun> まゝ[儘]</kun>",
            "furikanji merged": "<kun> まゝ[儘]</kun>",
            "kana_only": "まゝ",
            "kana_only split": "<kun>まゝ</kun>",
            "kana_only merged": "<kun>まゝ</kun>",
        },
        id="furigana with a hiragana iteration mark",
    ),
    pytest.param(
        "",
        "儘[マヽ]",
        True,
        {
            "furigana": " 儘[マヽ]",
            "furigana split": "<kun> 儘[マヽ]</kun>",
            "furigana merged": "<kun> 儘[マヽ]</kun>",
            "furikanji": " マヽ[儘]",
            "furikanji split": "<kun> マヽ[儘]</kun>",
            "furikanji merged": "<kun> マヽ[儘]</kun>",
            "kana_only": "マヽ",
            "kana_only split": "<kun>マヽ</kun>",
            "kana_only merged": "<kun>マヽ</kun>",
        },
        id="furigana with a katakana iteration mark",
    ),
    pytest.param(
        "",
        "続[つゞ]く",
        True,
        {
            "furigana": " 続[つゞ]く",
            "furigana split": "<kun> 続[つゞ]</kun><oku>く</oku>",
            "furigana merged": "<kun> 続[つゞ]</kun><oku>く</oku>",
            "furikanji": " つゞ[続]く",
            "furikanji split": "<kun> つゞ[続]</kun><oku>く</oku>",
            "furikanji merged": "<kun> つゞ[続]</kun><oku>く</oku>",
            "kana_only": "つゞく",
            "kana_only split": "<kun>つゞ</kun><oku>く</oku>",
            "kana_only merged": "<kun>つゞ</kun><oku>く</oku>",
        },
        id="furigana with a voiced iteration mark",
    ),
    pytest.param(
        "",
        "続[ツヾ]く",
        True,
        {
            "furigana": " 続[ツヾ]く",
            "furigana split": "<kun> 続[ツヾ]</kun><oku>く</oku>",
            "furigana merged": "<kun> 続[ツヾ]</kun><oku>く</oku>",
            "furikanji": " ツヾ[続]く",
            "furikanji split": "<kun> ツヾ[続]</kun><oku>く</oku>",
            "furikanji merged": "<kun> ツヾ[続]</kun><oku>く</oku>",
            "kana_only": "ツヾく",
            "kana_only split": "<kun>ツヾ</kun><oku>く</oku>",
            "kana_only merged": "<kun>ツヾ</kun><oku>く</oku>",
        },
        id="furigana with a voiced katakana iteration mark",
    ),
    pytest.param(
        # The ゃ of きゃ belongs to that mora, so it is not one of the lone small kana that get
        # rewritten, and neither is the っ that ends a mora rather than starting the reading
        "",
        "却[きゃっ]て",
        True,
        {
            "furigana": " 却[キャッ]て",
            "furigana split": "<on> 却[キャッ]</on>て",
            "furigana merged": "<on> 却[キャッ]</on>て",
            "furikanji": " キャッ[却]て",
            "furikanji split": "<on> キャッ[却]</on>て",
            "furikanji merged": "<on> キャッ[却]</on>て",
            "kana_only": "キャッて",
            "kana_only split": "<on>キャッ</on>て",
            "kana_only merged": "<on>キャッ</on>て",
        },
        id="small kana of a palatalized mora is not a lone one",
    ),
]


# A mode id that is not one of MODES' would otherwise make the case quietly skip that mode
# instead of asserting it, so a typo in a key is caught here, at collection.
_MODE_IDS = {mode.values[0] for mode in MODES}
for _case in CASES:
    _expected = _case.values[3]
    assert isinstance(_expected, dict), f"{_case.id}: the fourth value is not a dict"
    _unknown = sorted(set(_expected) - _MODE_IDS)
    assert not _unknown, f"{_case.id}: expectations for modes that do not exist: {_unknown}"


@pytest.mark.parametrize("mode, return_type, with_tags, merge_consecutive", MODES)
@pytest.mark.parametrize("kanji, sentence, onyomi_to_katakana, expected", CASES)
def test_kana_highlight(
    kanji: str | None,
    sentence: str,
    onyomi_to_katakana: bool,
    expected: dict[str, str],
    mode: str,
    return_type: FuriReconstruct,
    with_tags: bool,
    merge_consecutive: bool,
):
    if mode not in expected:
        pytest.skip(f"the case asserts no {mode} output")
    with_tags_def = WithTagsDef(with_tags, merge_consecutive, onyomi_to_katakana, False)
    assert kana_highlight(kanji, sentence, return_type, with_tags_def) == expected[mode]


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
