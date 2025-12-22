import re
import sys
from typing import NamedTuple, Tuple, Union, Optional, Literal

try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger  # type: ignore[no-redef]

try:
    from kanji.number_to_kanji import number_to_kanji
except ImportError:
    from ..kanji.number_to_kanji import number_to_kanji  # type: ignore[no-redef]

TAG_WRAPPED_FURIGANA_RE = re.compile(r"(?:<(b)>)?<(on|kun|juk)>(.*?)<\/\2>(?:<\/\1>)?")

IS_NUMBER_RE = re.compile(r"^[0-9０-９]+$")


FuriReconstruct = Literal["furigana", "furikanji", "kana_only"]


class TagOrder(NamedTuple):
    tag: str
    highlight: Union[str, None]
    contents: str
    position: int


def get_tag_order(furigana: str, logger=Logger("error")) -> list[TagOrder]:
    """
    Get the order of <on>, <kun>, and <juk> tags in the furigana string.

    :param furigana: The furigana string containing the tags.
    :return: A list of tuples containing the tag name and its position.
    """
    logger.debug(f"get_tag_order furigana: {furigana}")
    tag_order = []
    for match in TAG_WRAPPED_FURIGANA_RE.finditer(furigana):
        highlight = match.group(1)
        tag = match.group(2)
        contents = match.group(3)
        tag_order.append(TagOrder(tag, highlight, contents, match.start()))
    return tag_order


class WrapMatchResult(NamedTuple):
    kanji: str
    tag: str
    highlight: Union[str, None]
    furigana: str
    is_num: bool


def match_tags_with_kanji(
    word: str, furigana: str, logger=Logger("error")
) -> list[WrapMatchResult]:
    """
    Match the tags with each kanji in the word.

    :param word: The word containing kanji characters.
    :param furigana: The furigana string containing the tags.
    :return: A list of tuples containing the kanji and its corresponding tag.
    """
    tag_order = get_tag_order(furigana, logger)
    logger.debug(f"match_tags_with_kanji - word: {word}, tag_order: {tag_order}")
    kanji_tags = []
    kanji_index = 0
    tag_index = 0
    loop_count = 0
    max_loops = len(word) * len(tag_order) + 10  # Safety limit
    while tag_index < len(tag_order):
        loop_count += 1
        if loop_count > max_loops:
            logger.debug(
                f"match_tags_with_kanji - infinite loop detected! word={word},"
                f" tag_order={tag_order}, kanji_index={kanji_index}, tag_index={tag_index}"
            )
            break
        cur_tag = tag_order[tag_index]
        tag, highlight, kana, _ = cur_tag
        if kanji_index < len(word):
            cur_kanji = word[kanji_index]
            next_kanji = word[kanji_index + 1] if kanji_index + 1 < len(word) else None
            # Merge any consecutive numbers into a single logical unit, consuming tags based on
            # how many kanji the number converts to (e.g., "３０" → "三十" = 2 kanji = 2 tags).
            # For numbers with mixed tags (kun+on), keep them as separate results so kana_only
            # mode can output them separately.
            if IS_NUMBER_RE.match(cur_kanji):
                number_start = kanji_index
                while kanji_index < len(word) and IS_NUMBER_RE.match(word[kanji_index]):
                    kanji_index += 1
                number_str = word[number_start:kanji_index]
                # Convert to kanji to determine how many tags we need to consume
                kanji_number = number_to_kanji(number_str, logger)
                tags_to_consume = len(kanji_number)
                # Check if all tags are the same type
                all_same_tag = True
                for i in range(1, tags_to_consume):
                    if tag_index + i < len(tag_order):
                        next_tag = tag_order[tag_index + i]
                        if next_tag.tag != tag:
                            all_same_tag = False
                            break

                if all_same_tag:
                    # All tags are the same, accumulate kana and create single result
                    accumulated_kana = kana
                    for i in range(1, tags_to_consume):
                        if tag_index + i < len(tag_order):
                            next_tag = tag_order[tag_index + i]
                            accumulated_kana += next_tag.contents
                    kanji_tags.append(
                        WrapMatchResult(number_str, tag, highlight, accumulated_kana, True)
                    )
                    tag_index += tags_to_consume
                else:
                    # Mixed tags - create separate results for each kanji in the converted number
                    # so they can be handled differently in kana_only vs furikanji modes
                    for i, kanji_char in enumerate(kanji_number):
                        if tag_index < len(tag_order):
                            cur_num_tag = tag_order[tag_index]
                            # For the first kanji, use the full number str; for others use empty
                            # (they'll get merged in furikanji mode but split in kana_only)
                            if i == 0:
                                kanji_tags.append(
                                    WrapMatchResult(
                                        number_str,
                                        cur_num_tag.tag,
                                        cur_num_tag.highlight,
                                        cur_num_tag.contents,
                                        True,
                                    )
                                )
                            else:
                                kanji_tags.append(
                                    WrapMatchResult(
                                        "",  # Empty kanji for subsequent parts
                                        cur_num_tag.tag,
                                        cur_num_tag.highlight,
                                        cur_num_tag.contents,
                                        True,
                                    )
                                )
                            tag_index += 1
            elif next_kanji and (next_kanji == cur_kanji or next_kanji == "々"):
                # Only merge with the next tag when it matches the same tag type; otherwise keep
                # separate so adjacent repeater groups with different readings don't collapse.
                next_tag = tag_order[tag_index + 1] if tag_index + 1 < len(tag_order) else None
                if next_tag and next_tag.tag == tag:
                    combined_kana = kana + next_tag.contents
                    kanji_tags.append(
                        WrapMatchResult(
                            cur_kanji + next_kanji, tag, highlight, combined_kana, False
                        )
                    )
                    kanji_index += 2
                    tag_index += 2  # Skip the next tag since we combined it
                else:
                    kanji_tags.append(
                        WrapMatchResult(word[kanji_index], tag, highlight, kana, False)
                    )
                    kanji_index += 1
                    tag_index += 1
            else:
                kanji_tags.append(WrapMatchResult(word[kanji_index], tag, highlight, kana, False))
                kanji_index += 1
                tag_index += 1
        else:
            # Ran out of kanji but still have tags - this shouldn't happen in normal cases
            # Just skip remaining tags to avoid infinite loop
            logger.debug(
                f"match_tags_with_kanji - ran out of kanji at tag_index={tag_index}, word={word},"
                f" tag_order={tag_order}"
            )
            break

    return kanji_tags


