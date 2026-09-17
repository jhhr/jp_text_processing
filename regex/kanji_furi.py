import re

# Regex matching any kanji characters or other characters to be treated as kanji, including
# - the counter characters ヶ and ヵ which are just small katakana
# - the kanji repeater punctuation as something that will be cleaned off
# - numbers as they are sometimes used in furigana instead of their kanji counterparts
KANJI_CHAR_RE = r"[\d々ヶヵ\u4e00-\u9faf\u3400-\u4dbf]"
KANJI_RE = rf"({KANJI_CHAR_RE}+)"
KANJI_REC = re.compile(KANJI_RE)
# Same as above but allows for being empty
KANJI_RE_OPT = rf"({KANJI_CHAR_RE}*)"

# Matching any furigana with match groups
FURIGANA_RE = r" ?([^ >]+?)\[(.+?)\]"
FURIGANA_REC = re.compile(FURIGANA_RE)

# Matching any furigana without match groups
FURIGANA_NO_GROUPS_RE = r" ?[^ >]+\[[^ >]+\]"
FURIGANA_NO_GROUPS_REC = re.compile(FURIGANA_NO_GROUPS_RE)

# Text that contains any kanji repeated, to be replaced by the kanji+々
DOUBLE_KANJI_RE = r"([\u4e00-\u9faf\u3400-\u4dbf])\1"
DOUBLE_KANJI_REC = re.compile(DOUBLE_KANJI_RE)

KANJI_AND_REPEATER_RE = r"([\u4e00-\u9faf\u3400-\u4dbf]々)"
KANJI_AND_REPEATER_REC = re.compile(KANJI_AND_REPEATER_RE)

# Regex matching any kanji and furigana + hiragana after the furigana
KANJI_AND_FURIGANA_AND_OKURIGANA_RE = r"([\d々ヶヵ\u4e00-\u9faf\u3400-\u4dbf]+)\[(.*?)\]([ぁ-ん]*)"
KANJI_AND_FURIGANA_AND_OKURIGANA_REC = re.compile(KANJI_AND_FURIGANA_AND_OKURIGANA_RE)

HIRAGANA_RE = "([ぁ-ん])"
KATAKANA_RE = "([ァ-ン])"
KATAKANA_REC = re.compile(KATAKANA_RE)

# The kana a furigana reading may consist of. ぁ-ん / ァ-ン stop short of the kana that live above
# ん and ン in the block, so spell those out: ゔゕゖ / ヴ, the iteration marks ゝゞ / ヽヾ which stand
# in for a repeated kana (儘[まゝ]), and the combining handakuten of か゚ き゚. ヵ and ヶ are
# deliberately left out, KANJI_CHAR_RE claims those as kanji.
KANA_CHARS = "ぁ-ゖゝゞァ-ヴヽヾー゚"  # the last one is U+309A
KANA_CHAR_RE = rf"[{KANA_CHARS}]"
KANA_REC = re.compile(KANA_CHAR_RE)
NON_KANA_REC = re.compile(rf"[^{KANA_CHARS}]")
