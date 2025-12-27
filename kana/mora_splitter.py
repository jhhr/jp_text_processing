"""
Mora splitting infrastructure for furigana processing.

This module handles splitting furigana into individual mora units, which are the
basic phonetic units of Japanese. It applies special rules like ん merging when
the mora count exceeds the kanji count.
"""

from typing import TypedDict

try:
    from mecab_controller.kana_conv import to_hiragana, is_katakana_str
except ImportError:
    from ..mecab_controller.kana_conv import to_hiragana, is_katakana_str
try:
    from regex.mora import ALL_MORA_REC
except ImportError:
    from ..regex.mora import ALL_MORA_REC


class MoraSplitResult(TypedDict):
    """
    Result of splitting furigana into mora.

    :param mora_list: List of individual mora strings
    :param was_katakana: True if input was in katakana (for later conversion back)
    """

    mora_list: list[str]
    was_katakana: bool


def split_to_mora_list(furigana: str, kanji_count: int) -> MoraSplitResult:
    """
    Split furigana string into a list of mora units.

    Applies the ん merging logic: when ん appears as a separate mora and the total
    mora count exceeds kanji_count, merge ん with the previous mora. This handles
    cases like 本[ほん] where ん should be part of the same mora as ほ.

    Note: っ (small tsu) is already captured in ALL_MORA_REC as compound mora like
    "きゃっ", so no separate っ merging is needed.

    :param furigana: The furigana reading (can be hiragana or katakana)
    :param kanji_count: Number of kanji in the word (used for ん merging logic)
    :return: MoraSplitResult with mora_list and was_katakana flag
    """
    # Detect if input is katakana
    was_katakana = is_katakana_str(furigana)

    # Convert to hiragana for processing
    if was_katakana:
        furigana = to_hiragana(furigana)

    # Extract all mora using the comprehensive regex
    mora_list = ALL_MORA_REC.findall(furigana)

    # Merge ん with previous mora only when len(mora_list) > kanji_count
    if "ん" in mora_list and len(mora_list) > kanji_count:
        new_list: list[str] = []
        for mora in mora_list:
            if mora == "ん" and len(new_list) > 0:
                # Merge ん with previous mora
                new_list[-1] += mora
            else:
                new_list.append(mora)
        mora_list = new_list

    return MoraSplitResult(mora_list=mora_list, was_katakana=was_katakana)
