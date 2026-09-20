import re

from ..kana.mora_alignment import find_first_complete_alignment
from ..kana.mora_splitter import split_to_mora_list
from ..mecab_controller.kana_conv import to_hiragana
from ..regex.kanji_furi import KANJI_CHAR_RE
from ..utils.logger import package_logger as logger
from ..utils.logger import silenced

# The characters that can sit in front of a word without being part of it, so that a word
# following one of them still counts as starting there. Besides whitespace and a tag's `>` those
# are another word's closing `]` and punctuation: ASCII punctuation, the CJK symbols and
# punctuation block 。、「」『』【】〜, the fullwidth forms of the ASCII punctuation ！？（）：；, and ….
# Left out of it are the characters a word is written with: 々, 〆 and 〇 sit in the CJK block and
# the fullwidth digits and letters sit among the fullwidth forms. Used in a negated lookbehind,
# which also lets the match start where the text or a line does.
WORD_START_PRECEDERS = (
    r"\s>"  # whitespace, a line break and a tag's end
    r"\]"  # another word's furigana bracket, the ASCII punctuation below covering it too
    r"!-/:-@\[-`{-~"  # ASCII punctuation
    "\u2026"  # …
    "\u3000-\u3004\u3008-\u303f"  # CJK symbols and punctuation, without 々 〆 〇
    "\uff01-\uff0f\uff1a-\uff20\uff3b-\uff40\uff5b-\uff60"  # the same punctuation, fullwidth
)

# Regex for a word that opens with kana and then has nothing but kanji before its furigana, so
# that the kana it opens with can be taken out of the reading. For example
# (a) お前[おまえ]
# (b) いい加減[いいかげん]
# (c) いざという時[いざというとき]
# (d) スペイン語[すぺいんご]   - the word's kana is katakana, the reading's is hiragana
#
# The match only starts where the word itself does, so that a particle mid-sentence is never
# mistaken for part of the word after it. At the start of the text, of a line or after a tag
# there is no such boundary to go by, so the replacer decides those by the reading; see it for
# why a prefix test on its own is not enough.
LEADING_KANA_CLEANING_REC = re.compile(
    rf"""
(?<![^{WORD_START_PRECEDERS}])  # the word's own start: the text's, a line's, or one after
                                # a space, a tag, a bracket or punctuation
(?P<pre>[ぁ-んァ-ヶー]+)          # the kana the word opens with   (a)お (b)いい (d)スペイン
(?P<kanji>{KANJI_CHAR_RE}+)     # kanji, with no okurigana before the bracket
\[
(?P<furi>[^\]]+)
]
""",
    re.VERBOSE,
)

# The prefixes that spell themselves even when the kanji's readings settle nothing either way:
# the honorifics, a katakana run, and any run of more than one kana. A lone hiragana in front of
# a kanji is a particle far more often than it is part of the word, so も紅葉[もみじ] keeps its
# reading whole while お土産[おみやげ] gives the お back - both readings the kanji cannot account for.
SELF_READING_PREFIX_REC = re.compile(r"^(?:[おご]|御|[ァ-ヶー]+|[ぁ-んァ-ヶー]{2,})$")


def unread_kanji_count(kanji: str, furigana: str) -> int:
    """
    How many of `kanji` no listed reading can account for if `furigana` is their whole reading.

    Zero means every kanji was matched to a reading of its own, which is the alignment the main
    pass is looking for; a higher count means that many were left to be guessed at as jukujikun.
    """
    mora_result = split_to_mora_list(furigana, len(kanji))
    # Probing a reading the writer may not have meant is expected to fail, so the alignment's
    # complaints about it are not the caller's business.
    with silenced():
        alignment = find_first_complete_alignment(
            word=kanji,
            furigana=furigana,
            maybe_okuri="",
            mora_list=mora_result["mora_list"],
        )
    return len(alignment["jukujikun_positions"])


def leading_kana_cleaning_replacer(match):
    """
    re.sub replacer for LEADING_KANA_CLEANING_REC, giving the kanji only its own reading:
    (a) お前[おまえ] becomes お前[まえ]
    (b) いい加減[いいかげん] becomes いい加減[かげん]
    (c) いざという時[いざというとき] becomes いざという時[とき]
    (d) スペイン語[すぺいんご] becomes スペイン語[ご]

    That the reading opens with the same kana as the word proves nothing on its own: a particle
    at the start of a field, of a line or after a tag opens the same way, and taking its kana out
    of the reading cost the word its first mora - か家族[かぞく] came out as か 家族[ぞく], with
    家 left unread and the word tagged jukujikun. So the kanji's own listed readings decide it:
    whichever spelling of the reading leaves fewer kanji unaccounted for is the one the writer
    meant. 家族 reads かぞく whole and ぞく not at all, so the か stays in; 前 reads まえ but not
    おまえ, so the お comes out.

    When neither spelling can be fully read - お土産[おみやげ], も紅葉[もみじ], both jukujikun
    either way - the readings settle nothing and SELF_READING_PREFIX_REC decides instead.
    """
    pre = match.group("pre")
    kanji = match.group("kanji")
    furigana = match.group("furi")
    # Compared as hiragana: the word may write its kana as katakana while the reading is kana.
    prefix = to_hiragana(pre)
    if not to_hiragana(furigana).startswith(prefix) or len(furigana) <= len(prefix):
        # お金[かね] omits the お from its reading, so there is nothing to take out of it.
        return match.group(0)
    stripped = furigana[len(prefix) :]
    kept_unread = unread_kanji_count(kanji, furigana)
    stripped_unread = unread_kanji_count(kanji, stripped)
    if stripped_unread != kept_unread:
        take_the_kana = stripped_unread < kept_unread
    else:
        # The kanji's readings account for neither spelling, so the prefix has to decide.
        take_the_kana = bool(SELF_READING_PREFIX_REC.match(pre))
    logger.debug(
        "leading_kana_cleaning_replacer - %s%s[%s]: unread kanji %s keeping the kana vs %s taking"
        " it, taking it: %s",
        pre,
        kanji,
        furigana,
        kept_unread,
        stripped_unread,
        take_the_kana,
    )
    if not take_the_kana:
        return match.group(0)
    return f"{pre}{kanji}[{stripped}]"


