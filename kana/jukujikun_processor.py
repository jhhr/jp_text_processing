"""
Jukujikun processor for handling unmatched kanji readings.

This module handles cases where kanji don't match standard onyomi/kunyomi readings,
splitting mora evenly among consecutive jukujikun positions and extracting okurigana
when the last kanji is jukujikun.
"""

from typing import Tuple

from ..all_types.main_types import ReadingMatchInfo, WrapMatchEntry
from .mora_splitter import split_to_mora_list
from .mora_alignment import MoraAlignment
from .furigana_exceptions import FURIGANA_EXCEPTION_ALIGNMENTS
from ..okuri.get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab
from ..utils.logger import package_logger as logger


def should_reject_lexicalized_na_suffix(
    word: str,
    alignment: MoraAlignment,
    remaining_kana: str,
    selected_okuri: str,
    selected_rest: str,
    last_juku_reading: str,
    kanji_okuri: str,
    word_okuri: str,
) -> bool:
    """
    Reject false-positive plain "ない" okurigana detection in partial jukujikun compounds.

    Cases like 不甲斐[ふがい]ない are lexicalized i-adjectives where the trailing ない is
    part of the word, not inflectional okurigana for the last jukujikun kanji.
    """
    if not (selected_okuri == "ない" and selected_rest == "" and remaining_kana == "ない"):
        return False
    if not (kanji_okuri == "ない" and word_okuri == "ない"):
        return False
    if len(word) < 2:
        return False
    # Only apply this safeguard when the alignment is mixed (some matched readings + jukujikun),
    # which is where this false positive appears.
    has_non_juku_match = any(match is not None for match in alignment["kanji_matches"][:-1])
    if not has_non_juku_match:
        return False
    # Last jukujikun readings ending in い are especially prone to "Xない" lexicalized parsing.
    if not last_juku_reading.endswith("い"):
        return False
    return True


def split_mora_for_jukujikun(mora_list: list[str], kanji: list[str]) -> list[str]:
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
        "split_mora_for_jukujikun - mora_count: %s, kanji_count: %s, mora_per_kanji: %s,"
        " remainder: %s, mora_list: %s, kanji: %s",
        mora_count,
        kanji_count,
        mora_per_kanji,
        remainder,
        mora_list,
        kanji,
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

        logger.debug("split_mora_for_jukujikun - kanji: %s, mora: %s", kanji[i], mora_string)
        result.append(mora_string)

        cur_mora_index = end_index

    return result


