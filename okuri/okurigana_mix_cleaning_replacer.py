import re

try:
    from regex.kanji_furi import KANJI_CHAR_RE
except ImportError:
    from ..regex.kanji_furi import KANJI_CHAR_RE
try:
    from mecab_controller.kana_conv import to_hiragana
except ImportError:
    from ..mecab_controller.kana_conv import to_hiragana

# Regex for a word that opens with kana and then has nothing but kanji before its furigana, so
# that the kana it opens with can be taken out of the reading. For example
# (a) お前[おまえ]
# (b) いい加減[いいかげん]
# (c) いざという時[いざというとき]
# (d) スペイン語[すぺいんご]   - the word's kana is katakana, the reading's is hiragana
#
# The kana is only taken when the reading opens with it too, which the replacer checks, and
# only where the word itself starts, so that a particle in a sentence is never mistaken for
# part of the word after it. Without this the main pass hands the whole reading to the kanji
# and the opening kana spells itself twice: お前[おまえ] came out as お 前[おまえ], read おおまえ.
LEADING_KANA_CLEANING_REC = re.compile(
    rf"""
(?<![^ >])                      # the word's own start: the text's, a space's or a tag's
(?P<pre>[ぁ-んァ-ヶー]+)          # the kana the word opens with   (a)お (b)いい (d)スペイン
(?P<kanji>{KANJI_CHAR_RE}+)     # kanji, with no okurigana before the bracket
\[
(?P<furi>[^\]]+)
]
""",
    re.VERBOSE,
)


def leading_kana_cleaning_replacer(match):
    """
    re.sub replacer for LEADING_KANA_CLEANING_REC, giving the kanji only its own reading:
    (a) お前[おまえ] becomes お前[まえ]
    (b) いい加減[いいかげん] becomes いい加減[かげん]
    (c) いざという時[いざというとき] becomes いざという時[とき]
    (d) スペイン語[すぺいんご] becomes スペイン語[ご]

    The word is left alone unless the reading really does open with the same kana, read the
    same way - お金[かね] omits the お from its reading, and there is nothing to take out of
    it - and unless something is left over afterwards for the kanji to be read as.
    """
    pre = match.group("pre")
    furigana = match.group("furi")
    # Compared as hiragana: the word may write its kana as katakana while the reading is kana.
    prefix = to_hiragana(pre)
    if not to_hiragana(furigana).startswith(prefix) or len(furigana) <= len(prefix):
        return match.group(0)
    return f"{pre}{match.group('kanji')}[{furigana[len(prefix):]}]"


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
(?<![^ >])              # the word's own start: the text's, a space's or a tag's
(?P<pre>[ぁ-ん]*)        # kana before the first kanji            (4)すり (5)かも
(?P<kanji1>{KANJI_CHAR_RE}+)   # kanji                           (1)消 (2)隣 (3)歯止 (5)知
(?P<hira1>[ぁ-ん]+)      # hiragana after it                      (1)え (2)り (3)め (5)れない
(?:                     # a second kanji run, or none at all
  (?P<kanji2>{KANJI_CHAR_RE}+) #                                 (1)去 (2)合
  (?P<hira2>[ぁ-ん]*)    # hiragana after that                    (2)わせ
)?
\[
(?P=pre)                # the reading opens with the same kana the word does
(?P<furi1>.+)           # reading of kanji1  (1)き (2)とな (3)はど (4)お (5)し (6)もったいな
(?P=hira1)              # hira1 occurring again
(?(kanji2)              # only when there is a second kanji to read
  (?P<furi2>.+)         # reading of kanji2  (1)さ (2)あ
  (?P=hira2)            # hira2 occurring again
)
]
""",
    re.VERBOSE,
)
# Two things make this work that are easy to get wrong:
#
# `furi1` is greedy because hira1 is the okurigana that *follows* kanji1, so it is the last
# place that run of kana can sit in the reading, not the first. Taking the first turned
# 勿体無い[もったいない] into 勿体無[もった]い[ない] - the い matched inside もったい - and the
# reading left over came out as a bracket with no word in front of it.
#
# `furi2` is `.+` rather than `.*?` so that a second kanji always gets a reading. With `.*?`
# the greedy furi1 would swallow the lot and leave 行き来[いきき] as 行[いき]き来[] - the
# engine backtracks furi1 instead when furi2 is made to insist on at least one character.
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
