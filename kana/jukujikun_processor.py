"""
Jukujikun processor for handling unmatched kanji readings.

This module handles cases where kanji don't match standard onyomi/kunyomi readings,
splitting mora evenly among consecutive jukujikun positions and extracting okurigana
when the last kanji is jukujikun.
"""

from typing import Tuple

try:
    from all_types.main_types import WrapMatchEntry
except ImportError:
    from ..all_types.main_types import WrapMatchEntry
try:
    from kana.mora_splitter import split_to_mora_list
except ImportError:
    from .mora_splitter import split_to_mora_list
try:
    from kana.mora_alignment import MoraAlignment
except ImportError:
    from .mora_alignment import MoraAlignment
try:
    from kana.furigana_exceptions import FURIGANA_EXCEPTION_ALIGNMENTS
except ImportError:
    from .furigana_exceptions import FURIGANA_EXCEPTION_ALIGNMENTS
try:
    from okuri.get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab
except ImportError:
    from ..okuri.get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab
try:
    from kanji.all_kanji_data import all_kanji_data
except ImportError:
    from ..kanji.all_kanji_data import all_kanji_data
try:
    from mecab_controller.kana_conv import to_hiragana
except ImportError:
    from ..mecab_controller.kana_conv import to_hiragana
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger


def split_mora_for_jukujikun(
    mora_list: list[str], kanji: list[str], logger: Logger = Logger("error")
) -> list[str]:
    """
    Split mora evenly for jukujikun kanji using arithmetic division.

    Distributes mora across each kanji position, with remainder mora
    distributed one per kanji from the start.

    :param mora_list: List of mora to split
    :param kanji: List of kanji to distribute mora among
    :return: List of mora strings, one per kanji
    """
    kanji_count = len(kanji)
    mora_count = len(mora_list)
    mora_per_kanji = mora_count // kanji_count
    remainder = mora_count % kanji_count

    logger.debug(
        f"split_mora_for_jukujikun - mora_count: {mora_count}, kanji_count: {kanji_count},"
        f" mora_per_kanji: {mora_per_kanji}, remainder: {remainder}, mora_list: {mora_list}, kanji:"
        f" {kanji}"
    )

    result: list[str] = []
    cur_mora_index = 0

    for i in range(kanji_count):
        # Base allocation
        end_index = cur_mora_index + mora_per_kanji

        # Add remainder extra mora until exhausted
        if i < remainder:
            end_index += 1

        # Join mora for this kanji
        mora_string = "".join(mora_list[cur_mora_index:end_index])

        logger.debug(f"split_mora_for_jukujikun - kanji: {kanji[i]}, mora: {mora_string}")
        result.append(mora_string)

        cur_mora_index = end_index

    return result


