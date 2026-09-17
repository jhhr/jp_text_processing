"""
Mora splitting infrastructure for furigana processing.

This module handles splitting furigana into individual mora units, which are the
basic phonetic units of Japanese. It applies special rules like ん merging when
the mora count exceeds the kanji count.
"""

from typing import TypedDict

try:
    from mecab_controller.kana_conv import to_hiragana
except ImportError:
    from ..mecab_controller.kana_conv import to_hiragana
try:
    from kana.katakana_positions import get_katakana_positions
except ImportError:
    from .katakana_positions import get_katakana_positions
try:
    from regex.mora import ALL_MORA_REC, LONG_VOWEL_MAP, ORPHAN_KANA, SMALL_TSU
except ImportError:
    from ..regex.mora import ALL_MORA_REC, LONG_VOWEL_MAP, ORPHAN_KANA, SMALL_TSU


class MoraSplitResult(TypedDict):
    """
    Result of splitting furigana into mora.

    :param mora_list: List of individual mora strings
    :param katakana_positions: List of character indices in original furigana that were katakana
    :param long_vowel_positions: List of character indices in original furigana that were long
        vowel marks (ー)
    """

    mora_list: list[str]
    katakana_positions: list[int]
    long_vowel_positions: list[int]


def normalize_long_vowel_marks(furigana: str) -> tuple[str, list[int]]:
    """
    Return furigana unchanged and capture long vowel mark (ー) indices.

    Matching behavior for ー is handled in reading comparison logic; this function only tracks
    original positions for reconstruction when marks are preserved.
    """
    if "ー" not in furigana:
        return furigana, []

    return furigana, [i for i, char in enumerate(furigana) if char == "ー"]


def long_vowel_variants(kana_string: str) -> frozenset[str]:
    """
    Spell out every ー in a kana string as the vowel it stands for.

    The vowel a ー lengthens is the vowel of the kana before it (LONG_VOWEL_MAP), but the vowel
    is not always how the word is spelled out: an お-row long vowel is usually written with う
    (とーきょー = とうきょう) and an え-row one with い (せんせー = せんせい), while the doubled
    vowel spelling also exists (おおきい, おねえさん). Both are returned for those two rows, so a
    caller matching against dictionary readings can accept either spelling.

    A ー with no mappable kana before it (string-initial, or after ん or っ) is left as it is.

    :param kana_string: Hiragana with zero or more ー in it
    :return: Every spelling the string could stand for, empty if it holds no ー
    """
    if "ー" not in kana_string:
        return frozenset()

    # Alternative spellings of a lengthened vowel, beyond the vowel itself
    alternatives = {"お": "う", "え": "い"}

    variants = [""]
    for char in kana_string:
        if char != "ー":
            variants = [variant + char for variant in variants]
            continue
        expanded = []
        for variant in variants:
            vowel = LONG_VOWEL_MAP.get(variant[-1:]) if variant else None
            if vowel is None:
                expanded.append(variant + char)
                continue
            expanded.append(variant + vowel)
            if vowel in alternatives:
                expanded.append(variant + alternatives[vowel])
        variants = expanded

    return frozenset(variants)


def attach_small_tsu(mora_list: list[str]) -> list[str]:
    """
    Attach a っ that stands alone to a neighbouring mora.

    ALL_MORA_REC already captures っ as the tail of the mora before it ("きゃっ"), so a lone っ
    can only come from a reading that starts with one, like 振[っぷり] or 丈[ったけ]. There is no
    mora before it to be the tail of, so it becomes the head of the one after it instead.

    :param mora_list: Mora as tokenized by ALL_MORA_REC
    :return: The same mora with every lone っ attached to a neighbour
    """
    if SMALL_TSU not in mora_list:
        return mora_list

    new_list: list[str] = []
    pending_small_tsu = ""
    for mora in mora_list:
        if mora == SMALL_TSU:
            if new_list:
                new_list[-1] += mora
            else:
                pending_small_tsu += mora
            continue
        new_list.append(f"{pending_small_tsu}{mora}")
        pending_small_tsu = ""
    if pending_small_tsu:
        # Nothing followed it after all, keep it rather than lose it
        new_list.append(pending_small_tsu)
    return new_list


def split_to_mora_list(furigana: str, kanji_count: int) -> MoraSplitResult:
    """
    Split furigana string into a list of mora units.

    Applies the ん merging logic: when ん appears as a separate mora and the total
    mora count exceeds kanji_count, merge ん with the previous mora. This handles
    cases like 本[ほん] where ん should be part of the same mora as ほ.

    ORPHAN_KANA - small vowels and iteration marks - are merged the same way and under the same
    condition, so that 煩[うるせぇ] keeps its ぇ while 嗚呼[あぁ] still has a mora for each kanji.

    Note: っ (small tsu) is already captured in ALL_MORA_REC as compound mora like
    "きゃっ", so only a reading-initial っ needs attaching, see attach_small_tsu.

    :param furigana: The furigana reading (can be hiragana or katakana)
    :param kanji_count: Number of kanji in the word (used for ん merging logic)
    :return: MoraSplitResult with mora_list, katakana_positions, and long_vowel_positions
    """
    # Track which positions were katakana in the original for later conversion back
    katakana_positions = get_katakana_positions(furigana)

    # Convert to hiragana for processing
    if katakana_positions:
        furigana = to_hiragana(furigana)

    # Track long-vowel positions for later reconstruction.
    _, long_vowel_positions = normalize_long_vowel_marks(furigana)

    # Extract all mora using the comprehensive regex. This is lossless, anything the regex doesn't
    # know as a mora comes back as a single-character token to be attached below.
    mora_list = ALL_MORA_REC.findall(furigana)

    # A reading-initial っ has no mora before it to attach to, give it the one after it
    mora_list = attach_small_tsu(mora_list)

    # Merge ん and orphan small kana with the previous mora, only when len(mora_list) > kanji_count
    mergeable = frozenset(f"ん{ORPHAN_KANA}")
    if not mergeable.isdisjoint(mora_list) and len(mora_list) > kanji_count:
        new_list: list[str] = []
        for mora in mora_list:
            if mora in mergeable and len(new_list) > 0:
                # Merge with previous mora
                new_list[-1] += mora
            else:
                new_list.append(mora)
        mora_list = new_list

    # If the furigana contained long vowels represented by ー, and we didn't get enough mora,
    # convert the ー into the previous vowel and splice it in as its own mora. In this branch,
    # restoration to ー should not be applied because the reading is being redistributed.
    if "ー" in furigana and len(mora_list) < kanji_count:
        long_vowel_positions = []
        mora_list = mora_list.copy()
        for i, mora in enumerate(mora_list):
            if len(mora) >= 2 and mora[-1] == "ー" and mora[-2] in LONG_VOWEL_MAP:
                # Split off the long vowel mark into its own mora
                before_last_char = mora[:-1]
                mora_list[i] = before_last_char
                mora_list.insert(i + 1, LONG_VOWEL_MAP[mora[-2]])

    return MoraSplitResult(
        mora_list=mora_list,
        katakana_positions=katakana_positions,
        long_vowel_positions=long_vowel_positions,
    )
