"""Cases for the two cleaning passes `kana_highlight` runs over mixed okurigana furigana, with
pytest from `anki_shared/`:

    python -m pytest jp_text_processing/okuri/okurigana_mix_cleaning_tests.py

Pass `--log-cli-level=debug` to see what the passes logged for a case; pytest captures the
package logger on its own, so nothing here has to turn logging on.

A case that is known to fail gets `marks=pytest.mark.xfail(reason="...", strict=True)` in its
`pytest.param`: strict so an unexpected pass fails the run and the reason gets dropped. None
of the cases below need it today.
"""

import logging
import re

import pytest

from ..kana.make_furigana_from_reading import make_furigana_from_reading
from ..mecab_controller.kana_conv import to_hiragana
from ..utils.logger import LOGGER_NAME
from .okurigana_mix_cleaning_replacer import (
    LEADING_KANA_CLEANING_REC,
    OKURIGANA_MIX_CLEANING_REC,
    leading_kana_cleaning_replacer,
    okurigana_mix_cleaning_replacer,
    unread_kanji_count,
)

TAG_RE = re.compile(r"<[^>]+>")
GROUP_RE = re.compile(r" ?([^ \[\]<>]+?)\[([^\]]*)\]")


def clean(text: str) -> str:
    """Both cleaning passes, in the order kana_highlight runs them."""
    text = LEADING_KANA_CLEANING_REC.sub(leading_kana_cleaning_replacer, text)
    return OKURIGANA_MIX_CLEANING_REC.sub(okurigana_mix_cleaning_replacer, text)


