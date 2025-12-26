"""
Reading matcher module for matching kanji readings to mora sequences.

This module handles matching onyomi and kunyomi readings to mora portions,
including special cases like rendaku, small tsu conversion, and vowel changes.
"""

from typing import Callable, Optional, Tuple

try:
    from all_types.main_types import (
        ReadingMatchInfo,
        ReadingType,
        KunyomiReadingToTry,
        KanjiData,
        KanjiReadingData,
    )
except ImportError:
    from ..all_types.main_types import (
        ReadingMatchInfo,
        ReadingType,
        KunyomiReadingToTry,
        KanjiData,
        KanjiReadingData,
    )
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
    cache_func: Optional[Callable[[str], None]] = None,
    logger: Logger = Logger("error"),
) -> Optional[Tuple[str, ReadingType]]:
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
    :param cache_func: Optional function to store cached results, instead of returning matches
    :return: Tuple of (matched_reading, reading_type) or ("", "none") if no match
    """
    if not reading:
        if cache_func:
            # Nothing to cache
            return None
        return "", "none"

    # 1. Plain match
    if cache_func:
        cache_func(reading, "plain")
    elif reading == mora_string:
        return reading, "plain"

    # 2. Rendaku - first kana voiced
    rendaku_readings = []
    if reading[0] in RENDAKU_CONVERSION_DICT_HIRAGANA:
        for kana in RENDAKU_CONVERSION_DICT_HIRAGANA[reading[0]]:
            rendaku_readings.append(f"{kana}{reading[1:]}")

    for rendaku_reading in rendaku_readings:
        if cache_func:
            cache_func(rendaku_reading, "rendaku")
        elif rendaku_reading == mora_string:
            return rendaku_reading, "rendaku"

    # 3. Small tsu - last kana becomes っ
    small_tsu_readings = []
    for kana in SMALL_TSU_POSSIBLE_HIRAGANA:
        if reading[-1] == kana:
            small_tsu_readings.append(f"{reading[:-1]}っ")

    for small_tsu_reading in small_tsu_readings:
        if cache_func:
            cache_func(small_tsu_reading, "small_tsu")
        elif small_tsu_reading == mora_string:
            return small_tsu_reading, "small_tsu"

    # 4. Vowel change
    vowel_change_readings = []
    if reading[0] in VOWEL_CHANGE_DICT_HIRAGANA:
        for kana in VOWEL_CHANGE_DICT_HIRAGANA[reading[0]]:
            vowel_change_readings.append(f"{kana}{reading[1:]}")

    for vowel_change_reading in vowel_change_readings:
        if cache_func:
            cache_func(vowel_change_reading, "vowel_change")
        elif vowel_change_reading == mora_string:
            return vowel_change_reading, "vowel_change"

    # 5. Yōon contraction: reading like しよ → しょ, きや → きゃ, etc.
    # Check direct contraction
    if len(reading) >= 2 and reading[1] in YOON_SMALL_MAP:
        yoon_contracted = f"{reading[0]}{YOON_SMALL_MAP[reading[1]]}{reading[2:]}"
        if cache_func:
            cache_func(yoon_contracted, "vowel_change")
        elif yoon_contracted == mora_string:
            return yoon_contracted, "vowel_change"

    # Also try yōon contraction on rendaku variants of the first kana
    for rendaku_reading in rendaku_readings:
        if len(rendaku_reading) >= 2 and rendaku_reading[1] in YOON_SMALL_MAP:
            yoon_rendaku = (
                f"{rendaku_reading[0]}{YOON_SMALL_MAP[rendaku_reading[1]]}{rendaku_reading[2:]}"
            )
            if cache_func:
                cache_func(yoon_rendaku, "vowel_change")
            elif yoon_rendaku == mora_string:
                return yoon_rendaku, "vowel_change"

    # 6. Combined rendaku + small tsu
    rendaku_small_tsu_readings = []
    for rendaku_reading in rendaku_readings:
        for kana in SMALL_TSU_POSSIBLE_HIRAGANA:
            if rendaku_reading[-1] == kana:
                rendaku_small_tsu_readings.append(f"{rendaku_reading[:-1]}っ")

    for combined_reading in rendaku_small_tsu_readings:
        if cache_func:
            cache_func(combined_reading, "rendaku_small_tsu")
        elif combined_reading == mora_string:
            return combined_reading, "rendaku_small_tsu"

    # 7. う dropped before っ okurigana (e.g., 言う[いう]って → い + って)
    if okurigana and okurigana[0] == "っ" and reading[-1] == "う":
        u_dropped = reading[:-1]
        if cache_func:
            cache_func(u_dropped, "u_dropped")
        elif u_dropped == mora_string:
            return u_dropped, "u_dropped"
        # Also try with rendaku
        for rendaku_reading in rendaku_readings:
            if rendaku_reading[-1] == "う":
                u_dropped_rendaku = rendaku_reading[:-1]
                if cache_func:
                    cache_func(u_dropped_rendaku, "u_dropped")
                elif u_dropped_rendaku == mora_string:
                    return u_dropped_rendaku, "u_dropped"

    if cache_func:
        # Nothing matched, but we were caching
        return None
    return "", "none"


def get_onyomi_reading_hiragana(
    onyomi_reading: str, logger: Logger = Logger("error")
) -> Tuple[str, str]:
    """
    Generate hiragana reading variant for a given onyomi reading.

    :param onyomi_reading: The original onyomi reading
    :return: Hiragana reading variant
    """
    if not onyomi_reading:
        return ""
    # Remove parentheses content
    try:
        onyomi_reading = onyomi_reading.split("(")[0].strip()
    except Exception:
        logger.error(f"get_onyomi_reading_variants - invalid onyomi_reading: {onyomi_reading}")
        return ""
    if not onyomi_reading:
        return ""

    # Convert to hiragana for matching
    reading_hiragana = to_hiragana(onyomi_reading)

    return reading_hiragana


def match_onyomi_to_mora(
    kanji: str,
    mora_sequence: str,
    okurigana: str,
    is_last_kanji: bool,
    kanji_data: Optional[KanjiData] = None,
    kanji_reading_data: Optional[KanjiReadingData] = None,
    logger: Logger = Logger("error"),
) -> Optional[ReadingMatchInfo]:
    """
    Try to match onyomi readings to a mora sequence.

    :param kanji: The kanji character to match
    :param mora_sequence: Joined mora string to match against
    :param okurigana: The okurigana following the word (used for last kanji okurigana extraction)
    :param is_last_kanji: Whether this is the last kanji in the word
    :param kanji_data: Optional dict containing onyomi/kunyomi data for this kanji, either this
        or kanji_reading_data must be provided
    :param kanji_reading_data: Optional cached kunyomi reading dict for this kanji, either this or
        kanji_data must be provided
    :return: ReadingMatchInfo if match found, None otherwise
    """

    onyomi = kanji_data.get("onyomi", "") if kanji_data else ""
    onyomi_reading_data = kanji_reading_data.get("onyomi", None) if kanji_reading_data else None
    if not onyomi and not onyomi_reading_data:
        return None

    if onyomi_reading_data:
        # Try cached onyomi readings, if given. When okurigana starts with っ we may
        # have both a normal entry and a _u_dropped variant; check both.
        mora_keys = [mora_sequence]
        if okurigana and okurigana[0] == "っ":
            mora_keys.insert(0, f"{mora_sequence}_u_dropped")

        for mora_key in mora_keys:
            if mora_key in onyomi_reading_data:
                original_reading, reading_variant = onyomi_reading_data[mora_key]
                return ReadingMatchInfo(
                    reading=mora_sequence,
                    dict_form=original_reading,  # Store original reading
                    match_type="onyomi",
                    reading_variant=reading_variant,
                    matched_mora=mora_sequence,
                    kanji=kanji,
                    okurigana="",
                    rest_kana="",
                )

        return None

    # Parse onyomi readings
    onyomi_readings = [r.strip() for r in onyomi.split("、")]

    for onyomi_reading in onyomi_readings:
        reading_hiragana = get_onyomi_reading_hiragana(onyomi_reading, logger=logger)
        if not reading_hiragana:
            continue

        # Try to match
        matched_reading, reading_variant = check_reading_match(
            reading_hiragana,
            mora_sequence,
            okurigana if is_last_kanji else "",
            logger=logger,
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


def get_kunyomi_reading_variants(
    kunyomi_reading: str, kanji: str, logger: Logger = Logger("error")
) -> list[KunyomiReadingToTry]:
    """
    Generate reading variants for a given kunyomi reading.

    This includes the base reading (stem) and noun form variants if applicable.

    :param kunyomi_reading: The original kunyomi reading (may include okurigana marker)
    :param kanji: The kanji character this reading is for
    :return: List of tuples (reading_to_match, base_variant, original_reading)
    """
    if not kunyomi_reading:
        return []
    # Remove parentheses content
    try:
        kunyomi_reading = kunyomi_reading.split("(")[0].strip()
    except Exception:
        logger.error(f"get_kunyomi_reading_variants - invalid kunyomi_reading: {kunyomi_reading}")
        return []
    if not kunyomi_reading:
        return []

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
    readings_to_try: list[KunyomiReadingToTry] = []

    # 1. Try stem first (e.g., "ひ" from "ひ.く")
    readings_to_try.append(KunyomiReadingToTry(stem, "plain", kunyomi_reading))

    # 2. If the reading has okurigana, try noun form variants
    # (e.g., "ひき" is the noun form of "ひ.く" where く→き)
    # This applies to both middle and last kanji (for compound noun forms like 書留)
    if dict_form_okuri:
        # Get noun form okurigana
        noun_form_okuri = get_verb_noun_form_okuri(dict_form_okuri, kanji, kunyomi_reading)
        if noun_form_okuri:
            noun_form_reading = f"{stem}{noun_form_okuri}"
            if noun_form_reading != full_reading:
                readings_to_try.append(
                    KunyomiReadingToTry(noun_form_reading, "plain", kunyomi_reading)
                )

    # 3. Try full reading if not already tried (e.g., "ひく" from "ひ.く")
    if full_reading != stem and full_reading not in [r.reading_to_match for r in readings_to_try]:
        readings_to_try.append(KunyomiReadingToTry(full_reading, "plain", kunyomi_reading))

    return readings_to_try


def match_kunyomi_to_mora(
    kanji: str,
    mora_sequence: str,
    okurigana: str,
    is_last_kanji: bool,
    kanji_data: Optional[KanjiData] = None,
    kanji_reading_data: Optional[KanjiReadingData] = None,
    logger: Logger = Logger("error"),
) -> Optional[ReadingMatchInfo]:
    """
    Try to match kunyomi readings to a mora sequence.

    For kunyomi, extracts the stem (portion before ".") and matches it.
    Also tries noun form variants (e.g., ひ.く → ひき) for compounds.
    The dict_form field preserves the original reading with okurigana marker.

    :param kanji: The kanji character to match
    :param mora_sequence: Joined mora string to match against
    :param okurigana: The okurigana following the word (used for last kanji okurigana extraction)
    :param is_last_kanji: Whether this is the last kanji in the word
    :param kanji_data: Optional dict containing onyomi/kunyomi data for this kanji, either this
        or kanji_reading_data must be provided
    :param kanji_reading_data: Optional cached kunyomi reading dict for this kanji, either this or
        kanji_data must be provided
    :return: ReadingMatchInfo if match found, None otherwise
    """

    kunyomi = kanji_data.get("kunyomi", "") if kanji_data else ""
    kunyomi_reading_data = kanji_reading_data.get("kunyomi", None) if kanji_reading_data else None
    if not kunyomi and not kunyomi_reading_data:
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

    # When this is the last kanji and okurigana is present, prefer readings whose
    # okurigana marker best matches the remaining kana. Collect candidates and pick best.
    best_candidate: Optional[ReadingMatchInfo] = None
    best_candidate_score: int = -1

    def process_candidate(
        matched_reading: str,
        reading_variant: str,
        original_reading: str,
    ) -> Optional[ReadingMatchInfo]:
        nonlocal best_candidate, best_candidate_score
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
                    logger=logger,
                )
                # Score by length of matched okuri (prefer full matches)
                score = len(res.okurigana)
                if res.result == "full_okuri":
                    # Perfect match, return immediately
                    return candidate
                if score > best_candidate_score:
                    best_candidate = candidate
                    best_candidate_score = score
                # Return None to continue processing other candidates
                return None
        else:
            # If not last kanji or no okurigana to match, return first found
            return candidate
        if best_candidate is None:
            # If not scoring or no okurigana marker, fall back to first matched candidate
            best_candidate = candidate
            best_candidate_score = max(best_candidate_score, 0)
        return None

    # Try cached kunyomi readings, if given
    if kunyomi_reading_data:
        # Try cached kunyomi readings. Check both the base key and the _u_dropped
        # variant for okurigana that starts with っ so regular stems still match.
        mora_keys = [mora_sequence]
        if okurigana and okurigana[0] == "っ":
            mora_keys.insert(0, f"{mora_sequence}_u_dropped")

        for mora_key in mora_keys:
            if mora_key in kunyomi_reading_data:
                candidate_data: list[list[str, ReadingType]] = kunyomi_reading_data[mora_key]
                for original_reading, reading_variant in candidate_data:
                    candidate = process_candidate(mora_sequence, reading_variant, original_reading)
                    if candidate:
                        return candidate

        # If cached lookup didn't produce a result and we have kanji_data, fall back to non-cached
        if best_candidate:
            return best_candidate
        return None

    # Parse kunyomi readings
    kunyomi_readings = [r.strip() for r in kunyomi.split("、")]
    for kunyomi_reading in kunyomi_readings:
        readings_to_try = get_kunyomi_reading_variants(kunyomi_reading, kanji, logger=logger)
        # Try to match each reading variant
        for reading_to_match, base_variant, original_reading in readings_to_try:
            matched_reading, reading_variant = check_reading_match(
                reading_to_match,
                mora_sequence,
                okurigana if is_last_kanji else "",
                logger=logger,
            )

            if matched_reading:
                candidate = process_candidate(matched_reading, reading_variant, original_reading)
                if candidate:
                    return candidate

    return best_candidate


def match_reading_to_mora(
    kanji: str,
    mora_sequence: str,
    okurigana: str,
    is_last_kanji: bool,
    prefer_kunyomi: bool = False,
    kanji_data: Optional[KanjiData] = None,
    kanji_reading_data: Optional[KanjiReadingData] = None,
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
            kanji=kanji,
            mora_sequence=mora_sequence,
            okurigana=okurigana,
            is_last_kanji=is_last_kanji,
            kanji_data=kanji_data,
            kanji_reading_data=kanji_reading_data,
            logger=logger,
        )
        if kunyomi_match:
            return kunyomi_match

        onyomi_match = match_onyomi_to_mora(
            kanji=kanji,
            mora_sequence=mora_sequence,
            okurigana=okurigana,
            is_last_kanji=is_last_kanji,
            kanji_data=kanji_data,
            kanji_reading_data=kanji_reading_data,
            logger=logger,
        )
        if onyomi_match:
            return onyomi_match
    else:
        # Default order: onyomi then kunyomi
        onyomi_match = match_onyomi_to_mora(
            kanji=kanji,
            mora_sequence=mora_sequence,
            okurigana=okurigana,
            is_last_kanji=is_last_kanji,
            kanji_data=kanji_data,
            kanji_reading_data=kanji_reading_data,
            logger=logger,
        )
        if onyomi_match:
            return onyomi_match

        kunyomi_match = match_kunyomi_to_mora(
            kanji=kanji,
            mora_sequence=mora_sequence,
            okurigana=okurigana,
            is_last_kanji=is_last_kanji,
            kanji_data=kanji_data,
            kanji_reading_data=kanji_reading_data,
            logger=logger,
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
