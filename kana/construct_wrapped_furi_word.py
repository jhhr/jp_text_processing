import logging
import re
import sys
from typing import Tuple, Optional, Literal

from ..mecab_controller.kana_conv import to_katakana, to_hiragana

from ..all_types.main_types import WrapMatchEntry, WrapTag

from ..utils.logger import console_logging, package_logger

from ..kanji.number_to_kanji import number_to_kanji

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
    logger: logging.Logger = package_logger,
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
    :param logger: the logger to use
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
            kanji_number = number_to_kanji(kanji, logger)
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

        if with_tags:
            if return_type == "kana_only":
                with_furi = f"<{tag}>{base}</{tag}>"
            else:
                with_furi = f"<{tag}>{base}</{tag}>"
        else:
            with_furi = base

        if apply_highlight and highlight:
            with_furi = f"<b>{with_furi}</b>"

        wrapped_furi_word += with_furi
        index += 1
    logger.debug("construct_wrapped_furi_word wrapped_furi_word: %s", wrapped_furi_word)
    return wrapped_furi_word


def test(
    entries: list[WrapMatchEntry],
    expected_kana_only: Optional[str] = None,
    expected_kana_only_merged: Optional[str] = None,
    expected_furigana: Optional[str] = None,
    expected_furigana_merged: Optional[str] = None,
    expected_furikanji: Optional[str] = None,
    expected_furikanji_merged: Optional[str] = None,
):

    cases: list[Tuple[FuriReconstruct, Optional[str], bool]] = [
        ("kana_only", expected_kana_only, False),
        ("kana_only", expected_kana_only_merged, True),
        ("furigana", expected_furigana, False),
        ("furikanji", expected_furikanji, False),
        ("furigana", expected_furigana_merged, True),
        ("furikanji", expected_furikanji_merged, True),
    ]

    for (
        return_type,
        expected,
        merge_consecutive,
    ) in cases:
        if not expected:
            continue
        try:
            result = construct_wrapped_furi_word(entries, return_type, merge_consecutive)
            assert result == expected
        except AssertionError:
            # Re-run with logging enabled to see what went wrong
            print("\n")
            console_logging("debug")
            construct_wrapped_furi_word(entries, return_type, merge_consecutive)
            print(f"""\033[91mTest failed
type: {return_type}, merge: {merge_consecutive}
entries: {entries}
\033[93mExpected: {expected}
\033[92mGot:      {result}
\033[0m""")
            # Stop testing here
            sys.exit(1)


def entry(
    kanji: str, tag: WrapTag, furigana: str, highlight: bool = False, is_num: bool = False
) -> WrapMatchEntry:
    """Shorthand for a test case's wrap entry, in the shape reconstruct_from_alignment builds."""
    return WrapMatchEntry(
        kanji=kanji, tag=tag, furigana=furigana, highlight=highlight, is_num=is_num
    )