CASES = [
    # --- the shapes the module has always handled ------------------------------------------
    pytest.param("消え去[きえさ]る", "消[き]え去[さ]る", id="okurigana between two kanji"),
    pytest.param(
        "隣り合わせ[となりあわせ]",
        "隣[とな]り合[あ]わせ",
        id="okurigana between two kanji and after the second",
    ),
    pytest.param("歯止め[はどめ]", "歯止[はど]め", id="okurigana only at the end"),
    # --- a word that opens with kana, with okurigana in the middle too ---------------------
    # Taking the match from the kanji alone left the opening kana outside the group, where it
    # spelled itself a second time: すり下ろす[すりおろす] became すり 下[すりお]ろす.
    pytest.param(
        "すり下ろす[すりおろす]", "すり下[お]ろす", id="opening kana is not handed to the kanji"
    ),
    pytest.param(
        "かも知れない[かもしれない]",
        "かも知[し]れない",
        id="opening kana before a kanji with long okurigana",
    ),
    pytest.param(
        "にも拘らず[にもかかわらず]",
        "にも拘[かかわ]らず",
        id="opening kana of more than one mora",
    ),
    pytest.param(
        "か如何か[かどうか]", "か如何[どう]か", id="opening kana before a two kanji reading"
    ),
    pytest.param(
        "お問い合わせ[おといあわせ]",
        "お問[と]い合[あ]わせ",
        id="opening kana with two kanji runs after it",
    ),
    # --- a word that opens with kana and has no okurigana before the bracket ---------------
    pytest.param("お前[おまえ]", "お前[まえ]", id="honorific prefix is not handed to the kanji"),
    pytest.param("いい加減[いいかげん]", "いい加減[かげん]", id="opening kana before a compound"),
    pytest.param(
        "いざという時[いざというとき]",
        "いざという時[とき]",
        id="a whole phrase of opening kana",
    ),
    pytest.param(
        "スペイン語[すぺいんご]",
        "スペイン語[ご]",
        id="katakana opening a word whose reading is hiragana",
    ),
    pytest.param(
        "ゴミ箱[ごみばこ]",
        "ゴミ箱[ばこ]",
        id="katakana opening a word whose kanji takes rendaku",
    ),
    # --- the okurigana also occurs inside the reading --------------------------------------
    # The okurigana is the kana *after* the kanji, so it is the last place that run can sit in
    # the reading. Taking the first い of もったいない split 勿体無い into 勿体無[もった]い[ない],
    # and the reading left over became a bracket with no word in front of it.
    pytest.param(
        "勿体無い[もったいない]",
        "勿体無[もったいな]い",
        id="okurigana that also occurs inside the reading",
    ),
    pytest.param(
        "無理遣り[むりやり]",
        "無理遣[むりや]り",
        id="okurigana occurring twice in a short reading",
    ),
    pytest.param(
        "羽搏く[はばたく]",
        "羽搏[はばた]く",
        id="okurigana whose kana ends the reading as well",
    ),
    # --- a second kanji still gets a reading of its own ------------------------------------
    # The greedy first reading must not swallow the lot: 行き来[いきき] became 行[いき]き来[].
    pytest.param("行き来[いきき]", "行[い]き来[き]", id="second kanji keeps a reading"),
    pytest.param(
        "其の物[そのもの]",
        "其[そ]の物[もの]",
        id="second kanji keeps a reading when the okurigana repeats",
    ),
    pytest.param(
        "包み紙[つつみがみ]",
        "包[つつ]み紙[がみ]",
        id="second kanji keeps a reading with rendaku",
    ),
    pytest.param(
        "良い塩梅[いいあんばい]",
        "良[い]い塩梅[あんばい]",
        id="opening kana and a second kanji together",
    ),
    # --- left alone -------------------------------------------------------------------------
    pytest.param(
        "お金[かね]", "お金[かね]", id="a reading that omits the word's honorific is not raided"
    ),
    pytest.param(
        " 私[わたし]は 元気[げんき]です",
        " 私[わたし]は 元気[げんき]です",
        id="a particle before a word is not taken for part of it",
    ),
    # A particle at the start of the text, of a line or after a tag has no space in front of it
    # to mark where the word begins, so only the kanji's readings tell it from a prefix. Taking
    # its kana cost the word its first mora: か家族[かぞく] became か家族[ぞく], leaving 家 unread.
    pytest.param(
        "か家族[かぞく]と",
        "か家族[かぞく]と",
        id="a particle opening the text is not taken for part of the word",
    ),
    pytest.param(
        "が学校[がっこう]に",
        "が学校[がっこう]に",
        id="a particle opening the text whose kanji takes a sound change",
    ),
    pytest.param(
        "も紅葉[もみじ]が",
        "も紅葉[もみじ]が",
        id="a particle opening the text before a jukujikun word",
    ),
    # The honorific is still given back when the kanji can account for neither spelling: 土産
    # reads みやげ as jukujikun either way, so the prefix itself has to decide.
    pytest.param("お土産[おみやげ]", "お土産[みやげ]", id="honorific prefix before a jukujikun word"),
    # A reading that spells a particle out belongs to the particle, not to the kanji.
    pytest.param(
        "と時間[とじかん]",
        "と時間[じかん]",
        id="a particle spelled out in the reading is given back",
    ),
    pytest.param(
        "消[き]え去[さ]る", "消[き]え去[さ]る", id="an already cleaned word is not cleaned again"
    ),
    # --- more than one word in the text -----------------------------------------------------
    # A reading stops at its own bracket. As `.+` the greedy first reading ran on past the `]`
    # and stopped at the last place in the whole text where the okurigana sat in front of one,
    # so 見え[みえ] took everything up to 消え[きえ]'s bracket for its reading and left 消え
    # rewritten into a form nothing reads as furigana any more.
    pytest.param(
        "彼は 見え[みえ]ない 所[ところ]で 消え[きえ]た",
        "彼は 見[み]えない 所[ところ]で 消[き]えた",
        id="two words whose okurigana is the same kana",
    ),
    pytest.param(
        "これは 上げ[あげ]て 下げ[さげ]る",
        "これは 上[あ]げて 下[さ]げる",
        id="two words whose okurigana and reading share a kana",
    ),
    pytest.param(
        "食べ[たべ]たい 食べ[たべ]る", "食[た]べたい 食[た]べる", id="the same word twice in one text"
    ),
    # A line start marks where a word begins just as a space does. Fields written in the HTML
    # editor break their lines with <br>, but fields pasted or imported as plain text carry \n,
    # and the first word of every line after the first used to be left uncleaned.
    pytest.param(
        "行[い]く\n食べ[たべ]る", "行[い]く\n食[た]べる", id="a word opening a line is a word start"
    ),
    pytest.param(
        "行[い]く\nお前[おまえ]",
        "行[い]く\nお前[まえ]",
        id="opening kana of a word opening a line",
    ),
    # --- whole sentences ---------------------------------------------------------------------
    # What the passes get from a card: several words in one text, kept apart by a space, a <br>
    # or a newline, one of them opening the text and one following a tag.
    pytest.param(
        "勿体無い[もったいない] 行き来[いきき]",
        "勿体無[もったいな]い 行[い]き来[き]",
        id="the greedy reading and the second reading in one text",
    ),
    pytest.param(
        "見え[みえ]た<br>消え[きえ]た",
        "見[み]えた<br>消[き]えた",
        id="words sharing okurigana across a line break",
    ),
    pytest.param(
        "<b>上げ[あげ]</b>て 下げ[さげ]る",
        "<b>上[あ]げ</b>て 下[さ]げる",
        id="a word right after a tag, with another after it",
    ),
    pytest.param(
        "すり下ろす[すりおろす]\nかも知れない[かもしれない]",
        "すり下[お]ろす\nかも知[し]れない",
        id="two words opening with kana, the second opening a line",
    ),
    pytest.param(
        "隣り合わせ[となりあわせ]の 歯止め[はどめ]",
        "隣[とな]り合[あ]わせの 歯止[はど]め",
        id="two kanji runs in the first word, one in the second",
    ),
    pytest.param(
        "朝[あさ] 起き[おき]て<br>夜[よる] 寝る[ねる]",
        "朝[あさ] 起[お]きて<br>夜[よる] 寝[ね]る",
        id="a sentence of words with and without okurigana",
    ),
]


