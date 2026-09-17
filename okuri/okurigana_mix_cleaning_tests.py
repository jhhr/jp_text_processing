import re
import sys

from .okurigana_mix_cleaning_replacer import (
    LEADING_KANA_CLEANING_REC,
    OKURIGANA_MIX_CLEANING_REC,
    leading_kana_cleaning_replacer,
    okurigana_mix_cleaning_replacer,
)

from ..kana.make_furigana_from_reading import make_furigana_from_reading
from ..mecab_controller.kana_conv import to_hiragana


RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

failed_tests: list[str] = []

TAG_RE = re.compile(r"<[^>]+>")
GROUP_RE = re.compile(r" ?([^ \[\]<>]+?)\[([^\]]*)\]")


def clean(text: str) -> str:
    """Both cleaning passes, in the order kana_highlight runs them."""
    text = LEADING_KANA_CLEANING_REC.sub(leading_kana_cleaning_replacer, text)
    return OKURIGANA_MIX_CLEANING_REC.sub(okurigana_mix_cleaning_replacer, text)


def check(test_name: str, result, expected):
    try:
        assert result == expected
    except AssertionError:
        failed_tests.append(test_name)
        print(
            f"""{RED}{test_name}
{YELLOW}Expected: {expected!r}
{GREEN}Got:      {result!r}
{RESET}"""
        )


def test(test_name: str, text: str, expected: str):
    """The cleaning passes turn `text` into `expected`."""
    check(test_name, clean(text), expected)


def test_reads_back(test_name: str, word: str, reading: str):
    """Whatever furigana the word gets, dropping the readings has to give the word back and
    keeping them has to give the reading back. This is the property the whole pipeline owes
    its callers: match_words_to_notes writes the result into a note's vocab-furigana."""
    furigana = make_furigana_from_reading(word, reading)
    plain = TAG_RE.sub("", furigana)
    got_word = GROUP_RE.sub(lambda m: m[1], plain).replace(" ", "")
    # A word keeps its own kana as it writes them, so スペイン語 reads back as スペインご.
    got_reading = to_hiragana(GROUP_RE.sub(lambda m: m[2], plain).replace(" ", ""))
    check(f"{test_name} ({furigana})", (got_word, got_reading), (word, to_hiragana(reading)))