def process_jukujikun_positions(
    word: str,
    alignment: MoraAlignment,
    remaining_kana: str,
    logger: Logger = Logger("error"),
) -> Tuple[dict[int, WrapMatchEntry], str, str]:
    """
    Process jukujikun (unmatched) positions in the alignment.

    Handles:
    - Single jukujikun: Tag the mora portion at that index with <juk> tags
    - Consecutive jukujikun: Re-split combined mora evenly with remainder distribution
    - Last kanji jukujikun: Extract okurigana using mecab

    :param word: The full word
    :param alignment: The mora alignment result containing jukujikun positions
    :param with_tags: Whether to wrap jukujikun portions in <juk> tags
    :param remaining_kana: The kana following the word (for okurigana extraction)
    :return: Tuple of (jukujikun_parts_dict, okurigana, rest_kana)
             jukujikun_parts_dict maps kanji_index → WrapMatchEntry describing the mora
    """
    jukujikun_parts: dict[int, WrapMatchEntry] = {}
    extracted_okurigana = ""
    extracted_rest_kana = remaining_kana

    if not alignment["jukujikun_positions"]:
        return jukujikun_parts, extracted_okurigana, extracted_rest_kana

    # Build the full furigana string from mora_split for exception substring detection
    all_mora = [mora for sublist in alignment["mora_split"] for mora in sublist]
    full_furigana = "".join(all_mora)
    logger.debug(f"process_jukujikun_positions: full_furigana: {full_furigana}")

    # Priority: If the word contains a known exception substring and the furigana contains
    # its reading, assign jukujikun parts directly based on the exception mapping.
    for key, entries in FURIGANA_EXCEPTION_ALIGNMENTS.items():
        # Keys are in the format "<word>_<furigana>"
        try:
            ex_word, ex_furi = key.split("_", 1)
        except ValueError:
            continue
        if ex_word in word and ex_furi in full_furigana:
            start_search = 0
            while True:
                start = word.find(ex_word, start_search)
                if start == -1:
                    break
                # Assign per-kanji mora for the exception substring
                for offset, entry in enumerate(entries):
                    pos = start + offset
                    mora_portion = entry["mora"]
                    # Only populate jukujikun parts for jukujikun entries; leave onyomi/kunyomi
                    # to the existing alignment matches so their tags stay accurate.
                    if entry["type"] != "jukujikun":
                        continue

                    if pos not in alignment["jukujikun_positions"]:
                        alignment["jukujikun_positions"].append(pos)
                    jukujikun_parts[pos] = {
                        "kanji": word[pos],
                        "tag": "juk",
                        "highlight": False,
                        "furigana": mora_portion,
                        "is_num": word[pos].isdigit(),
                    }
                # Special-case: when there is exactly one kanji before the first exception,
                # set its matched mora to the furigana prefix before the exception reading.
                if start_search == 0 and start == 1 and not alignment["kanji_matches"][0]:
                    prefix_str = full_furigana.split(ex_furi, 1)[0]
                    if prefix_str:
                        alignment["kanji_matches"][0] = {
                            "reading": prefix_str,
                            "dict_form": prefix_str,
                            "match_type": "onyomi",
                            "reading_variant": "plain",
                            "matched_mora": prefix_str,
                            "kanji": word[0],
                            "okurigana": "",
                            "rest_kana": "",
                        }
                start_search = start + len(ex_word)

            # Synthesize matches for prefix/suffix positions without matches
            def synthesize_match_for_pos(pos: int):
                if pos < 0 or pos >= len(word):
                    return
                if alignment["kanji_matches"][pos]:
                    return
                if pos in alignment["jukujikun_positions"]:
                    return
                mora_seq = "".join(alignment["mora_split"][pos])
                if not mora_seq:
                    return
                kanji_char = word[pos]
                data = all_kanji_data.get(kanji_char, {})
                on_readings = [to_hiragana(r) for r in data.get("on", "").split("、") if r]
                kun_readings = [
                    to_hiragana(r.split(".")[0]) for r in data.get("kun", "").split("、") if r
                ]
                match_type = (
                    "onyomi"
                    if mora_seq in on_readings
                    else ("kunyomi" if mora_seq in kun_readings else "onyomi")
                )
                alignment["kanji_matches"][pos] = {
                    "reading": mora_seq,
                    "dict_form": mora_seq,
                    "match_type": match_type,
                    "reading_variant": "plain",
                    "matched_mora": mora_seq,
                    "kanji": kanji_char,
                    "okurigana": "",
                    "rest_kana": "",
                }

            # Prefix [0, start)
            for p in range(0, start):
                synthesize_match_for_pos(p)
            # Suffix (start + len(entries)) .. end
            end = start + len(entries)
            for p in range(end, len(word)):
                synthesize_match_for_pos(p)
            # Stop after first match; remaining positions handled by alignment
            break

    # If exception mapping did not set any juku parts, fall back to redistributing
    if not jukujikun_parts:
        # The mora_split from alignment was based on a trial split where some
        # positions matched and others didn't. The mora allocated to jukujikun positions in that
        # split may be incorrect. Instead, we should:
        # 1. Calculate total mora used by MATCHED positions (from their matched_mora field)
        # 2. Calculate remaining mora (total - matched)
        # 3. Redistribute remaining mora among jukujikun positions

        # Mark mora consumed by matched positions using the split indices
        consumed_indices = set()
        for i in range(len(alignment["kanji_matches"])):
            if alignment["kanji_matches"][i]:
                consumed_indices.add(i)

        # Get remaining mora (not consumed), merge the lists back into a single string and then
        # split into mora again with split_to_mora_list
        try:
            unconsumed_mora = [
                "".join(moras)
                for idx, moras in enumerate(alignment["mora_split"])
                if idx not in consumed_indices
            ]
            juku_mora_str = "".join(unconsumed_mora)
        except Exception:
            logger.error(
                "process_jukujikun_positions - Error building juku_mora_str, alignment:"
                f" {alignment}, consumed_indices: {consumed_indices}, word: {word}"
            )
        logger.debug(
            f"process_jukujikun_positions - remaining mora for jukujikun: {juku_mora_str},"
            f" consumed_indices: {consumed_indices}, alignment.mora_split:"
            f" {alignment['mora_split']}"
        )
        juku_count = len(alignment["jukujikun_positions"])
        juku_mora = split_to_mora_list(
            furigana=juku_mora_str,
            kanji_count=juku_count,
        )["mora_list"]

        # Redistribute these mora evenly among jukujikun positions
        if juku_count == 0 or len(juku_mora) == 0:
            return jukujikun_parts, extracted_okurigana, extracted_rest_kana

        juku_kanji = [word[pos] for pos in alignment["jukujikun_positions"]]
        redistributed_mora = split_mora_for_jukujikun(juku_mora, juku_kanji, logger=logger)

        # Assign redistributed mora to jukujikun positions
        for idx, pos in enumerate(alignment["jukujikun_positions"]):
            kanji = word[pos]
            mora_portion = redistributed_mora[idx]
            # Tag numbers and 為 (する verb) as kunyomi instead of jukujikun
            # 為 with readings し/さ is the irregular verb する
            is_suru_verb = kanji == "為" and mora_portion in ["し", "さ"]
            tag = "kun" if (kanji.isdigit() or is_suru_verb) else "juk"
            jukujikun_parts[pos] = {
                "kanji": kanji,
                "tag": tag,
                "highlight": False,
                "furigana": mora_portion,
                "is_num": kanji.isdigit(),
            }

    # Handle okurigana extraction if last kanji is jukujikun
    last_kanji_index = len(word) - 1
    if last_kanji_index in alignment["jukujikun_positions"] and last_kanji_index in jukujikun_parts:
        # Last kanji is jukujikun, extract okurigana using mecab
        # Get the jukujikun reading for last kanji (structured entry)
        juku_entry = jukujikun_parts[last_kanji_index]
        juku_reading = juku_entry["furigana"]
        last_kanji = word[last_kanji_index]
        if last_kanji == "々" and last_kanji_index > 0:
            # Combine with previous kanji for okurigana extraction
            last_kanji = word[last_kanji_index - 1] + "々"
            # Combine reading also
            juku_reading = jukujikun_parts[last_kanji_index - 1]["furigana"] + juku_reading

        # Use mecab to extract okurigana
        okuri_result = get_conjugated_okuri_with_mecab(
            kanji=last_kanji,
            kanji_reading=juku_reading,
            maybe_okuri=remaining_kana,
            okuri_prefix="kanji_reading",
        )
        logger.debug(
            f"process_jukujikun_positions - okuri_result: {okuri_result}, remaining_kana:"
            f" {remaining_kana}, juku_reading: {juku_reading}, last_kanji: {last_kanji}"
        )

        extracted_okurigana = okuri_result.okurigana
        extracted_rest_kana = okuri_result.rest_kana

        # Fallback: for jukujikun exceptions where mecab cannot parse (e.g., 清々 + しい),
        # treat the entire trailing kana as okurigana when nothing was extracted and the
        # trailing text doesn't look like a standalone particle.
        particle_heads = {"を", "は", "が", "に", "で", "と", "も", "へ", "の", "や", "か"}
        if (
            not extracted_okurigana
            and remaining_kana
            and len(remaining_kana) > 1
            and remaining_kana[0] not in particle_heads
        ):
            extracted_okurigana = remaining_kana
            extracted_rest_kana = ""

    return jukujikun_parts, extracted_okurigana, extracted_rest_kana
