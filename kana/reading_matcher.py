"""
Reading matcher module for matching kanji readings to mora sequences.

This module handles matching onyomi and kunyomi readings to mora portions,
including special cases like rendaku, small tsu conversion, and vowel changes.
"""

from typing import Optional, Tuple

try:
    from all_types.main_types import ReadingMatchInfo, ReadingType
except ImportError:
    from ..all_types.main_types import ReadingMatchInfo, ReadingType
try:
    from mecab_controller.kana_conv import to_hiragana
except ImportError:
    from ..mecab_controller.kana_conv import to_hiragana
try:
    from regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA
except ImportError:
    from ..regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA
try:
    from all_types.main_types import MatchType, OkuriResults
except ImportError:
    from ..all_types.main_types import MatchType, OkuriResults
try:
    from okuri.check_okurigana_for_inflection import check_okurigana_for_inflection
except ImportError:
    from ..okuri.check_okurigana_for_inflection import check_okurigana_for_inflection
try:
    from okuri.okurigana_dict import ONYOMI_GODAN_SU_FIRST_KANA
except ImportError:
    from ..okuri.okurigana_dict import ONYOMI_GODAN_SU_FIRST_KANA
try:
    from kanji.all_kanji_data import all_kanji_data
except ImportError:
    from ..kanji.all_kanji_data import all_kanji_data
try:
    from okuri.okurigana_dict import get_verb_noun_form_okuri
except ImportError:
    from ..okuri.okurigana_dict import get_verb_noun_form_okuri
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger

# Small tsu conversion possible endings
SMALL_TSU_POSSIBLE_HIRAGANA = ["つ", "ち", "く", "き", "り", "ん", "う"]

# Vowel change dictionary
VOWEL_CHANGE_DICT_HIRAGANA = {
    "お": ["よ", "ょ"],
    "あ": ["や", "ゃ"],
    "う": ["ゆ", "ゅ"],
}

# Yōon contraction mapping (second kana → small yōon)
YOON_SMALL_MAP = {
    "や": "ゃ",
    "ゆ": "ゅ",
    "よ": "ょ",
}


def check_reading_match(
    reading: str,
    mora_string: str,
    okurigana: str = "",
    logger: Logger = Logger("error"),
) -> Tuple[str, ReadingType]:
    """
    Core function to check if a reading matches a mora string, trying various phonetic changes.

    Checks in order:
    1. Plain match
    2. Rendaku (濁点) - first kana voiced (k→g, s→z, etc.)
    3. Small tsu (促音) - last kana becomes っ for certain consonants
    4. Vowel change (拗音化) - first kana vowel change (あ→や, お→よ, う→ゆ)
    5. Combined rendaku + small tsu
    6. う dropped before っ okurigana

    :param reading: The dictionary reading to check
    :param mora_string: The joined mora sequence to match against
    :param okurigana: The okurigana following this reading (for う→っ cases)
    :return: Tuple of (matched_reading, reading_type) or ("", "none") if no match
    """
    if not reading:
        return "", "none"

    # 1. Plain match
    if reading == mora_string:
        return reading, "plain"

    # 2. Rendaku - first kana voiced
    rendaku_readings = []
    if reading[0] in RENDAKU_CONVERSION_DICT_HIRAGANA:
        for kana in RENDAKU_CONVERSION_DICT_HIRAGANA[reading[0]]:
            rendaku_readings.append(f"{kana}{reading[1:]}")

    for rendaku_reading in rendaku_readings:
        if rendaku_reading == mora_string:
            return rendaku_reading, "rendaku"

    # 3. Small tsu - last kana becomes っ
    small_tsu_readings = []
    for kana in SMALL_TSU_POSSIBLE_HIRAGANA:
        if reading[-1] == kana:
            small_tsu_readings.append(f"{reading[:-1]}っ")

    for small_tsu_reading in small_tsu_readings:
        if small_tsu_reading == mora_string:
            return small_tsu_reading, "small_tsu"

    # 4. Vowel change
    vowel_change_readings = []
    if reading[0] in VOWEL_CHANGE_DICT_HIRAGANA:
        for kana in VOWEL_CHANGE_DICT_HIRAGANA[reading[0]]:
            vowel_change_readings.append(f"{kana}{reading[1:]}")

    for vowel_change_reading in vowel_change_readings:
        if vowel_change_reading == mora_string:
            return vowel_change_reading, "vowel_change"

    # 5. Yōon contraction: reading like しよ → しょ, きや → きゃ, etc.
    # Check direct contraction
    if len(reading) >= 2 and reading[1] in YOON_SMALL_MAP:
        yoon_contracted = f"{reading[0]}{YOON_SMALL_MAP[reading[1]]}{reading[2:]}"
        if yoon_contracted == mora_string:
            return yoon_contracted, "vowel_change"

    # Also try yōon contraction on rendaku variants of the first kana
    for rendaku_reading in rendaku_readings:
        if len(rendaku_reading) >= 2 and rendaku_reading[1] in YOON_SMALL_MAP:
            yoon_rendaku = (
                f"{rendaku_reading[0]}{YOON_SMALL_MAP[rendaku_reading[1]]}{rendaku_reading[2:]}"
            )
            if yoon_rendaku == mora_string:
                return yoon_rendaku, "vowel_change"

    # 6. Combined rendaku + small tsu
    rendaku_small_tsu_readings = []
    for rendaku_reading in rendaku_readings:
        for kana in SMALL_TSU_POSSIBLE_HIRAGANA:
            if rendaku_reading[-1] == kana:
                rendaku_small_tsu_readings.append(f"{rendaku_reading[:-1]}っ")

    for combined_reading in rendaku_small_tsu_readings:
        if combined_reading == mora_string:
            return combined_reading, "rendaku_small_tsu"

    # 7. う dropped before っ okurigana (e.g., 言う[いう]って → い + って)
    if okurigana and okurigana[0] == "っ" and reading[-1] == "う":
        u_dropped = reading[:-1]
        if u_dropped == mora_string:
            return u_dropped, "small_tsu"
        # Also try with rendaku
        for rendaku_reading in rendaku_readings:
            if rendaku_reading[-1] == "う":
                u_dropped_rendaku = rendaku_reading[:-1]
                if u_dropped_rendaku == mora_string:
                    return u_dropped_rendaku, "rendaku"

    return "", "none"


