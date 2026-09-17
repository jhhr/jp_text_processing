"""
Normalization of furigana into a form the reading matcher can work with.

Some kana carry no reading of their own and so never appear in a kanji's listed readings. Left in
place they stop the whole word from matching and it falls through to being tagged jukujikun:

- a reading-initial っ (振[っぷり], 丈[ったけ]) is gemination carried over from the word before it
- a small vowel standing on its own (煩[うるせぇ], 嗚呼[あぁ]) is a written-out drawl of the vowel
  before it
- an iteration mark (儘[まゝ], 儘[マヽ]) is shorthand for repeating the kana before it

So each is taken out of the way before matching - dropped, or rewritten to the kana it stands for -
and put back afterwards from the recorded positions, the same way a long vowel mark ー is.
"""

from typing import TypedDict

try:
    from mecab_controller.kana_conv import to_hiragana, to_katakana, is_katakana_char
except ImportError:
    from ..mecab_controller.kana_conv import to_hiragana, to_katakana, is_katakana_char
try:
    from regex.mora import ALL_MORA_REC, ORPHAN_KANA, SMALL_TSU
except ImportError:
    from ..regex.mora import ALL_MORA_REC, ORPHAN_KANA, SMALL_TSU
try:
    from regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA
except ImportError:
    from ..regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA


# The full-size kana a small one drawls out. ゕ and ゖ are here for completeness, they only ever
# turn up as counters.
SMALL_TO_FULL_KANA = {
    "ぁ": "あ",
    "ぃ": "い",
    "ぅ": "う",
    "ぇ": "え",
    "ぉ": "お",
    "ゃ": "や",
    "ゅ": "ゆ",
    "ょ": "よ",
    "ゎ": "わ",
    "ゕ": "か",
    "ゖ": "け",
}

# Repeat the previous kana, ゞ repeating it voiced (まゞ is まざ)
ITERATION_MARK = "ゝ"
VOICED_ITERATION_MARK = "ゞ"


class NormalizedFurigana(TypedDict):
    """
    Furigana rewritten for matching, plus what it takes to undo that.

    :param furigana: What the reading matcher should see
    :param prefix: Kana taken off the front of the furigana, to be put back on the first kanji's
        reading once matching is done
    :param restored_chars: Index in `furigana` → the character the original had there. Indices are
        into `furigana`, so a caller that puts `prefix` back has to shift them by its length.
    """

    furigana: str
    prefix: str
    restored_chars: dict[int, str]


def find_orphan_small_kana(furigana: str) -> list[int]:
    """
    Find the small kana in a reading that aren't part of a mora.

    The ゃ of きゃ is part of one and is left alone; the ぇ of うるせぇ is not, and is what this
    reports. ALL_MORA_REC hands back anything it doesn't know as a single character, so an orphan
    is exactly a one-character token that is a small kana.

    :param furigana: The reading, in hiragana
    :return: Indices into furigana of the small kana that stand on their own
    """
    positions: list[int] = []
    index = 0
    for mora in ALL_MORA_REC.findall(furigana):
        if len(mora) == 1 and mora in ORPHAN_KANA and mora in SMALL_TO_FULL_KANA:
            positions.append(index)
        index += len(mora)
    return positions


def normalize_furigana_for_matching(furigana: str) -> NormalizedFurigana:
    """
    Rewrite a furigana reading into the form a kanji's listed readings can be matched against.

    :param furigana: The furigana as written, hiragana or katakana
    :return: NormalizedFurigana with the reading to match, the prefix taken off it, and the
        characters to put back
    """
    restored_chars: dict[int, str] = {}
    original_chars = list(furigana)
    chars = list(furigana)

    # Whatever a position ends up being rewritten to, and however many passes touch it, what goes
    # back there is what the reading was written with. まゝ has its ゝ rewritten to ま and then that
    # ま taken for an orphan, and it is still a ゝ that belongs at that position.
    def record(index: int) -> None:
        restored_chars[index] = original_chars[index]

    # An iteration mark first, so that what it stands for is there for the steps below to read
    for i, char in enumerate(chars):
        if i == 0 or to_hiragana(char) not in (ITERATION_MARK, VOICED_ITERATION_MARK):
            continue
        repeated = chars[i - 1]
        if to_hiragana(char) == VOICED_ITERATION_MARK:
            voiced = RENDAKU_CONVERSION_DICT_HIRAGANA.get(to_hiragana(repeated))
            if voiced:
                # Keep the script of the kana being repeated
                repeated = to_katakana(voiced[0]) if is_katakana_char(repeated) else voiced[0]
        record(i)
        chars[i] = repeated

    # Then the small kana that no mora claimed, which needs the mora split to tell
    hiragana = to_hiragana("".join(chars))
    for i in find_orphan_small_kana(hiragana):
        full_kana = SMALL_TO_FULL_KANA[hiragana[i]]
        record(i)
        # Keep the script, so that the katakana positions taken from this still line up
        chars[i] = to_katakana(full_kana) if is_katakana_char(chars[i]) else full_kana

    # A leading っ has nothing before it to geminate, so it can only come from the word before.
    # Take it off rather than rewrite it, there is no kana it stands for.
    prefix = ""
    if len(chars) > 1 and to_hiragana(chars[0]) == SMALL_TSU:
        prefix = original_chars[0]
        chars = chars[1:]
        restored_chars = {i - 1: char for i, char in restored_chars.items()}

    return NormalizedFurigana(
        furigana="".join(chars),
        prefix=prefix,
        restored_chars=restored_chars,
    )