def main():
    test(
        # 漢字: one part highlighted, other not, no difference when merging
        entries=[
            entry("漢", "on", "かん", highlight=True),
            entry("字", "on", "じ"),
        ],
        expected_kana_only="<b><on>かん</on></b><on>じ</on>",
        expected_kana_only_merged="<b><on>かん</on></b><on>じ</on>",
        expected_furigana="<b><on> 漢[かん]</on></b><on> 字[じ]</on>",
        expected_furigana_merged="<b><on> 漢[かん]</on></b><on> 字[じ]</on>",
        expected_furikanji="<b><on> かん[漢]</on></b><on> じ[字]</on>",
        expected_furikanji_merged="<b><on> かん[漢]</on></b><on> じ[字]</on>",
    )
    test(
        # 大人
        entries=[
            entry("大", "juk", "おと"),
            entry("人", "juk", "な"),
        ],
        expected_kana_only="<juk>おと</juk><juk>な</juk>",
        expected_kana_only_merged="<juk>おとな</juk>",
        expected_furigana="<juk> 大[おと]</juk><juk> 人[な]</juk>",
        expected_furigana_merged="<juk> 大人[おとな]</juk>",
        expected_furikanji="<juk> おと[大]</juk><juk> な[人]</juk>",
        expected_furikanji_merged="<juk> おとな[大人]</juk>",
    )
    test(
        # 友達: different tags, should not merge
        entries=[
            entry("友", "kun", "とも"),
            entry("達", "on", "だち"),
        ],
        expected_kana_only="<kun>とも</kun><on>だち</on>",
        expected_kana_only_merged="<kun>とも</kun><on>だち</on>",
        expected_furigana="<kun> 友[とも]</kun><on> 達[だち]</on>",
        expected_furigana_merged="<kun> 友[とも]</kun><on> 達[だち]</on>",
        expected_furikanji="<kun> とも[友]</kun><on> だち[達]</on>",
        expected_furikanji_merged="<kun> とも[友]</kun><on> だち[達]</on>",
    )
    test(
        # 悠々: repeated kanji, one entry covering both characters
        entries=[entry("悠々", "on", "ゆうゆう")],
        expected_kana_only="<on>ゆうゆう</on>",
        expected_kana_only_merged="<on>ゆうゆう</on>",
        expected_furigana="<on> 悠々[ゆうゆう]</on>",
        expected_furigana_merged="<on> 悠々[ゆうゆう]</on>",
        expected_furikanji="<on> ゆうゆう[悠々]</on>",
        expected_furikanji_merged="<on> ゆうゆう[悠々]</on>",
    )
    test(
        # 時間: both parts not highlighted and same tag, can get merged
        entries=[
            entry("時", "on", "ジ"),
            entry("間", "on", "カン"),
        ],
        expected_kana_only="<on>ジ</on><on>カン</on>",
        expected_kana_only_merged="<on>ジカン</on>",
        expected_furigana="<on> 時[ジ]</on><on> 間[カン]</on>",
        expected_furigana_merged="<on> 時間[ジカン]</on>",
        expected_furikanji="<on> ジ[時]</on><on> カン[間]</on>",
        expected_furikanji_merged="<on> ジカン[時間]</on>",
    )
    test(
        # 不自然: three same tag parts, can get merged
        entries=[
            entry("不", "on", "ふ"),
            entry("自", "on", "じ"),
            entry("然", "on", "ぜん"),
        ],
        expected_kana_only="<on>ふ</on><on>じ</on><on>ぜん</on>",
        expected_kana_only_merged="<on>ふじぜん</on>",
        expected_furigana="<on> 不[ふ]</on><on> 自[じ]</on><on> 然[ぜん]</on>",
        expected_furigana_merged="<on> 不自然[ふじぜん]</on>",
        expected_furikanji="<on> ふ[不]</on><on> じ[自]</on><on> ぜん[然]</on>",
        expected_furikanji_merged="<on> ふじぜん[不自然]</on>",
    )
    test(
        # 11個: a number block, always merged into one reading
        entries=[
            entry("11", "on", "じゅういっ", is_num=True),
            entry("個", "on", "こ"),
        ],
        expected_kana_only="<on>じゅういっ</on><on>こ</on>",
        expected_kana_only_merged="<on>じゅういっこ</on>",
        expected_furigana="<on> 11[じゅういっ]</on><on> 個[こ]</on>",
        expected_furigana_merged="<on> 11個[じゅういっこ]</on>",
        expected_furikanji="<on> じゅういっ[11]</on><on> こ[個]</on>",
        expected_furikanji_merged="<on> じゅういっこ[11個]</on>",
    )
    test(
        # 40分: a number block read with two tags, so the second entry carries no kanji of its
        # own; furigana and furikanji merge it into the block and tag the result <mix>
        entries=[
            entry("40", "kun", "よん", is_num=True),
            entry("", "on", "じゅっ", is_num=True),
            entry("分", "on", "ぷん"),
        ],
        expected_kana_only="<kun>よん</kun><on>じゅっ</on><on>ぷん</on>",
        expected_kana_only_merged="<kun>よん</kun><on>じゅっぷん</on>",
        expected_furigana="<mix> 40[よんじゅっ]</mix><on> 分[ぷん]</on>",
        expected_furigana_merged="<mix> 40[よんじゅっ]</mix><on> 分[ぷん]</on>",
        expected_furikanji="<mix> よんじゅっ[40]</mix><on> ぷん[分]</on>",
        expected_furikanji_merged="<mix> よんじゅっ[40]</mix><on> ぷん[分]</on>",
    )
    print("\n\033[92mTests passed\033[0m")


if __name__ == "__main__":
    main()