def match_onyomi_to_mora(
    kanji: str,
    mora_sequence: str,
    kanji_data: dict,
    okurigana: str,
    is_last_kanji: bool,
    logger: Logger = Logger("error"),
) -> Optional[ReadingMatchInfo]:
    """
    Try to match onyomi readings to a mora sequence.

    :param kanji: The kanji character to match
    :param mora_sequence: Joined mora string to match against
    :param kanji_data: Dictionary containing onyomi/kunyomi data for this kanji
    :param okurigana: The okurigana following the word (used for last kanji okurigana extraction)
    :param is_last_kanji: Whether this is the last kanji in the word
    :return: ReadingMatchInfo if match found, None otherwise
    """
    onyomi = kanji_data.get("onyomi", "")
    if not onyomi:
        return None

    # Parse onyomi readings
    onyomi_readings = [r.strip() for r in onyomi.split("、")]

    for onyomi_reading in onyomi_readings:
        # Remove parentheses content
        onyomi_reading = onyomi_reading.split("(")[0].strip()
        if not onyomi_reading:
            continue

        # Convert to hiragana for matching
        reading_hiragana = to_hiragana(onyomi_reading)

        # Try to match
        matched_reading, reading_variant = check_reading_match(
            reading_hiragana,
            mora_sequence,
            okurigana if is_last_kanji else "",
        )

        if matched_reading:
            # For now, set okurigana/rest_kana to empty (will be extracted in step 4)
            return ReadingMatchInfo(
                reading=matched_reading,
                dict_form=onyomi_reading,  # Store original reading
                match_type="onyomi",
                reading_variant=reading_variant,
                matched_mora=mora_sequence,
                kanji=kanji,
                okurigana="",
                rest_kana="",
            )

    return None