def main():
    # --- the shapes the module has always handled ------------------------------------------
    test(
        test_name="okurigana between two kanji",
        text="消え去[きえさ]る",
        expected="消[き]え去[さ]る",
    )
    test(
        test_name="okurigana between two kanji and after the second",
        text="隣り合わせ[となりあわせ]",
        expected="隣[とな]り合[あ]わせ",
    )
    test(
        test_name="okurigana only at the end",
        text="歯止め[はどめ]",
        expected="歯止[はど]め",
    )

    # --- a word that opens with kana, with okurigana in the middle too ---------------------
    # Taking the match from the kanji alone left the opening kana outside the group, where it
    # spelled itself a second time: すり下ろす[すりおろす] became すり 下[すりお]ろす.
    test(
        test_name="opening kana is not handed to the kanji",
        text="すり下ろす[すりおろす]",
        expected="すり下[お]ろす",
    )
    test(
        test_name="opening kana before a kanji with long okurigana",
        text="かも知れない[かもしれない]",
        expected="かも知[し]れない",
    )
    test(
        test_name="opening kana of more than one mora",
        text="にも拘らず[にもかかわらず]",
        expected="にも拘[かかわ]らず",
    )
    test(
        test_name="opening kana before a two kanji reading",
        text="か如何か[かどうか]",
        expected="か如何[どう]か",
    )
    test(
        test_name="opening kana with two kanji runs after it",
        text="お問い合わせ[おといあわせ]",
        expected="お問[と]い合[あ]わせ",
    )

    # --- a word that opens with kana and has no okurigana before the bracket ---------------
    test(
        test_name="honorific prefix is not handed to the kanji",
        text="お前[おまえ]",
        expected="お前[まえ]",
    )
    test(
        test_name="opening kana before a compound",
        text="いい加減[いいかげん]",
        expected="いい加減[かげん]",
    )
    test(
        test_name="a whole phrase of opening kana",
        text="いざという時[いざというとき]",
        expected="いざという時[とき]",
    )
    test(
        test_name="katakana opening a word whose reading is hiragana",
        text="スペイン語[すぺいんご]",
        expected="スペイン語[ご]",
    )
    test(
        test_name="katakana opening a word whose kanji takes rendaku",
        text="ゴミ箱[ごみばこ]",
        expected="ゴミ箱[ばこ]",
    )

    # --- the okurigana also occurs inside the reading --------------------------------------
    # The okurigana is the kana *after* the kanji, so it is the last place that run can sit in
    # the reading. Taking the first い of もったいない split 勿体無い into 勿体無[もった]い[ない],
    # and the reading left over became a bracket with no word in front of it.
    test(
        test_name="okurigana that also occurs inside the reading",
        text="勿体無い[もったいない]",
        expected="勿体無[もったいな]い",
    )
    test(
        test_name="okurigana occurring twice in a short reading",
        text="無理遣り[むりやり]",
        expected="無理遣[むりや]り",
    )
    test(
        test_name="okurigana whose kana ends the reading as well",
        text="羽搏く[はばたく]",
        expected="羽搏[はばた]く",
    )

    # --- a second kanji still gets a reading of its own ------------------------------------
    # The greedy first reading must not swallow the lot: 行き来[いきき] became 行[いき]き来[].
    test(
        test_name="second kanji keeps a reading",
        text="行き来[いきき]",
        expected="行[い]き来[き]",
    )
    test(
        test_name="second kanji keeps a reading when the okurigana repeats",
        text="其の物[そのもの]",
        expected="其[そ]の物[もの]",
    )
    test(
        test_name="second kanji keeps a reading with rendaku",
        text="包み紙[つつみがみ]",
        expected="包[つつ]み紙[がみ]",
    )
    test(
        test_name="opening kana and a second kanji together",
        text="良い塩梅[いいあんばい]",
        expected="良[い]い塩梅[あんばい]",
    )

    # --- left alone -------------------------------------------------------------------------
    test(
        test_name="a reading that omits the word's honorific is not raided",
        text="お金[かね]",
        expected="お金[かね]",
    )
    test(
        test_name="a particle before a word is not taken for part of it",
        text=" 私[わたし]は 元気[げんき]です",
        expected=" 私[わたし]は 元気[げんき]です",
    )
    # A particle at the start of the text, of a line or after a tag has no space in front of it
    # to mark where the word begins, so only the kanji's readings tell it from a prefix. Taking
    # its kana cost the word its first mora: か家族[かぞく] became か家族[ぞく], leaving 家 unread.
    test(
        test_name="a particle opening the text is not taken for part of the word",
        text="か家族[かぞく]と",
        expected="か家族[かぞく]と",
    )
    test(
        test_name="a particle opening the text whose kanji takes a sound change",
        text="が学校[がっこう]に",
        expected="が学校[がっこう]に",
    )
    test(
        test_name="a particle opening the text before a jukujikun word",
        text="も紅葉[もみじ]が",
        expected="も紅葉[もみじ]が",
    )
    # The honorific is still given back when the kanji can account for neither spelling: 土産
    # reads みやげ as jukujikun either way, so the prefix itself has to decide.
    test(
        test_name="honorific prefix before a jukujikun word",
        text="お土産[おみやげ]",
        expected="お土産[みやげ]",
    )
    # A reading that spells a particle out belongs to the particle, not to the kanji.
    test(
        test_name="a particle spelled out in the reading is given back",
        text="と時間[とじかん]",
        expected="と時間[じかん]",
    )
    test(
        test_name="an already cleaned word is not cleaned again",
        text="消[き]え去[さ]る",
        expected="消[き]え去[さ]る",
    )

    # --- the property all of it exists to keep ----------------------------------------------
    for word, reading in [
        ("気持ち", "きもち"),
        ("見付ける", "みつける"),
        ("其の儘", "そのまま"),
        ("すり下ろす", "すりおろす"),
        ("かも知れない", "かもしれない"),
        ("にも拘らず", "にもかかわらず"),
        ("か如何か", "かどうか"),
        ("お問い合わせ", "おといあわせ"),
        ("お前", "おまえ"),
        ("いい加減", "いいかげん"),
        ("いざという時", "いざというとき"),
        ("スペイン語", "すぺいんご"),
        ("ゴミ箱", "ごみばこ"),
        ("勿体無い", "もったいない"),
        ("無理遣り", "むりやり"),
        ("羽搏く", "はばたく"),
        ("行き来", "いきき"),
        ("其の物", "そのもの"),
        ("包み紙", "つつみがみ"),
        ("良い塩梅", "いいあんばい"),
        ("土産", "みやげ"),
        ("紅葉", "もみじ"),
    ]:
        test_reads_back(f"{word} reads back", word, reading)

    if failed_tests:
        print(f"{RED}{len(failed_tests)} tests failed{RESET}")
        sys.exit(1)
    print(f"\n{GREEN}All tests passed{RESET}")


if __name__ == "__main__":
    main()