@pytest.mark.parametrize("text, expected", CASES)
def test_okurigana_mix_cleaning(text: str, expected: str):
    """The cleaning passes turn `text` into `expected`."""
    assert clean(text) == expected


# The probe behind the leading-kana decision keeps its complaints to itself.
# 土産/みやげ reaches the godan-ending lookup, which used to log on the package logger because
# its caller never took the silent one; 紅葉/もみじ stops before it and was quiet either way.
PROBE_CASES = [
    pytest.param("土産", "みやげ", id="土産 probe is silent"),
    pytest.param("紅葉", "もみじ", id="紅葉 probe is silent"),
]


@pytest.mark.parametrize("kanji, furigana", PROBE_CASES)
def test_probe_says_nothing(kanji: str, furigana: str, caplog: pytest.LogCaptureFixture):
    """The alignment `unread_kanji_count` asks for is expected to fail - it is probing a reading
    the writer may not have meant - so none of what that attempt logs is the caller's business.
    Silencing it one call signature at a time used to leak whatever a function further down was
    called without the silent logger."""
    with caplog.at_level(logging.DEBUG, logger=LOGGER_NAME):
        unread_kanji_count(kanji, furigana)
    assert [r.getMessage() for r in caplog.records if r.name.startswith(LOGGER_NAME)] == []


# --- the property all of it exists to keep ----------------------------------------------
READS_BACK_CASES = [
    pytest.param("気持ち", "きもち", id="気持ち reads back"),
    pytest.param("見付ける", "みつける", id="見付ける reads back"),
    pytest.param("其の儘", "そのまま", id="其の儘 reads back"),
    pytest.param("すり下ろす", "すりおろす", id="すり下ろす reads back"),
    pytest.param("かも知れない", "かもしれない", id="かも知れない reads back"),
    pytest.param("にも拘らず", "にもかかわらず", id="にも拘らず reads back"),
    pytest.param("か如何か", "かどうか", id="か如何か reads back"),
    pytest.param("お問い合わせ", "おといあわせ", id="お問い合わせ reads back"),
    pytest.param("お前", "おまえ", id="お前 reads back"),
    pytest.param("いい加減", "いいかげん", id="いい加減 reads back"),
    pytest.param("いざという時", "いざというとき", id="いざという時 reads back"),
    pytest.param("スペイン語", "すぺいんご", id="スペイン語 reads back"),
    pytest.param("ゴミ箱", "ごみばこ", id="ゴミ箱 reads back"),
    pytest.param("勿体無い", "もったいない", id="勿体無い reads back"),
    pytest.param("無理遣り", "むりやり", id="無理遣り reads back"),
    pytest.param("羽搏く", "はばたく", id="羽搏く reads back"),
    pytest.param("行き来", "いきき", id="行き来 reads back"),
    pytest.param("其の物", "そのもの", id="其の物 reads back"),
    pytest.param("包み紙", "つつみがみ", id="包み紙 reads back"),
    pytest.param("良い塩梅", "いいあんばい", id="良い塩梅 reads back"),
    pytest.param("土産", "みやげ", id="土産 reads back"),
    pytest.param("紅葉", "もみじ", id="紅葉 reads back"),
]


@pytest.mark.parametrize("word, reading", READS_BACK_CASES)
def test_reads_back(word: str, reading: str):
    """Whatever furigana the word gets, dropping the readings has to give the word back and
    keeping them has to give the reading back. This is the property the whole pipeline owes
    its callers: match_words_to_notes writes the result into a note's vocab-furigana."""
    furigana = make_furigana_from_reading(word, reading)
    plain = TAG_RE.sub("", furigana)
    got_word = GROUP_RE.sub(lambda m: m[1], plain).replace(" ", "")
    # A word keeps its own kana as it writes them, so スペイン語 reads back as スペインご.
    got_reading = to_hiragana(GROUP_RE.sub(lambda m: m[2], plain).replace(" ", ""))
    assert (got_word, got_reading) == (word, to_hiragana(reading)), furigana


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
