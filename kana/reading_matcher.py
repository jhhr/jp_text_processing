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
    from okuri.check_okurigana_for_inflection import check_okurigana_for_inflection
except ImportError:
    from ..okuri.check_okurigana_for_inflection import check_okurigana_for_inflection
try:
    from okuri.okurigana_dict import get_verb_noun_form_okuri
except ImportError:
    from ..okuri.okurigana_dict import get_verb_noun_form_okuri
try:
    from okuri.get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab
except ImportError:
    from ..okuri.get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab
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

# Kana that can change to 'ん' if a reading ends with it
N_CHANGE_HIRAGANA = {
    "の",  # e.g. もの -> もん
    "に",  # e.g. なに -> なん
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
    5. Yōon contraction (e.g., しよ → しょ)
    6. Combined rendaku + small tsu
    7. う dropped before っ okurigana
    8. Kana that can change to 'ん' if a reading ends with it
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

    # 8. Kana that can change to 'ん' if a reading ends with it
    if reading[-1] in N_CHANGE_HIRAGANA:
        n_changed = f"{reading[:-1]}ん"
        if n_changed == mora_string:
            return n_changed, "n_change"

    return "", "none"


def match_onyomi_to_mora(
    kanji: str,
    word: str,
    furigana: str,
    mora_sequence: str,
    kanji_data: dict,
    maybe_okuri: str,
    is_last_kanji: bool,
    logger: Logger = Logger("error"),
) -> Optional[ReadingMatchInfo]:
    """
    Try to match onyomi readings to a mora sequence.

    :param kanji: The kanji character to match
    :param word: The full word containing the kanji, needed for okurigana extraction with mecab
    :param furigana: The full reading of the word in kana, needed for okurigana extraction with mecab
    :param mora_sequence: Joined mora string to match against
    :param kanji_data: Dictionary containing onyomi/kunyomi data for this kanji
    :param maybe_okuri: The kana following the word (used for last kanji okurigana extraction)
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
            maybe_okuri if is_last_kanji else "",
        )
        if matched_reading:
            # Get okurigana with mecab since onyomi readings don't have okurigana markers
            okuri_result, is_noun_suru_verb = get_conjugated_okuri_with_mecab(
                word=word,
                reading=furigana,
                maybe_okuri=maybe_okuri,
                okuri_prefix="word",
                logger=logger,
            )
            return ReadingMatchInfo(
                reading=matched_reading,
                dict_form=onyomi_reading,  # Store original reading
                match_type="onyomi",
                reading_variant=reading_variant,
                matched_mora=mora_sequence,
                kanji=kanji,
                okurigana=okuri_result.okurigana,
                rest_kana=okuri_result.rest_kana,
                is_noun_suru_verb=is_noun_suru_verb,
            )

    return None


def match_kunyomi_to_mora(
    kanji: str,
    mora_sequence: str,
    kanji_data: dict,
    maybe_okuri: str,
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
    :param maybe_okuri: The kana following the word (used for last kanji okurigana extraction)
    :param is_last_kanji: Whether this is the last kanji in the word
    :return: ReadingMatchInfo if match found, None otherwise
    """

    kunyomi = kanji_data.get("kunyomi", "")
    logger.debug(
        f"match_kunyomi_to_mora - kanji: {kanji}, mora_sequence: {mora_sequence}, "
        f"okurigana: {maybe_okuri}, is_last_kanji: {is_last_kanji}, kunyomi: {kunyomi}"
    )
    if not kunyomi:
        return None

    # Special handling for 為 (する verb) - add conjugated stems し and さ
    # These are conjugated forms of す.る that should match as kunyomi
    if kanji == "為" and mora_sequence in ["し", "さ", "せ"]:
        logger.debug(f"match_kunyomi_to_mora - special 為 handling for: '{mora_sequence}'")
        # Treat these as stems of す.る
        match_info = ReadingMatchInfo(
            reading=mora_sequence,
            dict_form="す.る",
            match_type="kunyomi",
            reading_variant="plain",
            matched_mora=mora_sequence,
            kanji=kanji,
            okurigana="",
            rest_kana=maybe_okuri,
        )
        if maybe_okuri:
            # If there's okurigana, check it
            res = check_okurigana_for_inflection(
                reading_okurigana="る",
                reading="す.る",
                maybe_okuri=maybe_okuri,
                kanji_to_match=kanji,
                logger=logger,
            )
            logger.debug(f"match_kunyomi_to_mora - special 為 okurigana check result: {res}")
            match_info["okurigana"] = res.okurigana
            match_info["rest_kana"] = res.rest_kana
        return match_info

    # Parse kunyomi readings
    kunyomi_readings = [r.strip() for r in kunyomi.split("、")]

    # When okurigana is present, prefer readings whose okurigana marker best matches the remaining
    # kana. Collect candidates and pick best.
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
                maybe_okuri if is_last_kanji else "",
            )

            if matched_reading:
                candidate = ReadingMatchInfo(
                    reading=matched_reading,
                    dict_form=original_reading,
                    match_type="kunyomi",
                    reading_variant=reading_variant if reading_variant != "none" else base_variant,
                    matched_mora=mora_sequence,
                    kanji=kanji,
                    # Initially we assume there's no okurigana; will adjust below if needed
                    okurigana="",
                    rest_kana=maybe_okuri,
                )
                if not maybe_okuri:
                    # No okurigana to match, return first found
                    return candidate
                else:
                    # If we were given okurigana to match, score this candidate
                    # If this reading has an okurigana marker, check how well it matches
                    if "." in original_reading:
                        reading_okurigana = original_reading.split(".", 1)[1]
                        res = check_okurigana_for_inflection(
                            reading_okurigana=reading_okurigana,
                            reading=original_reading,
                            maybe_okuri=maybe_okuri,
                            kanji_to_match=kanji,
                        )
                        # Set okurigana/rest_kana in candidate
                        candidate["okurigana"] = res.okurigana
                        candidate["rest_kana"] = res.rest_kana
                        logger.debug(
                            f"match_kunyomi_to_mora - scoring candidate: {candidate}, "
                            f"okurigana match result: {res}"
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
                # If not scoring or no okurigana marker, fall back to first matched candidate
                if best_candidate is None:
                    best_candidate = candidate
                    best_candidate_score = max(best_candidate_score, 0)

    return best_candidate


def match_reading_to_mora(
    kanji: str,
    word: str,
    furigana: str,
    mora_sequence: str,
    kanji_data: dict,
    maybe_okuri: str,
    is_last_kanji: bool,
    logger: Logger = Logger("error"),
) -> Tuple[Optional[ReadingMatchInfo], Optional[ReadingMatchInfo]]:
    """
    Try to match any reading (onyomi or kunyomi) to a mora sequence.

    Returns both kunyomi and onyomi matches as a tuple.
    When maybe_okuri is present, both are checked.
    When no maybe_okuri, onyomi is checked first for performance.

    :param kanji: The kanji character to match
    :param word: The full word containing the kanji
    :param furigana: The full reading of the word in kana
    :param mora_sequence: Joined mora string to match against
    :param kanji_data: Dictionary containing onyomi/kunyomi data for this kanji
    :param maybe_okuri: The okurigana following the word (used for last kanji okurigana extraction)
    :param is_last_kanji: Whether this is the last kanji in the word
    :return: Tuple of (kunyomi_match, onyomi_match), either can be None
    """
    if maybe_okuri:
        # When okurigana is present, check both
        kunyomi_match = match_kunyomi_to_mora(
            kanji, mora_sequence, kanji_data, maybe_okuri, is_last_kanji, logger
        )
        onyomi_match = match_onyomi_to_mora(
            kanji, word, furigana, mora_sequence, kanji_data, maybe_okuri, is_last_kanji, logger
        )
        return (kunyomi_match, onyomi_match)
    else:
        # When no okurigana, prefer onyomi for performance
        onyomi_match = match_onyomi_to_mora(
            kanji, word, furigana, mora_sequence, kanji_data, maybe_okuri, is_last_kanji, logger
        )
        if onyomi_match:
            return (None, onyomi_match)

        kunyomi_match = match_kunyomi_to_mora(
            kanji, mora_sequence, kanji_data, maybe_okuri, is_last_kanji, logger
        )
        if kunyomi_match:
            return (kunyomi_match, None)

    return (None, None)
