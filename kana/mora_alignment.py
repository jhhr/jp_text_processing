"""
Mora-to-kanji alignment module with early exit optimization.

This module implements the combinatorial mora alignment algorithm that tries
all possible ways to split mora among kanji, returning the first complete match.
"""

from typing import Optional

try:
    from all_types.main_types import ReadingMatchInfo, MoraAlignment
except ImportError:
    from ..all_types.main_types import ReadingMatchInfo, MoraAlignment
try:
    from kana.get_ordered_sublists import get_ordered_sublists
except ImportError:
    from .get_ordered_sublists import get_ordered_sublists
try:
    from kana.reading_matcher import (
        match_reading_to_mora,
        extract_okurigana_for_match,
    )
except ImportError:
    from .reading_matcher import (
        match_reading_to_mora,
        extract_okurigana_for_match,
    )
try:
    from regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA
except ImportError:
    from ..regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA
try:
    from kanji.all_kanji_data import all_kanji_data
except ImportError:
    from ..kanji.all_kanji_data import all_kanji_data
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger


def contains_repeated_kanji(word: str) -> bool:
    """
    Check if the word contains a repeater (々).
    """
    for i in range(1, len(word)):
        if word[i] == "々":
            return True
    return False


def is_valid_split_for_repeaters(word: str, split: list[list[str]]) -> bool:
    """
    Filter splits to only those valid for repeater kanji (々)
    For each 々 at position i, the mora split at position i must have the same
    length as the mora split at position i-1 (the kanji being repeated)
    """
    for i, kanji in enumerate(word):
        if kanji == "々" and i > 0:
            # This is a repeater - check if mora count matches previous kanji
            if len(split[i]) != len(split[i - 1]):
                return False
    return True