def process_jukujikun_positions(
    word: str,
    furigana: str,
    alignment: MoraAlignment,
    remaining_kana: str,
) -> Tuple[dict[int, WrapMatchEntry], str, str]:
    """
    Process jukujikun (unmatched) positions in the alignment.

    Handles:
    - Single jukujikun: Tag the mora portion at that index with <juk> tags
    - Consecutive jukujikun: Re-split combined mora evenly with remainder distribution
    - Last kanji jukujikun: Extract okurigana using mecab

    :param word: The full word
    :param furigana: The full furigana reading for the word
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
    full_furigana = "".join(alignment["mora_split"])
    logger.debug("process_jukujikun_positions: full_furigana: %s", full_furigana)

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
                        alignment["kanji_matches"][0] = ReadingMatchInfo(
                            reading=prefix_str,
                            dict_form=prefix_str,
                            match_type="onyomi",
                            reading_variant="plain",
                            matched_mora=prefix_str,
                            kanji=word[0],
                            okurigana="",
                            rest_kana="",
                        )
                start_search = start + len(ex_word)

    # If exception mapping did not set any juku parts, fall back to redistributing
    if not jukujikun_parts:
        # The trial split that produced the alignment may have handed the wrong mora to each
        # jukujikun position, so re-split and deal them out evenly. Do this one contiguous run of
        # jukujikun positions at a time: a matched kanji between two runs keeps its own mora and
        # separates what comes before it from what comes after, so pooling the mora of every
        # unmatched position would deal mora from after the match to positions before it and
        # reorder the reading.
        mora_split = alignment["mora_split"]
        runs: list[list[int]] = []
        for pos in sorted(alignment["jukujikun_positions"]):
            if runs and pos == runs[-1][-1] + 1:
                runs[-1].append(pos)
            else:
                runs.append([pos])

        for run in runs:
            # Only the mora the alignment assigned to this run's own slots. They are already in
            # order and already bounded by the neighbouring matched kanji.
            run_mora_str = "".join(mora_split[pos] for pos in run if pos < len(mora_split))
            run_mora = split_to_mora_list(
                furigana=run_mora_str,
                kanji_count=len(run),
            )["mora_list"]
            logger.debug(
                "process_jukujikun_positions - jukujikun run %s gets mora %s,"
                " alignment.mora_split: %s",
                run,
                run_mora_str,
                mora_split,
            )
            if not run_mora:
                continue

            run_kanji = [word[pos] for pos in run]
            redistributed_mora = split_mora_for_jukujikun(run_mora, run_kanji)

            # Assign redistributed mora to this run's jukujikun positions
            for idx, pos in enumerate(run):
                kanji = word[pos]
                mora_portion = redistributed_mora[idx]
                # Tag numbers and 為 (する verb) as kunyomi instead of jukujikun
                # 為 with readings し/さ is the irregular verb する
                is_suru_verb = kanji == "為" and mora_portion in ["し", "さ"]
                jukujikun_parts[pos] = {
                    "kanji": kanji,
                    "tag": "kun" if (kanji.isdigit() or is_suru_verb) else "juk",
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
        logger.debug(
            "process_jukujikun_positions - extracting okurigana for last jukujikun kanji: %s,"
            " juku_reading: %s, remaining_kana: %s",
            last_kanji,
            juku_reading,
            remaining_kana,
        )
        # Either the full word or the last kanji may produce okurigana correctly, check both
        # and take the one that produces the longest okurigana match
        kanji_okuri_result, kanji_is_noun_suru_verb = get_conjugated_okuri_with_mecab(
            word=last_kanji,
            reading=juku_reading,
            maybe_okuri=remaining_kana,
            okuri_prefix="reading",
            strict_inflection=True,
        )
        word_okuri_result, word_is_noun_suru_verb = get_conjugated_okuri_with_mecab(
            word=word,
            reading=furigana,
            maybe_okuri=remaining_kana,
            okuri_prefix="reading",
            strict_inflection=True,
        )
        # Whatever is taken as okurigana has to be spent out of the kana that follow the word:
        # okurigana + rest_kana == remaining_kana. A candidate claiming more than that has taken
        # the difference from the kanji's own reading, which stays in the furigana as well. For
        # 羽搏[はばた]く the last kanji offered たく, and writing that out gave 羽搏[はばた]たく.
        def spends_only_following_kana(result) -> bool:
            return result.okurigana + result.rest_kana == remaining_kana

        word_usable = spends_only_following_kana(word_okuri_result)
        kanji_usable = spends_only_following_kana(kanji_okuri_result)
        # Of the candidates that do, the longest okurigana is still the most specific one.
        if (
            word_usable
            and word_okuri_result.okurigana
            and (
                not kanji_usable
                or len(word_okuri_result.okurigana) > len(kanji_okuri_result.okurigana)
            )
        ):
            okuri_result = word_okuri_result
            is_noun_suru_verb = word_is_noun_suru_verb
        elif kanji_usable and kanji_okuri_result.okurigana:
            okuri_result = kanji_okuri_result
            is_noun_suru_verb = kanji_is_noun_suru_verb
        elif word_usable:
            okuri_result = word_okuri_result
            is_noun_suru_verb = word_is_noun_suru_verb
        else:
            okuri_result = word_okuri_result._replace(okurigana="", rest_kana=remaining_kana)
            is_noun_suru_verb = word_is_noun_suru_verb
        juku_entry["is_noun_suru_verb"] = is_noun_suru_verb

        if should_reject_lexicalized_na_suffix(
            word=word,
            alignment=alignment,
            remaining_kana=remaining_kana,
            selected_okuri=okuri_result.okurigana,
            selected_rest=okuri_result.rest_kana,
            last_juku_reading=juku_reading,
            kanji_okuri=kanji_okuri_result.okurigana,
            word_okuri=word_okuri_result.okurigana,
        ):
            logger.debug(
                "process_jukujikun_positions - rejecting lexicalized plain ない suffix as okurigana"
                " for word: %s, reading: %s, remaining_kana: %s, juku_reading: %s",
                word,
                furigana,
                remaining_kana,
                juku_reading,
            )
            okuri_result = okuri_result._replace(okurigana="", rest_kana=remaining_kana)

        logger.debug(
            "process_jukujikun_positions - okuri_result: %s, remaining_kana: %s, juku_reading: %s,"
            " last_kanji: %s",
            okuri_result,
            remaining_kana,
            juku_reading,
            last_kanji,
        )

        extracted_okurigana = okuri_result.okurigana
        extracted_rest_kana = okuri_result.rest_kana

    return jukujikun_parts, extracted_okurigana, extracted_rest_kana