def match_kunyomi_to_mora(
    kanji: str,
    mora_sequence: str,
    kanji_data: dict,
    okurigana: str,
    is_last_kanji: bool,
    logger: Logger = Logger("error"),
) -> Optional[ReadingMatchInfo]:
    """
    Try to match kunyomi readings to a mora sequence.

    For kunyomi, extracts the stem (portion before ".") and matches it.
    Also tries noun form variants (e.g., ひ.く → ひき) for compounds.
    The dict_form field preserves the original reading with okurigana marker.

    :param kanji: The kanji character to match
    :param mora_sequence: Joined mora string to match against
    :param kanji_data: Dictionary containing onyomi/kunyomi data for this kanji
    :param okurigana: The okurigana following the word (used for last kanji okurigana extraction)
    :param is_last_kanji: Whether this is the last kanji in the word
    :return: ReadingMatchInfo if match found, None otherwise
    """

    kunyomi = kanji_data.get("kunyomi", "")
    if not kunyomi:
        return None

    # Special handling for 為 (する verb) - add conjugated stems し and さ
    # These are conjugated forms of す.る that should match as kunyomi
    if kanji == "為" and mora_sequence in ["し", "さ"]:
        # Treat these as stems of す.る
        return ReadingMatchInfo(
            reading=mora_sequence,
            dict_form="す.る",
            match_type="kunyomi",
            reading_variant="plain",
            matched_mora=mora_sequence,
            kanji=kanji,
            okurigana="",
            rest_kana="",
        )

    # Parse kunyomi readings
    kunyomi_readings = [r.strip() for r in kunyomi.split("、")]

    # When this is the last kanji and okurigana is present, prefer readings whose
    # okurigana marker best matches the remaining kana. Collect candidates and pick best.
    best_candidate: Optional[ReadingMatchInfo] = None
    best_candidate_score: int = -1

    for kunyomi_reading in kunyomi_readings:
        # Remove parentheses content
        kunyomi_reading = kunyomi_reading.split("(")[0].strip()
        if not kunyomi_reading:
            continue

        # Extract stem (portion before "." marker)
        if "." in kunyomi_reading:
            stem = kunyomi_reading.split(".")[0]
            dict_form_okuri = kunyomi_reading.split(".")[1]
            # Also extract full reading (without dot) for cases without okurigana
            full_reading = kunyomi_reading.replace(".", "")
        else:
            stem = kunyomi_reading
            dict_form_okuri = ""
            full_reading = kunyomi_reading

        # Build list of readings to try (in priority order)
        readings_to_try = []

        # 1. Try stem first (e.g., "ひ" from "ひ.く")
        readings_to_try.append((stem, "plain", kunyomi_reading))

        # 2. If the reading has okurigana, try noun form variants
        # (e.g., "ひき" is the noun form of "ひ.く" where く→き)
        # This applies to both middle and last kanji (for compound noun forms like 書留)
        if dict_form_okuri:
            # Get noun form okurigana
            noun_form_okuri = get_verb_noun_form_okuri(dict_form_okuri, kanji, kunyomi_reading)
            if noun_form_okuri:
                noun_form_reading = f"{stem}{noun_form_okuri}"
                if noun_form_reading != full_reading:
                    readings_to_try.append((noun_form_reading, "plain", kunyomi_reading))

        # 3. Try full reading if not already tried (e.g., "ひく" from "ひ.く")
        if full_reading != stem and full_reading not in [r[0] for r in readings_to_try]:
            readings_to_try.append((full_reading, "plain", kunyomi_reading))

        # Try to match each reading variant
        for reading_to_match, base_variant, original_reading in readings_to_try:
            matched_reading, reading_variant = check_reading_match(
                reading_to_match,
                mora_sequence,
                okurigana if is_last_kanji else "",
            )

            if matched_reading:
                candidate = ReadingMatchInfo(
                    reading=matched_reading,
                    dict_form=original_reading,
                    match_type="kunyomi",
                    reading_variant=reading_variant if reading_variant != "none" else base_variant,
                    matched_mora=mora_sequence,
                    kanji=kanji,
                    okurigana="",
                    rest_kana="",
                )
                # If we are at the last kanji and have okurigana to match, score this candidate
                if is_last_kanji and okurigana:
                    # If this reading has an okurigana marker, check how well it matches
                    if "." in original_reading:
                        reading_okurigana = original_reading.split(".", 1)[1]
                        # Minimal word_data/highlight_args for scoring
                        word_data = {
                            "okurigana": okurigana,
                            "word": kanji,
                            "kanji_pos": 0,
                            "kanji_count": 1,
                            "furigana": "",
                            "furigana_is_katakana": False,
                            "edge": "whole",
                        }
                        highlight_args = {
                            "onyomi": "",
                            "kunyomi": original_reading,
                            "kanji_to_match": kanji,
                            "kanji_to_highlight": kanji,
                            "add_highlight": False,
                            "edge": "whole",
                            "full_word": kanji,
                            "full_furigana": "",
                        }
                        res = check_okurigana_for_inflection(
                            reading_okurigana=reading_okurigana,
                            reading=original_reading,
                            word_data=word_data,
                            highlight_args=highlight_args,
                        )
                        # Score by length of matched okuri (prefer full matches)
                        score = len(res.okurigana)
                        if res.result == "full_okuri":
                            # Perfect match, return immediately
                            return candidate
                        if score > best_candidate_score:
                            best_candidate = candidate
                            best_candidate_score = score
                        # Continue checking other readings to find a better match
                        continue
                else:
                    # Not last kanji or no okurigana to match, return first found
                    return candidate
                # If not scoring or no okurigana marker, fall back to first matched candidate
                if best_candidate is None:
                    best_candidate = candidate
                    best_candidate_score = max(best_candidate_score, 0)

    return best_candidate