def construct_wrapped_furi_word(
    word: str,
    furigana: str,
    return_type: FuriReconstruct,
    merge_consecutive: bool = True,
    logger=Logger("error"),
) -> str:
    """
    Construct the word with furigana wrapped in the appropriate tags
    """
    logger.debug(
        f"construct_wrapped_furi_word word: {word}, furigana: {furigana}, return_type:"
        f" {return_type}, merge_consecutive: {merge_consecutive}"
    )
    kanji_tags = match_tags_with_kanji(word, furigana, logger)
    logger.debug(f"kanji_tags: {kanji_tags}")
    wrapped_furi_word = ""
    index = 0
    while index < len(kanji_tags):
        cur_tag_res = kanji_tags[index]
        logger.debug(f"cur_tag_res: {cur_tag_res} in index: {index}")
        # merge consecutive results with the same tag and highlight
        # and merge numbers together in any mode but kana_only
        while next_tag_res := (kanji_tags[index + 1] if (index + 1 < len(kanji_tags)) else None):
            do_merge = False
            logger.debug(f"next_tag_res: {next_tag_res}")
            if (
                merge_consecutive
                and next_tag_res.tag == cur_tag_res.tag
                and next_tag_res.highlight == cur_tag_res.highlight
            ):
                # Do not merge when switching between number blocks and regular kanji if the
                # highlight differs (keep boundaries for targeted bolding). Otherwise allow
                # merging so unhighlighted numeric+counter pairs combine.
                if cur_tag_res.is_num != next_tag_res.is_num and (
                    cur_tag_res.highlight or next_tag_res.highlight
                ):
                    do_merge = False
                else:
                    logger.debug(f"Merging consecutive tags: {cur_tag_res}, {next_tag_res}")
                    is_num = cur_tag_res.is_num and next_tag_res.is_num
                    tag = cur_tag_res.tag
                    highlight = cur_tag_res.highlight
                    do_merge = True
            elif return_type != "kana_only" and next_tag_res.is_num and cur_tag_res.is_num:
                # Merge consecutive numeric digits in furikanji/furigana mode
                # Always use <mix> for multi-part numbers to indicate they're composite
                logger.debug(f"Merging consecutive numbers: {cur_tag_res}, {next_tag_res}")
                do_merge = True
                highlight = cur_tag_res.highlight
                is_num = True
                tag = "mix"
            elif (
                merge_consecutive
                and return_type == "furikanji"
                and cur_tag_res.is_num
                and not next_tag_res.is_num
            ):
                # In furikanji mode with merge_consecutive=True and number+counter:
                # merge them together if same tag, keep separate if mixed tags
                peek_next = kanji_tags[index + 2] if index + 2 < len(kanji_tags) else None
                if not peek_next and next_tag_res.tag == cur_tag_res.tag:
                    # Last item and same tag, merge
                    logger.debug(
                        f"Merging number with counter (same tag): {cur_tag_res}, {next_tag_res}"
                    )
                    do_merge = True
                    is_num = False  # Result is number+counter, not pure number
                    tag = cur_tag_res.tag
                    highlight = cur_tag_res.highlight
                # Otherwise keep them separate (will create <mix> for number, separate tag for counter)
            if do_merge:
                cur_tag_res = WrapMatchResult(
                    cur_tag_res.kanji + next_tag_res.kanji,
                    tag,
                    highlight,
                    cur_tag_res.furigana + next_tag_res.furigana,
                    is_num,
                )
                logger.debug(f"New merged tag: {cur_tag_res}")
                # Now we skip the next tag, since it's been merged
                index += 1
            else:
                break
        kanji, tag, highlight, kana, is_num = cur_tag_res
        logger.debug(
            f"kanji: {kanji}, tag: {tag}, highlight: {highlight}, kana: {kana}, is_num: {is_num},"
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
            with_furi = f"<{tag}> {kana}[{kanji}]</{tag}>"
            if highlight:
                with_furi = f"<{highlight}>{with_furi}</{highlight}>"
        elif return_type == "furigana":
            # Skip empty kanji in furigana mode (they've been merged)
            if not kanji:
                index += 1
                continue
            with_furi = f"<{tag}> {kanji}[{kana}]</{tag}>"
            if highlight:
                with_furi = f"<{highlight}>{with_furi}</{highlight}>"
        else:
            # kana_only: output kana even for empty kanji entries
            with_furi = f"<{tag}>{kana}</{tag}>"
            if highlight:
                with_furi = f"<{highlight}>{with_furi}</{highlight}>"
        wrapped_furi_word += with_furi
        index += 1
    logger.debug(f"construct_wrapped_furi_word wrapped_furi_word: {wrapped_furi_word}")
    return wrapped_furi_word


def test(
    word: str,
    furigana: str,
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
            result = construct_wrapped_furi_word(word, furigana, return_type, merge_consecutive)
            assert result == expected
        except AssertionError:
            # Re-run with logging enabled to see what went wrong
            print("\n")
            construct_wrapped_furi_word(
                word, furigana, return_type, merge_consecutive, logger=Logger("debug")
            )
            print(f"""\033[91mTest failed
type: {return_type}, merge: {merge_consecutive}
word: {word}, furigana: {furigana}
\033[93mExpected: {expected}
\033[92mGot:      {result}
\033[0m""")
            # Stop testing here
            sys.exit(0)


def main():
    test(
        word="漢字",
        # one part highlighted, other not, no difference when merging
        furigana="<b><on>かん</on></b><on>じ</on>",
        expected_kana_only="<b><on>かん</on></b><on>じ</on>",
        expected_kana_only_merged="<b><on>かん</on></b><on>じ</on>",
        expected_furigana="<b><on> 漢[かん]</on></b><on> 字[じ]</on>",
        expected_furigana_merged="<b><on> 漢[かん]</on></b><on> 字[じ]</on>",
        expected_furikanji="<b><on> かん[漢]</on></b><on> じ[字]</on>",
        expected_furikanji_merged="<b><on> かん[漢]</on></b><on> じ[字]</on>",
    )
    test(
        word="大人",
        furigana="<juk>おと</juk><juk>な</juk>",
        expected_kana_only="<juk>おと</juk><juk>な</juk>",
        expected_kana_only_merged="<juk>おとな</juk>",
        expected_furigana="<juk> 大[おと]</juk><juk> 人[な]</juk>",
        expected_furigana_merged="<juk> 大人[おとな]</juk>",
        expected_furikanji="<juk> おと[大]</juk><juk> な[人]</juk>",
        expected_furikanji_merged="<juk> おとな[大人]</juk>",
    )
    test(
        word="友達",
        # different tags, should not merge
        furigana="<kun>とも</kun><on>だち</on>",
        expected_kana_only="<kun>とも</kun><on>だち</on>",
        expected_kana_only_merged="<kun>とも</kun><on>だち</on>",
        expected_furigana="<kun> 友[とも]</kun><on> 達[だち]</on>",
        expected_furigana_merged="<kun> 友[とも]</kun><on> 達[だち]</on>",
        expected_furikanji="<kun> とも[友]</kun><on> だち[達]</on>",
        expected_furikanji_merged="<kun> とも[友]</kun><on> だち[達]</on>",
    )
    test(
        word="悠々",
        # repeated kanji, should merge always
        furigana="<on>ゆうゆう</on>",
        expected_kana_only="<on>ゆうゆう</on>",
        expected_kana_only_merged="<on>ゆうゆう</on>",
        expected_furigana="<on> 悠々[ゆうゆう]</on>",
        expected_furigana_merged="<on> 悠々[ゆうゆう]</on>",
        expected_furikanji="<on> ゆうゆう[悠々]</on>",
        expected_furikanji_merged="<on> ゆうゆう[悠々]</on>",
    )
    test(
        word="時間",
        # both parts not highlighted and same tag, can get merged
        furigana="<on>ジ</on><on>カン</on>",
        expected_kana_only="<on>ジ</on><on>カン</on>",
        expected_kana_only_merged="<on>ジカン</on>",
        expected_furigana="<on> 時[ジ]</on><on> 間[カン]</on>",
        expected_furigana_merged="<on> 時間[ジカン]</on>",
        expected_furikanji="<on> ジ[時]</on><on> カン[間]</on>",
        expected_furikanji_merged="<on> ジカン[時間]</on>",
    )
    test(
        word="不自然",
        # three same tag parts, can get merged
        furigana="<on>ふ</on><on>じ</on><on>ぜん</on>",
        expected_kana_only="<on>ふ</on><on>じ</on><on>ぜん</on>",
        expected_kana_only_merged="<on>ふじぜん</on>",
        expected_furigana="<on> 不[ふ]</on><on> 自[じ]</on><on> 然[ぜん]</on>",
        expected_furigana_merged="<on> 不自然[ふじぜん]</on>",
        expected_furikanji="<on> ふ[不]</on><on> じ[自]</on><on> ぜん[然]</on>",
        expected_furikanji_merged="<on> ふじぜん[不自然]</on>",
    )
    test(
        word="11個",
        # numbers, always merge
        furigana="<on>じゅう</on><on>いっ</on><on>こ</on>",
        expected_kana_only="<on>じゅういっ</on><on>こ</on>",
        expected_kana_only_merged="<on>じゅういっこ</on>",
        expected_furigana="<on> 11[じゅういっ]</on><on> 個[こ]</on>",
        expected_furigana_merged="<on> 11個[じゅういっこ]</on>",
        expected_furikanji="<on> じゅういっ[11]</on><on> こ[個]</on>",
        expected_furikanji_merged="<on> じゅういっこ[11個]</on>",
    )
    test(
        word="40分",
        # numbers, merged in furigana and furikanji modes always
        furigana="<kun>よん</kun><on>じゅっ</on><on>ぷん</on>",
        expected_kana_only="<kun>よん</kun><on>じゅっ</on><on>ぷん</on>",
        expected_kana_only_merged="<kun>よん</kun><on>じゅっぷん</on>",
        expected_furigana="<mix> 40[よんじゅっ]</mix><on> 分[ぷん]</on>",
        expected_furigana_merged="<mix> 40[よんじゅっ]</mix><on> 分[ぷん]</on>",
        expected_furikanji="<mix> よんじゅっ[40]</mix><on> ぷん[分]</on>",
        expected_furikanji_merged="<mix> よんじゅっ[40]</mix><on> ぷん[分]</on>",
    )
    # Numbers where the number of tags > number of kanji will break currently
    # test(
    #     word="２１９１年",
    #     # numbers, always merge
    #     furigana="<on>に</on><on>せん</on><on>ひゃく</on><on>きゅう</on><on>じゅう</on><on>いち</on><on>ねん</on>",
    #     expected_kana_only="<on>にせんひゃくきゅうじゅういちねん</on>",
    #     expected_kana_only_merged="<on>にせんひゃくきゅうじゅういちねん</on>",
    #     expected_furigana="<on> ２１９１[にせんひゃくきゅうじゅういち]</on><on> 年[ねん]</on>",
    #     expected_furigana_merged="<on> ２１９１年[にせんひゃくきゅうじゅういちねん]</on>",
    #     expected_furikanji="<on> にせんひゃくきゅうじゅういち[２１９１]</on><on> ねん[年]</on>",
    #     expected_furikanji_merged="<on> にせんひゃくきゅうじゅういちねん[２１９１年]</on>",
    # )
    print("\n\033[92mTests passed\033[0m")


if __name__ == "__main__":
    main()
