import re
from typing import Literal

from ..all_types.main_types import WrapMatchEntry
from ..kanji.number_to_kanji import number_to_kanji
from ..mecab_controller.kana_conv import to_hiragana, to_katakana
from ..utils.logger import package_logger as logger

IS_NUMBER_RE = re.compile(r"^[0-9０-９]+$")


FuriReconstruct = Literal["furigana", "furikanji", "kana_only"]


def construct_wrapped_furi_word(
    kanji_tags: list[WrapMatchEntry],
    return_type: FuriReconstruct = "furigana",
    merge_consecutive: bool = True,
    with_tags: bool = True,
    apply_highlight: bool = True,
    original_furigana: str = "",
    katakana_positions: list[int] | None = None,
    restored_chars: dict[int, str] | None = None,
    original_start_index: int = 0,
) -> str:
    """
    Construct the word with furigana wrapped in the appropriate tags.

    :param kanji_tags: List of wrap match entries to process
    :param return_type: Type of output (furigana, furikanji, kana_only)
    :param merge_consecutive: Whether to merge consecutive tags
    :param with_tags: Whether to include XML tags
    :param apply_highlight: Whether to apply highlighting
    :param original_furigana: The original furigana before hiragana conversion
    :param katakana_positions: List of indices in original_furigana that were katakana
    :param restored_chars: Index in original_furigana → the character to write back there, for the
        kana that were rewritten before matching (ー, an iteration mark, a small vowel)
    :param original_start_index: Offset into original_furigana for the first character of this
        segment, used when reconstructing per-segment output
    :return: The constructed furigana string
    """
    if katakana_positions is None:
        katakana_positions = []
    if restored_chars is None:
        restored_chars = {}

    # Convert original furigana to hiragana for matching
    original_hiragana = to_hiragana(original_furigana) if original_furigana else ""

    logger.debug("kanji_tags: %s", kanji_tags)
    wrapped_furi_word = ""
    index = 0
    original_cursor = original_start_index
    while index < len(kanji_tags):
        cur_tag_res = kanji_tags[index]
        logger.debug("cur_tag_res: %s in index: %s", cur_tag_res, index)
        # merge consecutive results with the same tag and highlight
        # and merge numbers together in any mode but kana_only
        while next_tag_res := (kanji_tags[index + 1] if (index + 1 < len(kanji_tags)) else None):
            do_merge = False
            logger.debug("next_tag_res: %s", next_tag_res)
            if (
                next_tag_res["kanji"] == "々"
                and next_tag_res["tag"] == cur_tag_res["tag"]
                and next_tag_res["highlight"] == cur_tag_res["highlight"]
                # Avoid auto-merging repeated numeric digits when split output is requested.
                and (merge_consecutive or not (cur_tag_res["is_num"] and next_tag_res["is_num"]))
                # Keep placeholder entries (empty kanji used to expand numbers) separate when
                # merging is disabled so split outputs can surface each component.
                and (merge_consecutive or cur_tag_res["kanji"] != "" or next_tag_res["kanji"] != "")
            ):
                logger.debug("Merging repeated kanji/repeater: %s, %s", cur_tag_res, next_tag_res)
                do_merge = True
                tag = cur_tag_res["tag"]
                highlight = cur_tag_res["highlight"]
                is_num = cur_tag_res["is_num"] and next_tag_res["is_num"]
            elif (
                merge_consecutive
                and next_tag_res["tag"] == cur_tag_res["tag"]
                and next_tag_res["highlight"] == cur_tag_res["highlight"]
            ):
                # Do not merge when switching between number blocks and regular kanji if the
                # highlight differs (keep boundaries for targeted bolding). Otherwise allow
                # merging so unhighlighted numeric+counter pairs combine.
                if cur_tag_res["is_num"] != next_tag_res["is_num"] and (
                    cur_tag_res["highlight"] or next_tag_res["highlight"]
                ):
                    do_merge = False
                else:
                    logger.debug("Merging consecutive tags: %s, %s", cur_tag_res, next_tag_res)
                    is_num = cur_tag_res["is_num"] and next_tag_res["is_num"]
                    tag = cur_tag_res["tag"]
                    highlight = cur_tag_res["highlight"]
                    do_merge = True
            elif (
                return_type != "kana_only"
                and cur_tag_res["is_num"]
                and next_tag_res["kanji"] == ""
                and next_tag_res["highlight"] == cur_tag_res["highlight"]
            ):
                # In furikanji/furigana modes, absorb placeholder entries that expand a number
                # (e.g., 123 → ['', 'ニ', 'ジュウ', 'サン']) into the numeric block so the final
                # mix tag contains the full reading.
                logger.debug(
                    "Merging numeric placeholder into number: %s, %s", cur_tag_res, next_tag_res
                )
                do_merge = True
                highlight = cur_tag_res["highlight"]
                is_num = True
                tag = "mix"
            elif (
                return_type != "kana_only"
                and next_tag_res["is_num"]
                and cur_tag_res["is_num"]
                and next_tag_res["highlight"] == cur_tag_res["highlight"]
            ):
                # Merge consecutive numeric digits in furikanji/furigana mode.
                # Preserve the tag when all parts share it; use mix only when tags differ.
                logger.debug("Merging consecutive numbers: %s, %s", cur_tag_res, next_tag_res)
                do_merge = True
                highlight = cur_tag_res["highlight"]
                is_num = True
                tag = cur_tag_res["tag"] if next_tag_res["tag"] == cur_tag_res["tag"] else "mix"
            elif (
                merge_consecutive
                and return_type == "furikanji"
                and cur_tag_res["is_num"]
                and not next_tag_res["is_num"]
            ):
                # In furikanji mode with merge_consecutive=True and number+counter:
                # merge them together if same tag, keep separate if mixed tags
                peek_next = kanji_tags[index + 2] if index + 2 < len(kanji_tags) else None
                if not peek_next and next_tag_res["tag"] == cur_tag_res["tag"]:
                    # Last item and same tag, merge
                    logger.debug(
                        "Merging number with counter (same tag): %s, %s", cur_tag_res, next_tag_res
                    )
                    do_merge = True
                    is_num = False  # Result is number+counter, not pure number
                    tag = cur_tag_res["tag"]
                    highlight = cur_tag_res["highlight"]
            elif next_tag_res["furigana"] == "":
                # Gracefully handle incorrect furigana input where there was more kanji than
                # mora provided - merge empty furigana entries into previous to avoid broken output.
                logger.debug("Merging empty furigana entry: %s, %s", cur_tag_res, next_tag_res)
                do_merge = True
                tag = cur_tag_res["tag"]
                highlight = cur_tag_res["highlight"]
                is_num = cur_tag_res["is_num"]

            # Otherwise keep them separate (will create <mix> for number, separate tag for counter)
            if do_merge:
                cur_tag_res = {
                    "kanji": cur_tag_res["kanji"] + next_tag_res["kanji"],
                    "tag": tag,
                    "highlight": highlight,
                    "furigana": cur_tag_res["furigana"] + next_tag_res["furigana"],
                    "is_num": is_num,
                }
                logger.debug("New merged tag: %s", cur_tag_res)
                # Now we skip the next tag, since it's been merged
                index += 1
            else:
                break
        kanji = cur_tag_res["kanji"]
        tag = cur_tag_res["tag"]
        highlight = cur_tag_res["highlight"]
        kana = cur_tag_res["furigana"]
        is_num = cur_tag_res["is_num"]

        # Put back the characters that were rewritten for matching, and the katakana, by their
        # position in the original furigana. A restored character is written as it originally was,
        # so it doesn't need the katakana conversion.
        if kana and original_hiragana and (katakana_positions or restored_chars):
            kana_chars = list(kana)
            for i in range(len(kana_chars)):
                original_pos = original_cursor + i
                if original_pos in restored_chars:
                    kana_chars[i] = restored_chars[original_pos]
                elif (
                    original_pos in katakana_positions
                    and original_pos < len(original_hiragana)
                    # A ー that was spread out into a vowel instead of being restored is not that
                    # vowel's script to decide, leave it as the hiragana it became
                    and original_hiragana[original_pos] != "ー"
                ):
                    kana_chars[i] = to_katakana(kana_chars[i])
            kana = "".join(kana_chars)
        original_cursor += len(kana)

        logger.debug(
            "kanji: %s, tag: %s, highlight: %s, kana: %s, is_num: %s,",
            kanji,
            tag,
            highlight,
            kana,
            is_num,
        )

        # For multi-kanji numbers (3+ kanji) in furikanji/furigana modes, use <mix> tag
        if is_num and return_type != "kana_only" and tag != "mix" and IS_NUMBER_RE.match(kanji):
            kanji_number = number_to_kanji(kanji)
            if len(kanji_number) >= 3:
                tag = "mix"

        if return_type == "furikanji":
            # Skip empty kanji in furikanji mode (they've been merged)
            if not kanji:
                index += 1
                continue
            base = f" {kana}[{kanji}]"
        elif return_type == "furigana":
            # Skip empty kanji in furigana mode (they've been merged)
            if not kanji:
                index += 1
                continue
            base = f" {kanji}[{kana}]"
        else:
            # kana_only: output kana even for empty kanji entries
            base = f"{kana}"

        with_furi = f"<{tag}>{base}</{tag}>" if with_tags else base

        if apply_highlight and highlight:
            with_furi = f"<b>{with_furi}</b>"

        wrapped_furi_word += with_furi
        index += 1
    logger.debug("construct_wrapped_furi_word wrapped_furi_word: %s", wrapped_furi_word)
    return wrapped_furi_word
