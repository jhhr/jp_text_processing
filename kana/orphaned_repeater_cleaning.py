import re

from ..regex.kanji_furi import KANJI_RANGES

# 々 stands in for the kanji written before it, so it is only ever half of a word. The furigana
# regex reads a word as an unbroken run of kanji before a bracket, which means anything sitting
# between the kanji and its 々 - a space, or the kanji having been given a bracket of its own -
# leaves the 々 as a word all by itself. On its own it has no readings to match, so it ends up
# read as jukujikun and 其々[それぞれ] comes out as 其<juk> 々[それぞれ]</juk>.
#
# The character 々 repeats has to be a real kanji, not the ヶ of 三ヶ月 or a number, both of which
# KANJI_CHAR_RE otherwise counts as kanji for furigana purposes.
REPEATED_KANJI_RE = rf"[{KANJI_RANGES}]"

# Regex for a 々 separated from the word it belongs to. For example
# (a) 其 々[それぞれ]      - only the 々 was given the reading
# (b) 其[それ]々[ぞれ]     - each was given its own half of the reading
# (c) 其[それ] 々[ぞれ]    - both of the above at once
#
# Something has to come between the two for there to be anything to repair, so the bracket and
# the space are not both optional: without that this would match 其々[それぞれ], which is already
# written the way the repair aims at.
ORPHANED_REPEATER_CLEANING_REC = re.compile(
    rf"""
(?P<word>{REPEATED_KANJI_RE}+)  # the word, whose last kanji is the one 々 stands in for
(?:
  \[(?P<furi1>[^\]]*)][ ]*      # a reading of its own, and maybe a space too  (b)[それ] (c)[それ]
 | [ ]+                         # or just a space                              (a)
)
々
\[(?P<furi2>[^\]]*)]            # the reading the 々 was given  (a)それぞれ (b)ぞれ (c)ぞれ
""",
    re.VERBOSE,
)


def orphaned_repeater_cleaning_replacer(match):
    """
    re.sub replacer for ORPHANED_REPEATER_CLEANING_REC, writing the word and its 々 back into
    the one furigana group they should have been in:
    (a) 其 々[それぞれ] becomes 其々[それぞれ]
    (b) 其[それ]々[ぞれ] becomes 其々[それぞれ]
    (c) 其[それ] 々[ぞれ] becomes 其々[それぞれ]

    The whole kanji run is kept, not just the kanji 々 repeats, so that the rest of the word is
    not dropped along with its reading: 生物[せいぶつ]々[ぶつ] is 生物々[せいぶつぶつ], not
    物々[せいぶつぶつ].
    """
    furi1 = match.group("furi1") or ""
    return f"{match.group('word')}々[{furi1}{match.group('furi2')}]"