def match_reading_to_mora(
    kanji: str,
    mora_sequence: str,
    kanji_data: dict,
    okurigana: str,
    is_last_kanji: bool,
    prefer_kunyomi: bool = False,
    logger: Logger = Logger("error"),
) -> Optional[ReadingMatchInfo]:
    """
    Try to match any reading (onyomi or kunyomi) to a mora sequence.

    Tries onyomi first, then kunyomi unless prefer_kunyomi is True.

    :param kanji: The kanji character to match
    :param mora_sequence: Joined mora string to match against
    :param kanji_data: Dictionary containing onyomi/kunyomi data for this kanji
    :param okurigana: The okurigana following the word (used for last kanji okurigana extraction)
    :param is_last_kanji: Whether this is the last kanji in the word
    :param prefer_kunyomi: Whether to prefer kunyomi first (overrides default logic)
    :return: ReadingMatchInfo if match found, None otherwise
    """
    if prefer_kunyomi:
        # Try kunyomi first when okurigana is present and kunyomi is more likely
        kunyomi_match = match_kunyomi_to_mora(
            kanji, mora_sequence, kanji_data, okurigana, is_last_kanji, logger
        )
        if kunyomi_match:
            return kunyomi_match

        onyomi_match = match_onyomi_to_mora(
            kanji, mora_sequence, kanji_data, okurigana, is_last_kanji, logger
        )
        if onyomi_match:
            return onyomi_match
    else:
        # Default order: onyomi then kunyomi
        onyomi_match = match_onyomi_to_mora(
            kanji, mora_sequence, kanji_data, okurigana, is_last_kanji, logger
        )
        if onyomi_match:
            return onyomi_match

        kunyomi_match = match_kunyomi_to_mora(
            kanji, mora_sequence, kanji_data, okurigana, is_last_kanji, logger
        )
        if kunyomi_match:
            return kunyomi_match

    return None


