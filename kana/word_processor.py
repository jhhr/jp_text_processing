"""
Word processor module for handling complete word furigana processing.

This module consolidates reading matching across entire words by using mora-based
alignment instead of the legacy edge-based system. It replaces the scattered logic
from check_onyomi_readings, check_kunyomi_readings, and process_readings.
"""

from typing import Optional, TypedDict

try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger

try:
    from all_types.main_types import WithTagsDef
except ImportError:
    from ..all_types.main_types import WithTagsDef

try:
    from reading_matcher import match_reading_to_mora
except ImportError:
    from .reading_matcher import match_reading_to_mora

try:
    from kanji.all_kanji_data import all_kanji_data
except ImportError:
    from ..kanji.all_kanji_data import all_kanji_data

try:
    from mecab_controller.kana_conv import to_katakana
except ImportError:
    from ..mecab_controller.kana_conv import to_katakana


class WordProcessingResult(TypedDict):
    """
    Result of processing a complete word's furigana against its kanji.

    :param furigana: The processed furigana string with tags if requested
    :param mora_list: The mora sequence that was matched
    :param kanji_matches: List of match results for each kanji
    :param was_katakana: Whether the original furigana was in katakana
    """

    furigana: str
    mora_list: list[str]
    kanji_matches: list[Optional[dict]]
    was_katakana: bool


def process_word_with_mora_alignment(
    word: str,
    mora_list: list[str],
    was_katakana: bool,
    with_tags_def: WithTagsDef,
    okurigana: str = "",
    kanji_to_highlight: str = "",
    logger: Logger = Logger("error"),
) -> WordProcessingResult:
    """
    Process a complete word using mora-based alignment instead of edge-based system.

    This function:
    1. Aligns kanji in the word to mora in the furigana sequence
    2. For each kanji, tries to match onyomi then kunyomi readings
    3. Builds tagged furigana output if requested
    4. Returns complete match information for all kanji

    The mora-based approach implicitly handles what the old system did with Edge
    (left/right/middle/whole) by simply aligning mora to kanji positions.

    :param word: The kanji word to process
    :param mora_list: The mora sequence from the furigana
    :param was_katakana: Whether original furigana was in katakana
    :param with_tags_def: Tag configuration
    :param okurigana: The okurigana portion (after the word)
    :param kanji_to_highlight: Kanji to add highlight tags around
    :param logger: Logger for debugging
    :return: WordProcessingResult with matched furigana and match details
    """
    logger.debug(f"process_word_with_mora_alignment - word: {word}, mora_list: {mora_list}")

    kanji_count = len(word)
    mora_count = len(mora_list)

    # Distribute mora among kanji
    # Start by assigning mora_count // kanji_count to each kanji,
    # then distribute remainder
    mora_per_kanji = mora_count // kanji_count
    remainder = mora_count % kanji_count

    kanji_matches = []
    mora_index = 0
    furigana_parts = []

    for kanji_index, kanji in enumerate(word):
        # Skip repeater kanji
        if kanji == "々":
            # Use previous kanji's reading
            if kanji_matches:
                prev_match = kanji_matches[-1]
                if prev_match:
                    furigana_parts.append(prev_match["matched_mora"])
            kanji_matches.append(None)
            continue

        # Determine how many mora to assign to this kanji
        num_mora = mora_per_kanji
        if kanji_index < remainder:
            num_mora += 1

        # Extract the mora for this kanji
        mora_for_kanji = mora_list[mora_index : mora_index + num_mora]
        mora_sequence = "".join(mora_for_kanji)
        mora_index += num_mora

        logger.debug(
            f"process_word_with_mora_alignment - kanji_index: {kanji_index}, kanji: {kanji}, "
            f"mora_sequence: {mora_sequence}"
        )

        # Get kanji data
        kanji_data = all_kanji_data.get(kanji, {})
        if not kanji_data:
            logger.error(f"process_word_with_mora_alignment - kanji '{kanji}' not found")
            kanji_matches.append(None)
            furigana_parts.append(mora_sequence)
            continue

        # Determine if this is the last kanji (for okurigana extraction)
        is_last_kanji = kanji_index == kanji_count - 1
        remaining_kana = okurigana if is_last_kanji else ""

        # Try to match reading
        match_info = match_reading_to_mora(
            kanji=kanji,
            mora_sequence=mora_sequence,
            kanji_data=kanji_data,
            okurigana=remaining_kana,
            is_last_kanji=is_last_kanji,
        )

        if match_info:
            # Build furigana part with tags if needed
            reading = match_info["matched_mora"]

            # Convert to katakana if original was katakana and not already converted for onyomi
            if was_katakana and match_info["match_type"] != "onyomi":
                reading = to_katakana(reading)

            # Apply tags if requested
            if with_tags_def.with_tags:
                match_type = match_info["match_type"]
                if match_type == "onyomi":
                    reading = f"<on>{reading}</on>"
                elif match_type == "kunyomi":
                    reading = f"<kun>{reading}</kun>"
                elif match_type == "jukujikun":
                    reading = f"<juk>{reading}</juk>"

            furigana_parts.append(reading)
            kanji_matches.append({
                "matched_mora": match_info["matched_mora"],
                "match_type": match_info["match_type"],
                "reading_variant": match_info["reading_variant"],
            })
        else:
            # No match found - treat as jukujikun
            furigana_parts.append(mora_sequence)
            kanji_matches.append({
                "matched_mora": mora_sequence,
                "match_type": "jukujikun",
                "reading_variant": "none",
            })

    # Build complete furigana
    complete_furigana = "".join(furigana_parts)

    # Add highlight tags if needed
    if kanji_to_highlight:
        kanji_pos = word.find(kanji_to_highlight)
        if kanji_pos >= 0:
            # Find which furigana portion corresponds to this kanji
            # For simplicity, wrap the corresponding mora portion in <b> tags
            # This would need more sophisticated handling for partial matches
            pass  # TODO: Implement highlight wrapping

    logger.debug(f"process_word_with_mora_alignment - complete_furigana: {complete_furigana}")

    return WordProcessingResult(
        furigana=complete_furigana,
        mora_list=mora_list,
        kanji_matches=kanji_matches,
        was_katakana=was_katakana,
    )
