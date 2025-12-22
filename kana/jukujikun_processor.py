"""
Jukujikun processor for handling unmatched kanji readings.

This module handles cases where kanji don't match standard onyomi/kunyomi readings,
splitting mora evenly among consecutive jukujikun positions and extracting okurigana
when the last kanji is jukujikun.
"""

import re
from typing import Tuple

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


def split_mora_for_jukujikun(mora_list: list[str], kanji_count: int) -> list[str]:
    """
    Split mora evenly for jukujikun kanji using arithmetic division.

    Distributes mora across kanji_count positions, with remainder mora
    distributed one per kanji from the start.

    :param mora_list: List of mora to split
    :param kanji_count: Number of kanji to distribute mora among
    :return: List of mora strings, one per kanji
    """
    mora_count = len(mora_list)
    mora_per_kanji = mora_count // kanji_count
    remainder = mora_count % kanji_count

    result: list[str] = []
    cur_mora_index = 0

    for i in range(kanji_count):
        # Base allocation
        end_index = cur_mora_index + mora_per_kanji

        # Add one extra mora to first 'remainder' kanji
        if i < remainder:
            end_index += 1

        # Join mora for this kanji
        mora_string = "".join(mora_list[cur_mora_index:end_index])
        result.append(mora_string)

        cur_mora_index = end_index

    return result


def process_jukujikun_positions(
    word: str,
    alignment: MoraAlignment,
    with_tags: bool,
    remaining_kana: str,
) -> Tuple[dict[int, str], str, str]:
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
             jukujikun_parts_dict maps kanji_index → tagged/untagged jukujikun mora string
    """
    jukujikun_parts: dict[int, str] = {}
    extracted_okurigana = ""
    extracted_rest_kana = remaining_kana

    if not alignment["jukujikun_positions"]:
        return jukujikun_parts, extracted_okurigana, extracted_rest_kana

    # Build the full furigana string from mora_split for exception substring detection
    all_mora = [mora for sublist in alignment["mora_split"] for mora in sublist]
    full_furigana = "".join(all_mora)

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
                    if with_tags:
                        jukujikun_parts[pos] = f"<juk>{mora_portion}</juk>"
                    else:
                        jukujikun_parts[pos] = mora_portion
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

        # Flatten the entire mora_split to get all mora
        all_mora = [mora for sublist in alignment["mora_split"] for mora in sublist]

        # Mark mora consumed by matched positions using the split indices
        consumed_indices = set()
        mora_index = 0
        for i in range(len(alignment["kanji_matches"])):
            mora_count_for_position = len(alignment["mora_split"][i])
            if alignment["kanji_matches"][i]:
                for j in range(mora_index, mora_index + mora_count_for_position):
                    consumed_indices.add(j)
            mora_index += mora_count_for_position

        # Get remaining mora (not consumed)
        juku_mora = [mora for idx, mora in enumerate(all_mora) if idx not in consumed_indices]

        # Redistribute these mora evenly among jukujikun positions
        juku_count = len(alignment["jukujikun_positions"])
        if juku_count == 0 or len(juku_mora) == 0:
            return jukujikun_parts, extracted_okurigana, extracted_rest_kana

        redistributed_mora = split_mora_for_jukujikun(juku_mora, juku_count)

        # Assign redistributed mora to jukujikun positions
        for idx, pos in enumerate(alignment["jukujikun_positions"]):
            mora_portion = redistributed_mora[idx]

            if with_tags:
                # Tag numbers and 為 (する verb) as kunyomi instead of jukujikun
                # 為 with readings し/さ is the irregular verb する
                is_suru_verb = word[pos] == "為" and mora_portion in ["し", "さ"]
                tag = "kun" if (word[pos].isdigit() or is_suru_verb) else "juk"
                jukujikun_parts[pos] = f"<{tag}>{mora_portion}</{tag}>"
            else:
                jukujikun_parts[pos] = mora_portion

    # Handle okurigana extraction if last kanji is jukujikun
    last_kanji_index = len(word) - 1
    if last_kanji_index in alignment["jukujikun_positions"] and last_kanji_index in jukujikun_parts:
        # Last kanji is jukujikun, extract okurigana using mecab
        last_kanji = word[last_kanji_index]
        if last_kanji == "々" and last_kanji_index > 0:
            # Use the preceding kanji for repeaters so mecab can find okurigana
            last_kanji = word[last_kanji_index - 1]

        # Get the jukujikun reading for last kanji (without tags)
        juku_reading = jukujikun_parts[last_kanji_index]
        if with_tags:
            # Remove <juk></juk> and <kun></kun> tags to get plain reading
            juku_reading = re.sub(r"</?(?:juk|kun)>", "", juku_reading)

        # Use mecab to extract okurigana
        okuri_result = get_conjugated_okuri_with_mecab(
            kanji=last_kanji,
            kanji_reading=juku_reading,
            maybe_okuri=remaining_kana,
            okuri_prefix="kanji_reading",
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