def extract_okurigana_for_match(
    match_type: MatchType,
    dict_form: str,
    remaining_kana: str,
    kanji: str,
    logger: Logger = Logger("error"),
) -> Tuple[str, str]:
    """
    Extract okurigana from remaining kana after the last kanji's reading match.

    This function handles okurigana extraction for both onyomi and kunyomi readings
    when they appear at the end of a word (last kanji).

    :param match_type: Whether this is an onyomi or kunyomi match
    :param dict_form: The dictionary form reading (for kunyomi, includes "." marker like "か.く")
    :param remaining_kana: The kana following the matched reading
    :param kanji: The kanji character this match is for
    :return: Tuple of (okurigana, rest_kana)
    """
    logger.debug(
        f"extract_okurigana_for_match - match_type: {match_type}, dict_form: {dict_form}, "
        f"remaining_kana: {remaining_kana}, kanji: {kanji}"
    )
    if not remaining_kana:
        return "", ""

    # Use the check_okurigana_for_inflection function to match against inflections
    # Create minimal word_data and highlight_args for the function
    word_data = {
        "okurigana": remaining_kana,
        "word": kanji,
        "kanji_pos": 0,
        "kanji_count": 1,
        "furigana": "",
        "furigana_is_katakana": False,
        "edge": "whole",
    }
    highlight_args = {
        "kanji_to_match": kanji,
        "kanji_to_highlight": kanji,
        "add_highlight": False,
        "edge": "whole",
        "full_word": kanji,
        "full_furigana": "",
    }

    if match_type == "onyomi":
        highlight_args["onyomi"] = dict_form
        highlight_args["kunyomi"] = ""
        # Check for godan su verbs that have okurigana
        if remaining_kana and remaining_kana[0] in ONYOMI_GODAN_SU_FIRST_KANA:
            if remaining_kana.startswith("する"):
                # If this is just a straight up suru verb, we can take okurigana up to する
                logger.debug(
                    "extract_okurigana_for_match - onyomi match found with する okurigana:"
                    f" word_data: {remaining_kana}, kanji: {kanji}"
                )
                return "する", remaining_kana[2:]
            else:
                logger.debug(
                    "extract_okurigana_for_match - onyomi match found with godan す verb okurigana:"
                    f" word_data: {remaining_kana}, kanji: {kanji}"
                )
                # onyomi godan verbs are always す verbs, e.g 呈す, 博す and have almost the same
                # inflection as する but not quite, so check both possiblities and pick the one that
                # matches the most of the okurigana
                inflection_results: list[OkuriResults] = []
                inflection_results.append(
                    check_okurigana_for_inflection(
                        reading_okurigana="す",
                        reading=dict_form,
                        word_data=word_data,
                        highlight_args=highlight_args,
                        logger=logger,
                    )
                )
                # In order to check for する, we need override the part_of_speech to check for
                # vs (normal suru) inflections
                inflection_results.append(
                    check_okurigana_for_inflection(
                        reading_okurigana="る",
                        reading=dict_form,
                        word_data=word_data,
                        highlight_args=highlight_args,
                        part_of_speech="vs",
                        logger=logger,
                    )
                )
                # Pick the longest okurigana match
                res = max(inflection_results, key=lambda x: len(x.okurigana))
                logger.debug(
                    f"extract_okurigana_for_match - check_okurigana_for_inflection result: {res}"
                )
                if res.result != "no_okuri":
                    return res.okurigana, res.rest_kana
                else:
                    # If there is no okurigana, we just return empty
                    return "", remaining_kana

        # No okurigana for other onyomi cases
        return "", remaining_kana

    elif match_type == "kunyomi":
        # For kunyomi, extract the okurigana marker portion from dict_form
        # e.g., "か.く" → reading_okurigana = "く"
        if "." in dict_form:
            reading_okurigana = dict_form.split(".", 1)[1]
            dict_form_to_use = dict_form
        else:
            # No okurigana marker in dict_form, but we have remaining_kana
            # This happens when a kunyomi without okurigana marker was matched first
            # (e.g., "みず" matched before "みず.しい" for repeater kanji)
            # Try to find an alternative reading with okurigana marker that matches

            kanji_data = all_kanji_data.get(kanji, {})
            kunyomi = kanji_data.get("kunyomi", "")

            if kunyomi:
                kunyomi_readings = [r.strip() for r in kunyomi.split("、")]
                # Look for readings with okurigana markers
                for reading in kunyomi_readings:
                    reading = reading.split("(")[0].strip()
                    if "." in reading:
                        stem = reading.split(".")[0]
                        # Check if this reading's stem matches the dict_form we have
                        # For repeater kanji, dict_form might be just the stem
                        if dict_form == stem or dict_form == reading.replace(".", ""):
                            # Found a reading with okurigana marker that has the same stem
                            reading_okurigana = reading.split(".", 1)[1]
                            dict_form_to_use = reading
                            break
                else:
                    # No reading with okurigana marker found
                    return "", remaining_kana
            else:
                return "", remaining_kana

        highlight_args["onyomi"] = ""
        highlight_args["kunyomi"] = dict_form_to_use

        result = check_okurigana_for_inflection(
            reading_okurigana=reading_okurigana,
            reading=dict_form_to_use,
            word_data=word_data,
            highlight_args=highlight_args,
            logger=logger,
        )

        return result.okurigana, result.rest_kana

    # For jukujikun or unmatched, return empty okurigana
    return "", remaining_kana
