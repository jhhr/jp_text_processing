import re

# The code point ranges that are kanji, for a character class. Besides the CJK unified
# ideographs and their extension A there are 〆 and 〇, which are written as part of a word
# (〆切, 四〇三), the compatibility ideographs, and the supplementary planes from extension B
# on. Python's re takes those last ones in a character class as they are.
KANJI_RANGES = "\u3006\u3007\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff\U00020000-\U0002fa1f"

# Regex matching any kanji characters or other characters to be treated as kanji, including
# - the counter characters ヶ and ヵ which are just small katakana
# - the kanji repeater punctuation as something that will be cleaned off
# - numbers as they are sometimes used in furigana instead of their kanji counterparts
KANJI_CHAR_RE = rf"[\d々ヶヵ{KANJI_RANGES}]"
KANJI_RE = rf"({KANJI_CHAR_RE}+)"

# Matching any furigana with match groups
FURIGANA_RE = r" ?([^ >]+?)\[(.+?)\]"
FURIGANA_REC = re.compile(FURIGANA_RE)

# Text that contains any kanji repeated, to be replaced by the kanji+々
DOUBLE_KANJI_RE = rf"([{KANJI_RANGES}])\1"
DOUBLE_KANJI_REC = re.compile(DOUBLE_KANJI_RE)

# Regex matching any kanji and furigana + hiragana after the furigana
KANJI_AND_FURIGANA_AND_OKURIGANA_RE = rf"([\d々ヶヵ{KANJI_RANGES}]+)\[(.*?)\]([ぁ-ん]*)"
KANJI_AND_FURIGANA_AND_OKURIGANA_REC = re.compile(KANJI_AND_FURIGANA_AND_OKURIGANA_RE)

# The kana a furigana reading may consist of. ぁ-ん / ァ-ン stop short of the kana that live above
# ん and ン in the block, so spell those out: ゔゕゖ / ヴ, the iteration marks ゝゞ / ヽヾ which stand
# in for a repeated kana (儘[まゝ]), and the combining handakuten of か゚ き゚. ヵ and ヶ are
# deliberately left out, KANJI_CHAR_RE claims those as kanji.
KANA_CHARS = "ぁ-ゖゝゞァ-ヴヽヾー゚"  # the last one is U+309A
KANA_CHAR_RE = rf"[{KANA_CHARS}]"
NON_KANA_REC = re.compile(rf"[^{KANA_CHARS}]")