def find_first_complete_alignment(
    word: str,
    okurigana: str,
    mora_list: Optional[list[str]] = None,
    possible_splits: Optional[list[list[str]]] = None,
    is_whole_word: bool = False,
    logger: Logger = Logger("error"),
) -> MoraAlignment:
    """
    Find the first complete alignment of mora to kanji with early exit.

    Uses get_ordered_sublists to generate all possible mora divisions in order,
    and returns immediately when a complete match (all kanji matched) is found.

    If no complete match exists, returns the best partial alignment (fewest jukujikun positions).

    :param word: The word to align (string of kanji, may include 々)
    :param all_kanji_data: Dictionary mapping kanji to their reading data
    :param okurigana: The okurigana following the word (for last kanji extraction)
    :param mora_list: List of mora units to distribute across kanji, optional if possible_splits
       provided
    :param possible_splits: Precomputed list of possible mora splits, optional, replaces mora_list
    :param is_whole_word: Whether the alignment is for the whole word (affects matching logic)
    :return: MoraAlignment with the first complete match or best partial match
    """
    kanji_count = len(word)

    # Handle edge case: empty word
    if kanji_count == 0:
        return MoraAlignment(
            kanji_matches=[],
            mora_split=[],
            jukujikun_positions=[],
            is_complete=True,
            final_okurigana="",
            final_rest_kana="",
        )

    # Get all possible mora splits in order, if a ready-made list is not provided
    if possible_splits is None:
        if mora_list is None:
            raise ValueError("Either mora_list or possible_splits must be provided")
        possible_splits = get_ordered_sublists(mora_list, kanji_count)

    # Filter out invalid splits
    if contains_repeated_kanji(word):
        possible_splits = [s for s in possible_splits if is_valid_split_for_repeaters(word, s)]

    best_alignment: Optional[MoraAlignment] = None
    best_jukujikun_count = kanji_count + 1  # Start with worst possible

    for mora_split in possible_splits:
        kanji_matches: list[Optional[ReadingMatchInfo]] = []
        jukujikun_positions: list[int] = []
        final_okurigana = ""
        final_rest_kana = ""

        # Try to match each kanji to its mora portion
        i = 0
        while i < kanji_count:
            kanji = word[i]
            is_last_kanji = i == kanji_count - 1

            # Check if next kanji is repeated
            next_kanji = word[i + 1] if i < kanji_count - 1 else ""
            next_kanji_is_repeater = next_kanji == "々" or next_kanji == kanji

            # Join the mora sublist for this kanji position
            try:
                mora_sequence = "".join(mora_split[i])
            except IndexError:
                mora_sequence = ""
                logger.error(
                    "find_first_complete_alignment - mora_split contains fewer parts than"
                    f" kanji_count for word '{word}': {mora_split} vs {kanji_count}"
                )

            # IMPORTANT: For repeater kanji, do NOT include the next position's mora
            # We match ONLY the first occurrence, then validate the second separately

            # Get kanji data
            kanji_data = all_kanji_data.get(kanji, None)
            if kanji_data is None:
                logger.error(f"Kanji data not found for '{kanji}'")
                kanji_data = {}

            # Try to match reading
            match_info = match_reading_to_mora(
                kanji=kanji,
                mora_sequence=mora_sequence,
                kanji_data=kanji_data,
                okurigana=okurigana if is_last_kanji and not next_kanji_is_repeater else "",
                is_last_kanji=is_last_kanji and not next_kanji_is_repeater,
                prefer_kunyomi=is_whole_word,
                logger=logger,
            )

            if match_info:
                # For repeater, check if second occurrence has rendaku
                if next_kanji_is_repeater:
                    first_mora = "".join(mora_split[i])
                    second_mora = "".join(mora_split[i + 1])

                    # Check for rendaku in second occurrence
                    rendaku_matched = False
                    if second_mora and second_mora[0] in RENDAKU_CONVERSION_DICT_HIRAGANA.values():
                        # Second mora might have rendaku, verify it matches first mora with rendaku
                        for plain_kana, rendaku_kanas in RENDAKU_CONVERSION_DICT_HIRAGANA.items():
                            if first_mora[0] == plain_kana:
                                for rendaku_kana in rendaku_kanas:
                                    if second_mora.startswith(rendaku_kana + first_mora[1:]):
                                        rendaku_matched = True
                                        break
                                if rendaku_matched:
                                    break

                    # Add match for first kanji
                    kanji_matches.append(match_info)

                    # Add duplicate match for 々 (copy reading but mark as second occurrence)
                    repeater_match = match_info.copy()
                    repeater_match["matched_mora"] = second_mora
                    repeater_match["kanji"] = "々"

                    # Check if repeater is the last kanji - if so, extract okurigana
                    repeater_is_last = (i + 1) == kanji_count - 1
                    if repeater_is_last:
                        okuri_extracted, rest_extracted = extract_okurigana_for_match(
                            match_type=repeater_match["match_type"],
                            dict_form=repeater_match["dict_form"],
                            remaining_kana=okurigana,
                            # Use the original kanji being repeated for okurigana extraction,
                            # not the repeater glyph itself
                            kanji=word[i],
                            logger=logger,
                        )
                        repeater_match["okurigana"] = okuri_extracted
                        repeater_match["rest_kana"] = rest_extracted
                        final_okurigana = okuri_extracted
                        final_rest_kana = rest_extracted

                    kanji_matches.append(repeater_match)

                    # Skip next position since we handled repeater
                    i += 2
                    continue

                # Extract okurigana if this is the last kanji (and not repeater)
                if is_last_kanji:
                    okuri_extracted, rest_extracted = extract_okurigana_for_match(
                        match_type=match_info["match_type"],
                        dict_form=match_info["dict_form"],
                        remaining_kana=okurigana,
                        kanji=kanji,
                        logger=logger,
                    )
                    match_info["okurigana"] = okuri_extracted
                    match_info["rest_kana"] = rest_extracted
                    final_okurigana = okuri_extracted
                    final_rest_kana = rest_extracted

                kanji_matches.append(match_info)
            else:
                # No match - mark as jukujikun
                kanji_matches.append(None)
                jukujikun_positions.append(i)

                # If this has a repeater, also mark repeater as jukujikun
                if next_kanji_is_repeater:
                    kanji_matches.append(None)
                    jukujikun_positions.append(i + 1)
                    i += 2
                    continue

            i += 1

        # Create alignment result
        alignment = MoraAlignment(
            kanji_matches=kanji_matches,
            mora_split=mora_split,
            jukujikun_positions=jukujikun_positions,
            is_complete=len(jukujikun_positions) == 0,
            final_okurigana=final_okurigana,
            final_rest_kana=final_rest_kana,
        )

        # Yōon boundary adjustment: if a yōon mora like しょ, きゃ is at a jukujikun
        # position and the previous kanji has a kunyomi match, try to split the yōon
        # so that the base kana attaches to the previous kanji and the small kana
        # becomes the next kanji's matched mora. This handles cases like 端折[はしょ]る
        # where the reading for 折 is お but should match only the small kana ょ.
        if len(jukujikun_positions) > 0:
            new_juku_positions = list(jukujikun_positions)
            for pos in list(jukujikun_positions):
                if pos > 0 and alignment["kanji_matches"][pos - 1]:
                    prev_match = alignment["kanji_matches"][pos - 1]
                    if prev_match["match_type"] == "kunyomi":
                        # Next mora sequence
                        next_mora = "".join(mora_split[pos])
                        prev_kanji = word[pos - 1]
                        prev_data = all_kanji_data.get(prev_kanji, {})
                        kunyomi_str = prev_data.get("kunyomi", prev_data.get("kun", ""))
                        stems = [r.split(".")[0] for r in kunyomi_str.split("、") if r]
                        full_forms = [r.replace(".", "") for r in kunyomi_str.split("、") if r]
                        # Case A: yōon contraction across boundary
                        if len(next_mora) == 2 and next_mora[1] in ["ゃ", "ゅ", "ょ"]:
                            base = next_mora[0]
                            small = next_mora[1]
                            extended = prev_match["matched_mora"] + base
                            if extended in stems:
                                # Apply adjustment: extend prev, set current as small kana kunyomi
                                prev_match["matched_mora"] = extended
                                alignment["kanji_matches"][pos] = {
                                    "reading": small,
                                    "dict_form": small,
                                    "match_type": "kunyomi",
                                    "reading_variant": "vowel_change",
                                    "matched_mora": small,
                                    "kanji": word[pos],
                                    "okurigana": "",
                                    "rest_kana": "",
                                }
                                # Remove pos from jukujikun positions
                                new_juku_positions = [p for p in new_juku_positions if p != pos]
                        else:
                            # Case B: carry over leading kana from juku to previous stem if valid
                            if next_mora:
                                lead = next_mora[0]
                                extended = prev_match["matched_mora"] + lead
                                if extended in stems or extended in full_forms:
                                    # Extend previous matched mora
                                    prev_match["matched_mora"] = extended
                                    # Adjust mora split: move leading kana to previous position
                                    prev_seq = "".join(mora_split[pos - 1])
                                    mora_split[pos - 1] = [prev_seq + lead]
                                    mora_split[pos] = [next_mora[1:]] if len(next_mora) > 1 else []
                                    # Keep current position as jukujikun (now with reduced mora)
            alignment["jukujikun_positions"] = new_juku_positions
            alignment["is_complete"] = len(new_juku_positions) == 0

        # If last kanji now has a match but okurigana/rest were not extracted, handle it
        if (
            alignment["kanji_matches"]
            and alignment["kanji_matches"][kanji_count - 1]
            and not alignment["final_okurigana"]
        ):
            last_match = alignment["kanji_matches"][kanji_count - 1]
            okuri_extracted, rest_extracted = extract_okurigana_for_match(
                match_type=last_match["match_type"],
                dict_form=last_match["dict_form"],
                remaining_kana=okurigana,
                kanji=word[kanji_count - 1],
                logger=logger,
            )
            alignment["final_okurigana"] = okuri_extracted
            alignment["final_rest_kana"] = rest_extracted

        # Early exit: if we found a complete match, return immediately
        if alignment["is_complete"]:
            return alignment

        # Track best partial alignment (fewest jukujikun positions)
        if len(jukujikun_positions) < best_jukujikun_count:
            best_jukujikun_count = len(jukujikun_positions)
            best_alignment = alignment

    # No complete match found, return best partial alignment
    if best_alignment:
        return best_alignment

    # Fallback: all kanji are jukujikun
    return MoraAlignment(
        kanji_matches=[None] * kanji_count,
        mora_split=[[m] for m in mora_list[:kanji_count]],  # Distribute evenly
        jukujikun_positions=list(range(kanji_count)),
        is_complete=False,
        final_okurigana="",
        final_rest_kana=okurigana,
    )
