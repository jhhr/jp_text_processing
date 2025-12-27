import re

# Regex matching any kanji characters
# Include the kanji repeater punctuation as something that will be cleaned off
# Also include numbers as they are sometimes used in furigana
KANJI_RE = r"([\d々\u4e00-\u9faf\u3400-\u4dbf]+)"
KANJI_REC = re.compile(KANJI_RE)
# Same as above but allows for being empty
KANJI_RE_OPT = r"([\d々\u4e00-\u9faf\u3400-\u4dbf]*)"

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
KANJI_AND_FURIGANA_AND_OKURIGANA_RE = r"([\d々\u4e00-\u9faf\u3400-\u4dbf]+)\[(.+?)\]([ぁ-ん]*)"
KANJI_AND_FURIGANA_AND_OKURIGANA_REC = re.compile(KANJI_AND_FURIGANA_AND_OKURIGANA_RE)

HIRAGANA_RE = "([ぁ-ん])"
KATAKANA_RE = "([ァ-ン])"
KATAKANA_REC = re.compile(KATAKANA_RE)