# Regex for a word written as one furigana group whose reading covers okurigana in the middle,
# so that it can be rewritten into one group per kanji run. For example
# (1) 消え去[きえさ]る
# (2) 隣り合わせ[となりあわせ]
# (3) 歯止め[はどめ]
# (4) すり下ろす[すりおろす]   - the word opens with kana
# (5) かも知れない[かもしれない] - the word opens with kana
# (6) 勿体無い[もったいない]    - the okurigana also occurs inside the reading
#
# The match has to start where the word does. Without that, (4) would match from 下 alone and
# the す・り of the reading would be handed to 下, leaving すり outside the group to spell
# itself a second time: すり 下[すりお]ろす.
OKURIGANA_MIX_CLEANING_REC = re.compile(
    rf"""
(?<![^{WORD_START_PRECEDERS}])  # the word's own start: the text's, a line's, or one after
                        # a space, a tag, a bracket or punctuation
(?P<pre>[ぁ-ん]*)        # kana before the first kanji            (4)すり (5)かも
(?P<kanji1>{KANJI_CHAR_RE}+)   # kanji                           (1)消 (2)隣 (3)歯止 (5)知
(?P<hira1>[ぁ-ん]+)      # hiragana after it                      (1)え (2)り (3)め (5)れない
(?:                     # a second kanji run, or none at all
  (?P<kanji2>{KANJI_CHAR_RE}+) #                                 (1)去 (2)合
  (?P<hira2>[ぁ-ん]*)    # hiragana after that                    (2)わせ
)?
\[
(?P=pre)                # the reading opens with the same kana the word does
(?P<furi1>[^\]]+)       # reading of kanji1  (1)き (2)とな (3)はど (4)お (5)し (6)もったいな
(?P=hira1)              # hira1 occurring again
(?(kanji2)              # only when there is a second kanji to read
  (?P<furi2>[^\]]+)     # reading of kanji2  (1)さ (2)あ
  (?P=hira2)            # hira2 occurring again
)
]
""",
    re.VERBOSE,
)
# Three things make this work that are easy to get wrong:
#
# Both reading groups are `[^\]]+` rather than `.+` so that a reading stops at its own closing
# bracket. As `.+` the greedy furi1 ran on past the `]` and took the rest of the line with it,
# so 食べ[たべ]たい 食べ[たべ]る gave the first 食 the reading たべ]たい 食べ[た and rewrote the
# second word into 食べ[た]べる, which nothing downstream reads as furigana any more.
#
# `furi1` is greedy because hira1 is the okurigana that *follows* kanji1, so it is the last
# place that run of kana can sit in the reading, not the first. Taking the first turned
# 勿体無い[もったいない] into 勿体無[もった]い[ない] - the い matched inside もったい - and the
# reading left over came out as a bracket with no word in front of it.
#
# `furi2` insists on at least one character rather than being lazy, so that a second kanji
# always gets a reading. Were it `[^\]]*?` the greedy furi1 would swallow the lot and leave
# 行き来[いきき] as 行[いき]き来[] - the engine backtracks furi1 instead when furi2 is made to
# insist on at least one character.
# Together they mean kanji2 and furi2 always take part as a pair, so neither a word without a
# reading nor a reading without a word can be produced here.


def okurigana_mix_cleaning_replacer(match):
    """
    re.sub replacer function for OKURIGANA_MIX_CLEANING_REC when it's only needed to
    clean the kanji and leave the furigana. The objective is to turn the hard to process
    case into a normal case. For example:
    (1) 消え去る[きえさ]る becomes 消[き]え去[さ]る
    (2) 隣り合わせ[となりあわせ] becomes 隣[とな]り合[あ]わせ
    (3) 歯止め[はどめ] becomes 歯[は]止[ど]め
    (4) すり下ろす[すりおろす] becomes すり下[お]ろす
    (5) かも知れない[かもしれない] becomes かも知[し]れない
    (6) 勿体無い[もったいない] becomes 勿体無[もったいな]い
    """
    pre = match.group("pre")  # kana the word opens with, which reads as itself
    kanji1 = match.group("kanji1")  # first kanji
    furigana1 = match.group("furi1")  # furigana for first kanji
    hiragana1 = match.group("hira1")  # hiragana in the middle, after the first kanji
    kanji2 = match.group("kanji2")  # second kanji, if the word has one
    furigana2 = match.group("furi2")  # furigana for second kanji
    hiragana2 = match.group("hira2") or ""  # hiragana at the end, after the second kanji

    # Return the cleaned and restructured string
    result = f"{pre}{kanji1}[{furigana1}]{hiragana1}"
    if kanji2:
        result += f"{kanji2}[{furigana2}]"
    return result + hiragana2
