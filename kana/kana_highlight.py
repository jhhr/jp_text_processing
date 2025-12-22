from functools import partial
import re
from typing import Literal, Optional, Tuple, cast

from .construct_wrapped_furi_word import (
    construct_wrapped_furi_word,
    FuriReconstruct,
)

try:
    from mecab_controller.kana_conv import to_katakana, to_hiragana, is_katakana_str
except ImportError:
    from ..mecab_controller.kana_conv import to_katakana, to_hiragana, is_katakana_str
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger
try:
    from kanji.number_to_kanji import number_to_kanji
except ImportError:
    from ..kanji.number_to_kanji import number_to_kanji
    from okuri.okurigana_dict import (
        get_verb_noun_form_okuri,
    )
except ImportError:
    from ..okuri.okurigana_dict import (
        get_verb_noun_form_okuri,
    )
try:
    from okuri.okurigana_mix_cleaning_replacer import (
        OKURIGANA_MIX_CLEANING_REC,
        okurigana_mix_cleaning_replacer,
    )
except ImportError:
    from ..okuri.okurigana_mix_cleaning_replacer import (
        OKURIGANA_MIX_CLEANING_REC,
        okurigana_mix_cleaning_replacer,
    )
try:
    from regex.kanji_furi import (
        DOUBLE_KANJI_REC,
        KANJI_AND_FURIGANA_AND_OKURIGANA_REC,
        FURIGANA_REC,
        KATAKANA_REC,
    )
except ImportError:
    from ..regex.kanji_furi import (
        DOUBLE_KANJI_REC,
        KANJI_AND_FURIGANA_AND_OKURIGANA_REC,
        FURIGANA_REC,
        KATAKANA_REC,
    )
try:
    from regex.mora import ALL_MORA_REC
except ImportError:
    from ..regex.mora import ALL_MORA_REC
try:
    from regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA, RENDAKU_CONVERSION_DICT_KATAKANA
except ImportError:
    from ..regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA, RENDAKU_CONVERSION_DICT_KATAKANA
try:
    from all_types.main_types import (
        WordData,
        HighlightArgs,
        Edge,
        WithTagsDef,
        FuriganaParts,
        YomiMatchResult,
        FinalResult,
        MoraAlignment,
        ReadingType,
    )
except ImportError:
    from ..all_types.main_types import (
        WordData,
        HighlightArgs,
        Edge,
        WithTagsDef,
        FuriganaParts,
        YomiMatchResult,
        FinalResult,
        MoraAlignment,
        ReadingType,
    )
try:
    from kana.furigana_exceptions import check_exception
except ImportError:
    from .furigana_exceptions import check_exception
try:
    from kana.mora_splitter import split_to_mora_list
except ImportError:
    from .mora_splitter import split_to_mora_list
try:
    from kana.mora_alignment import find_first_complete_alignment
except ImportError:
    from .mora_alignment import find_first_complete_alignment
try:
    from kana.jukujikun_processor import process_jukujikun_positions
except ImportError:
    from .jukujikun_processor import process_jukujikun_positions


SMALL_TSU_POSSIBLE_HIRAGANA = ["つ", "ち", "く", "き", "り", "ん", "う"]
SMALL_TSU_POSSIBLE_KATAKANA = [to_katakana(k) for k in SMALL_TSU_POSSIBLE_HIRAGANA]


VOWEL_CHANGE_DICT_HIRAGANA = {
    "お": ["よ", "ょ"],
    "あ": ["や", "ゃ"],
    "う": ["ゆ", "ゅ"],
}
VOWEL_CHANGE_DICT_KATAKANA = {
    to_katakana(k): [to_katakana(v) for v in vs] for k, vs in VOWEL_CHANGE_DICT_HIRAGANA.items()
}


# Exceptions for words where the first kanji has a kunyomi reading that is the same as the
# the whole reading for the jukujikun compound. This is used to avoid matching the kunyomi
# reading for the first kanji as a separate word.
JUKUJIKUN_KUNYOMI_OVERLAP: dict[str, str] = {
    "風邪": "かぜ",
    "薔薇": "ばら",
    "真面": "まじ",
    "蕎麦": "そば",
    "襤褸": "ぼろ",
}


def re_match_from_right(text):
    return re.compile(rf"(.*)({text})(.*?)$")


def re_match_from_left(text):
    return re.compile(rf"^(.*?)({text})(.*)$")


def re_match_from_middle(text):
    return re.compile(rf"^(.*?)({text})(.*?)$")


def onyomi_replacer(match, wrap_readings_with_tags=True, convert_to_katakana=True):
    """
    re.sub replacer function for onyomi used with the above regexes§
    """
    onyomi_kana = to_katakana(match.group(2)) if convert_to_katakana else match.group(2)
    if wrap_readings_with_tags:
        onyomi_kana = f"<on>{onyomi_kana}</on>"
    return f"{match.group(1)}<b>{onyomi_kana}</b>{match.group(3)}"


def kunyomi_replacer(match, wrap_readings_with_tags=True):
    """
    re.sub replacer function for kunyomi used with the above regexes
    """
    kunyomi_kana = match.group(2)
    if wrap_readings_with_tags:
        kunyomi_kana = f"<kun>{kunyomi_kana}</kun>"
    return f"{match.group(1)}<b>{kunyomi_kana}</b>{match.group(3)}"


def kana_filter(text):
    """
    Implementation of the basic Anki kana filter
    This is needed to clean up the text in cases where we know there's no matches to the kanji
    This works differently as it directly matches kanji characters instead of [^ >] as in the Anki
    built-in version. For whatever reason a python version using that doesn't work as expected.
    :param text: The text to clean
    :return: The cleaned text
    """

    def bracket_replace(match):
        if match.group(1).startswith("sound:"):
            # [sound:...] should not be replaced
            return match.group(0)
        # Return the furigana inside the brackets
        return match.group(1)

    # First remove all brackets and then remove all kanji
    # Assuming every kanji had furigana, we'll be left with the correct kana


def furigana_reverser(text):
    """
    Reverse the position of kanji and furigana in the text.
    :param text: The text to process
    :return: The text with kanji and furigana reversed
    """

    def bracket_reverser(match):
        if match.group(1).startswith("sound:"):
            # [sound:...] should not be reversed, do nothing
            return match.group(0)
        # Preserve leading space if present
        leading_space = " " if match.group(0).startswith(" ") else ""
        kanji = match.group(1)
        furigana = match.group(2)
        return f"{leading_space}{furigana}[{kanji}]"

    return re.sub(FURIGANA_REC, bracket_reverser, text.replace("&nbsp;", " "))


REPLACED_FURIGANA_MIDDLE_RE = re.compile(r"^(.+)<b>(.+)</b>(.+)$")
REPLACED_FURIGANA_RIGHT_RE = re.compile(r"^(.+)<b>(.+)</b>$")
REPLACED_FURIGANA_LEFT_RE = re.compile(r"^<b>(.+)</b>(.+)$")


def get_furigana_parts(
    furigana: str,
    edge: Edge,
    logger: Logger = Logger("error"),
) -> FuriganaParts:
    logger.debug(f"get_furigana_parts - furigana: {furigana}, edge: {edge}")
    result: FuriganaParts = {
        "has_highlight": "<b>" in furigana,
        "left_furigana": None,
        "middle_furigana": None,
        "right_furigana": None,
        "matched_edge": edge,
    }
    if edge == "whole":
        return result
    if match := REPLACED_FURIGANA_MIDDLE_RE.match(furigana):
        logger.debug(
            f"get_furigana_parts - middle match: {match.groups()}, edge was correct:"
            f" {edge == 'middle'}"
        )
        result["left_furigana"] = match.group(1)
        result["middle_furigana"] = match.group(2)
        result["right_furigana"] = match.group(3)
        result["matched_edge"] = "middle"
        return result
    elif match := REPLACED_FURIGANA_RIGHT_RE.match(furigana):
        logger.debug(
            f"get_furigana_parts - right match: {match.groups()}, edge was correct:"
            f" {edge == 'right'}"
        )
        result["left_furigana"] = match.group(1)
        result["middle_furigana"] = None
        result["right_furigana"] = match.group(2)
        result["matched_edge"] = "right"
        return result
    elif match := REPLACED_FURIGANA_LEFT_RE.match(furigana):
        logger.debug(
            f"get_furigana_parts - left match: {match.groups()}, edge was correct: {edge == 'left'}"
        )
        result["left_furigana"] = match.group(1)
        result["middle_furigana"] = None
        result["right_furigana"] = match.group(2)
        result["matched_edge"] = "left"
        return result

    # Nothing matched
    logger.debug("\nget_furigana_parts - no match")
    return result


def apply_katakana_conversion(text: str, preserve_tags: bool = True) -> str:
    """
    Convert hiragana content to katakana, optionally preserving XML-style tags.

    This is a unified helper for katakana conversion used throughout reconstruction.
    When preserve_tags=True, converts only the content within tags while preserving
    tag structure (e.g., <kun>もの</kun> → <kun>モノ</kun>).
    When preserve_tags=False, converts all text including tag markers.

    :param text: The text to convert
    :param preserve_tags: Whether to preserve XML-style tags
    :return: The converted text
    """
    if not text:
        return text

    if preserve_tags:
        # Convert content within tags while preserving tag markers
        def katakana_replacer(match):
            tag_open = match.group(1)  # e.g., "<kun>"
            content = match.group(3)  # The text content
            tag_close = match.group(4)  # e.g., "</kun>"
            return f"{tag_open}{to_katakana(content)}{tag_close}"

        # Match any tag with content (handles on, kun, juk, oku, mix, b, etc.)
        return re.sub(r"(<(on|kun|juk|oku|mix|b)>)([^<]+)(</\2>)", katakana_replacer, text)
    else:
        # Convert all text
        return to_katakana(text)


def reconstruct_furigana(
    furi_okuri_result: FinalResult,
    with_tags_def: WithTagsDef,
    reconstruct_type: FuriReconstruct = "furigana",
    force_merge: bool = False,
    logger: Logger = Logger("error"),
) -> str:
    """
    Reconstruct the furigana from the replace result

    :return: The reconstructed furigana with the kanji and that kanji's furigana highlighted
    """
    logger.debug(
        f"reconstruct_furigana - final_result: {furi_okuri_result}, reconstruct_type:"
        f" {reconstruct_type}, wrap_with_tags: {with_tags_def.with_tags}, merge_consecutive:"
        f" {with_tags_def.merge_consecutive}"
    )
    furigana = furi_okuri_result.get("furigana", "")
    okurigana = furi_okuri_result.get("okurigana", "")
    rest_kana = furi_okuri_result.get("rest_kana", "")
    left_word = furi_okuri_result.get("left_word", "")
    middle_word = furi_okuri_result.get("middle_word", "")
    right_word = furi_okuri_result.get("right_word", "")
    edge = furi_okuri_result.get("edge")
    match_type = furi_okuri_result.get("match_type", "none")
    # For backwards compatibility, also check highlight_match_type
    highlight_match_type = furi_okuri_result.get("highlight_match_type", match_type)

    # Keep okuri out of the highlight if it is not supposed to be included
    okuri_out_of_highlight = (
        not with_tags_def.include_suru_okuri
        and highlight_match_type == "onyomi"
        and (len(f"{left_word}{middle_word}{right_word}") > 1 or okurigana == "する")
    )
    if not edge:
        raise ValueError("reconstruct_furigana: edge missing in final_result")

    furigana_parts = get_furigana_parts(furigana, edge, logger=logger)
    logger.debug(f"reconstruct_furigana edge: {edge}, furigana_parts: {furigana_parts}")

    has_highlight = furigana_parts.get("has_highlight")
    left_furigana = furigana_parts.get("left_furigana")
    middle_furigana = furigana_parts.get("middle_furigana")
    right_furigana = furigana_parts.get("right_furigana")
    edge = furigana_parts.get("matched_edge")

    if not has_highlight:
        logger.debug("\nreconstruct_furigana - no highlight")
        # There was no match found during onyomi and kunyomi processing, so no<b> tags
        # For kana_only mode without merge_consecutive, we need to check if we have repeater kanji
        # that need to be processed by construct_wrapped_furi_word
        if reconstruct_type == "kana_only" and not with_tags_def.merge_consecutive:
            # Check if we have tags AND repeater kanji (々) - if so, we need to call construct_wrapped_furi_word
            # to properly combine the repeater pairs
            has_tags_in_furigana = "<" in furigana and ">" in furigana
            has_repeater = "々" in f"{left_word}{middle_word}{right_word}"
            if not (has_tags_in_furigana and has_repeater):
                # No tags or no repeater kanji, so we can just return the furigana as-is
                if with_tags_def.with_tags:
                    okurigana = f"<oku>{okurigana}</oku>" if okurigana else ""
                return f"{furigana}{okurigana}{rest_kana}"
        if with_tags_def.with_tags:
            # we need to extract the wrap tags from the furigana and include the word and
            # furigana within them. All words will need to be split into separate furigana
            # sections
            if edge == "whole":
                whole_word = f"{left_word}{middle_word}{right_word}"
                wrapped_whole_word = construct_wrapped_furi_word(
                    whole_word, furigana, reconstruct_type, with_tags_def.merge_consecutive
                )
            elif force_merge:
                if with_tags_def.with_tags:
                    okurigana = f"<oku>{okurigana}</oku>" if okurigana else ""
                if reconstruct_type == "kana_only":
                    if not with_tags_def.with_tags:
                        furigana = re.sub(r"<\w+>|</\w+>", "", furigana)
                    # If we're in kana_only mode, we just return the furigana
                    wrapped_whole_word = f"{furigana}{okurigana}{rest_kana}"
                else:
                    # Just merge the whole word with the furigana
                    # remove all tags from furigana and wrap everything with <mix> tags
                    furigana = re.sub(r"<\w+>|</\w+>", "", furigana)
                    whole_word = f"{left_word}{middle_word}{right_word}"
                    if with_tags_def.with_tags:
                        if reconstruct_type == "furigana":
                            wrapped_whole_word = f"<mix> {whole_word}[{furigana}]</mix>"
                        elif reconstruct_type == "furikanji":
                            wrapped_whole_word = f"<mix> {furigana}[{whole_word}]</mix>"
                    else:
                        if reconstruct_type == "furigana":
                            wrapped_whole_word = f" {whole_word}[{furigana}]"
                        elif reconstruct_type == "furikanji":
                            wrapped_whole_word = f" {furigana}[{whole_word}]"
                    wrapped_whole_word += okurigana + rest_kana
            else:
                wrapped_whole_word = ""
                for word, word_furigana in [
                    (left_word, left_furigana),
                    (middle_word, middle_furigana),
                    (right_word, right_furigana),
                ]:
                    if word and word_furigana:
                        wrapped_word = construct_wrapped_furi_word(
                            word, word_furigana, reconstruct_type, with_tags_def.merge_consecutive
                        )
                        wrapped_whole_word += wrapped_word

            logger.debug(
                f"reconstruct_furigana - whole_word: {left_word}{middle_word}{right_word},"
                f" furigana: {furigana}, wrapped_whole_word: {wrapped_whole_word}, okurigana:"
                f" {okurigana}, rest_kana: {rest_kana}"
            )

            okurigana = f"<oku>{okurigana}</oku>" if okurigana else ""
            return f"{wrapped_whole_word}{okurigana}{rest_kana}"

        # No tags case - apply katakana conversion if needed
        if reconstruct_type == "furikanji":
            return f" {furigana}[{left_word}{middle_word}{right_word}]{okurigana}{rest_kana}"
        return f" {left_word}{middle_word}{right_word}[{furigana}]{okurigana}{rest_kana}"

    if edge == "whole":
        logger.debug(
            f"reconstruct_furigana highlight whole word - before processing: edge: {edge},"
            f" okuri_out_of_highlight: {okuri_out_of_highlight}, okurigana: {okurigana}, rest_kana:"
            f" {rest_kana}"
        )
        # Same as above except we add the<b> tags around the whole thing
        # First remove<b> tags from the furigana
        furigana = re.sub(r"<b>|</b>", "", furigana)
        whole_word = f"{left_word}{middle_word}{right_word}"
        if with_tags_def.with_tags:
            wrapped_word = construct_wrapped_furi_word(
                whole_word, furigana, reconstruct_type, with_tags_def.merge_consecutive
            )
            okurigana = f"<oku>{okurigana}</oku>" if okurigana else ""
            if okuri_out_of_highlight:
                return f"<b>{wrapped_word}</b>{okurigana}{rest_kana}"
            return f"<b>{wrapped_word}{okurigana}</b>{rest_kana}"

        if okuri_out_of_highlight:
            rest_kana = f"{okurigana}{rest_kana}"
            okurigana = ""
        if reconstruct_type == "kana_only":
            return f"<b>{furigana}{okurigana}</b>{rest_kana}"
        if reconstruct_type == "furikanji":
            return f"<b> {furigana}[{whole_word}]{okurigana}</b>{rest_kana}"
        return f"<b> {whole_word}[{furigana}]{okurigana}</b>{rest_kana}"

    # There is highlighting, split the furigana and word into three parts and assemble them
    result = ""
    parts = [
        # The furigana and word parts should match exactly;
        # when one is missing so is the other
        (left_word, left_furigana, "left"),
        (middle_word, middle_furigana, "middle"),
        (right_word, right_furigana, "right"),
    ]
    logger.debug(
        f"reconstruct_furigana with highlight in parts - before processing: {parts}, edge: {edge},"
        f" okuri_out_of_highlight: {okuri_out_of_highlight}, okurigana: {okurigana}, rest_kana:"
        f" {rest_kana}"
    )
    for word, word_furigana, word_edge in parts:
        logger.debug(
            f"reconstruct_furigana - word: {word}, word_furigana: {word_furigana},"
            f" word_edge: {word_edge}"
        )
        if word and word_furigana:
            if with_tags_def.with_tags:
                part = construct_wrapped_furi_word(
                    word, word_furigana, reconstruct_type, with_tags_def.merge_consecutive
                )
            elif reconstruct_type == "kana_only":
                part = f"{word_furigana}"
            elif reconstruct_type == "furikanji":
                part = f" {word_furigana}[{word}]"
            else:
                part = f" {word}[{word_furigana}]"
            # If this is the edge that was matched, add the bold tags while
            # removing the existing ones in the furigana
            part = re.sub(r"<b>|</b>", "", part)
            if word_edge == "right":
                # If we're at the end, add the okurigana
                if not okuri_out_of_highlight:
                    if with_tags_def.with_tags:
                        part += f"<oku>{okurigana}</oku>" if okurigana else ""
                    else:
                        part += okurigana
                else:
                    # If we're not supposed to add する okuri, and the part ends with </on>,
                    # then we know the okurigana contains する inflections, if it's non-empty
                    # In any case, just add okuri to rest kana so we don't highlight it
                    if with_tags_def.with_tags:
                        rest_kana = f"<oku>{okurigana}</oku>{rest_kana}" if okurigana else rest_kana
                    else:
                        rest_kana = f"{okurigana}{rest_kana}"
            if edge == word_edge:
                # Finally, add the highlighting if this is the edge that was matched
                part = f"<b>{part}</b>"
            result += part
    logger.debug(
        f"reconstruct_furigana with highlight - result after parts: {result}, okurigana:"
        f" {okurigana}, rest_kana: {rest_kana}"
    )
    if (
        with_tags_def.with_tags
        and rest_kana
        and match_type == "kunyomi"
        and edge in ["left", "right"]
        and rest_kana[0] in {"る", "う", "た", "て", "っ", "い", "く"}
    ):
        rest_kana = f"<oku>{rest_kana}</oku>"
    return f"{result}{rest_kana}"


MatchProcess = Literal["replace", "match", "juku"]


def is_reading_in_furigana_section(
    reading: str,
    furigana_section: str,
    check_in_katakana: bool,
    okurigana: str,
    edge: Edge,
    logger: Logger = Logger("error"),
) -> Tuple[str, ReadingType]:
    """
    Function that checks if a reading is in the furigana section

    :return: str, the reading that matched the furigana section
    """
    if not reading:
        return "", "none"
    # The reading might have a match with a changed kana like シ->ジ, フ->プ, etc.
    # This only applies to the first kana in the reading and if the reading isn't a single kana
    rendaku_readings = []
    rendaku_dict = (
        RENDAKU_CONVERSION_DICT_KATAKANA if check_in_katakana else RENDAKU_CONVERSION_DICT_HIRAGANA
    )
    if possible_rendaku_kana := rendaku_dict.get(reading[0]):
        for kana in possible_rendaku_kana:
            rendaku_readings.append(f"{kana}{reading[1:]}")
    # Then also check for small tsu conversion of some consonants
    # this only happens in the last kana of the reading
    small_tsu_readings = []
    small_tsu_list = (
        SMALL_TSU_POSSIBLE_KATAKANA if check_in_katakana else SMALL_TSU_POSSIBLE_HIRAGANA
    )
    for kana in small_tsu_list:
        if reading[-1] == kana:
            small_tsu_readings.append(f"{reading[:-1]}っ")
    # Handle う-->っ cases, these can have the っ in the okurigana so it's more like
    # the う is dropped in these cases. So, check if the first okuri char is っ and this
    # reading ends in う. If so, add a reading with う removed
    # These only apply when the okuri could belong to this reading, so "whole" or "right" edge
    u_dropped_readings = []
    if okurigana and okurigana[0] == "っ" and reading[-1] == "う":
        u_dropped_readings.append(f"{reading[:-1]}")
        for rendaku_reading in rendaku_readings:
            u_dropped_readings.append(f"{rendaku_reading[:-1]}")
    # Handle vowel change
    vowel_change_readings = []
    vowel_change_dict = (
        VOWEL_CHANGE_DICT_KATAKANA if check_in_katakana else VOWEL_CHANGE_DICT_HIRAGANA
    )
    if reading[0] in vowel_change_dict:
        for kana in vowel_change_dict[reading[0]]:
            vowel_change_readings.append(f"{kana}{reading[1:]}")

    if edge == "whole":
        # match the whole furigana or repeat twice in it, possibly with rendaku or small tsu
        # (eg. the next kanji is the same or 々)
        if reading == furigana_section:
            return reading, "plain"
        for u_dropped_reading in u_dropped_readings:
            if u_dropped_reading == furigana_section:
                return u_dropped_reading, "small_tsu"
        if reading * 2 == furigana_section:
            return reading * 2, "plain"
        for rendaku_reading in rendaku_readings:
            if rendaku_reading == furigana_section:
                return rendaku_reading, "rendaku"
            if f"{reading}{rendaku_reading}" == furigana_section:
                return f"{reading}{rendaku_reading}", "rendaku"
        for small_tsu_reading in small_tsu_readings:
            if small_tsu_reading == furigana_section:
                return small_tsu_reading, "small_tsu"
            if f"{small_tsu_reading}{reading}" == furigana_section:
                return f"{small_tsu_reading}{reading}", "small_tsu"
        for vowel_change_reading in vowel_change_readings:
            if vowel_change_reading == furigana_section:
                return vowel_change_reading, "vowel_change"
        return "", "none"
    # For non-whole edge, also check readings are both rendaku and small tsu
    rendaku_small_tsu_readings = []
    for rendaku_reading in rendaku_readings:
        for kana in SMALL_TSU_POSSIBLE_HIRAGANA:
            if rendaku_reading[-1] == kana:
                rendaku_small_tsu_readings.append(f"{rendaku_reading[:-1]}っ")
    all_readings = (
        [(reading, "plain")]
        + [(r, "rendaku") for r in rendaku_readings]
        + [(r, "small_tsu") for r in small_tsu_readings]
        + [(r, "rendaku_small_tsu") for r in rendaku_small_tsu_readings]
        + [(r, "vowel_change") for r in vowel_change_readings]
    )
    if edge == "left":
        logger.debug(
            f"check_reading_in_furigana_section - left edge, furigana_section: {furigana_section}"
            f", all_readings: {all_readings}"
        )
        for r, t in all_readings:
            if furigana_section.startswith(r):
                return r, cast(ReadingType, t)
        return "", "none"
    if edge == "right":
        for r, t in all_readings:
            if furigana_section.endswith(r):
                return r, cast(ReadingType, t)
        for u_dropped_reading in u_dropped_readings:
            if u_dropped_reading == furigana_section:
                return u_dropped_reading, "small_tsu"
        return "", "none"
    # middle
    for r, t in all_readings:
        if r in furigana_section:
            return r, cast(ReadingType, t)
    return "", "none"


def check_onyomi_readings(
    onyomi: str,
    furigana: str,
    word_data: WordData,
    highlight_args: HighlightArgs,
    target_furigana_section: str,
    edge: Edge,
    wrap_readings_with_tags: bool = True,
    convert_to_katakana: bool = True,
    process_type: MatchProcess = "match",
    skip_reading: Optional[str] = None,
    logger: Logger = Logger("error"),
) -> YomiMatchResult:
    """
    Function that checks the onyomi readings against the target furigana section

    :return: string, the modified furigana
      or [True, False] when return_on_or_kun_match_only
    """
    if not onyomi:
        return {
            "text": "",
            "type": "none",
            "match_edge": "none",
            "actual_match": "",
            "matched_reading": "",
            "all_readings_processed": True,
        }
    onyomi_readings = onyomi.split("、")
    # order readings by length so that we try to match the longest reading first
    onyomi_readings.sort(key=len, reverse=True)
    okurigana = word_data.get("okurigana", "")

    logger.debug(
        f"check_onyomi_readings - target_furigana_section: {target_furigana_section}, edge: {edge}"
    )

    # Exception for 麻雀[まーじゃん] where 麻[まー] should be a jukujikun, and we don't want to
    # match ま as a onyomi
    if furigana == "まーじゃん":
        return {
            "text": "",
            "type": "none",
            "match_edge": "none",
            "actual_match": "",
            "matched_reading": "",
            "all_readings_processed": True,
        }

    # Exception for 菠薐草[ほうれんそう] where ほうれん should be a jukujikun, but 菠 has the onyomi
    # ほ which would get incorrectly matched here
    if furigana.startswith("ほうれん") and highlight_args.get("kanji_to_match") == "菠":
        return {
            "text": "",
            "type": "none",
            "match_edge": "none",
            "actual_match": "",
            "matched_reading": "",
            "all_readings_processed": True,
        }

    skip_reading_found = False
    for reading_index, onyomi_reading in enumerate(onyomi_readings):
        # remove text in () in the reading
        onyomi_reading = re.sub(r"\(.*?\)", "", onyomi_reading).strip()
        logger.debug(f"check_onyomi_readings 1 - onyomi_reading: {onyomi_reading}")
        if not onyomi_reading:
            continue

        # Skip readings that have been tried before
        if skip_reading and not skip_reading_found:
            if onyomi_reading == skip_reading:
                skip_reading_found = True
                logger.debug(f"check_onyomi_readings - skipping reading: {onyomi_reading}")
            # We skip until we find the reading to skip, and the next reading will have
            # skip_reading_found=True and won't be skipped
            continue

        furigana_is_katakana = word_data.get("furigana_is_katakana", False)
        match_in_section, match_type = is_reading_in_furigana_section(
            onyomi_reading if furigana_is_katakana else to_hiragana(onyomi_reading),
            target_furigana_section,
            furigana_is_katakana,
            okurigana,
            edge,
            logger=logger,
        )
        logger.debug(
            f"check_onyomi_readings 2 - onyomi_reading: {onyomi_reading}, in_section:"
            f" {match_in_section}, type: {match_type}"
        )
        is_last_reading = reading_index == len(onyomi_readings) - 1
        if match_in_section:
            return {
                "text": process_onyomi_match(
                    furigana,
                    match_in_section,
                    edge,
                    process_type,
                    wrap_readings_with_tags,
                    convert_to_katakana,
                ),
                "type": "onyomi",
                "match_edge": edge,
                "actual_match": match_in_section,
                "matched_reading": onyomi_reading,
                "all_readings_processed": is_last_reading,
            }
    return {
        "text": "",
        "type": "none",
        "match_edge": "none",
        "actual_match": "",
        "matched_reading": "",
        "all_readings_processed": True,
    }


def process_onyomi_match(
    furigana: str,
    onyomi_that_matched: str,
    edge: Edge,
    process_type: MatchProcess,
    wrap_readings_with_tags: bool,
    convert_to_katakana: bool,
) -> str:
    """
    Function that replaces the furigana with the onyomi reading that matched

    :return: string, the modified furigana or the matched part, depending on the process_type
    """
    if edge == "right":
        reg = re_match_from_right(onyomi_that_matched)
    elif edge == "left":
        reg = re_match_from_left(onyomi_that_matched)
    else:
        reg = re_match_from_middle(onyomi_that_matched)
    if process_type == "match":
        match = reg.match(furigana)
        if match:
            return to_katakana(match.group(2)) if convert_to_katakana else match.group(2)
        # return nothing if we have no match
        return ""
    replacer = partial(
        onyomi_replacer,
        wrap_readings_with_tags=wrap_readings_with_tags,
        convert_to_katakana=convert_to_katakana,
    )
    return re.sub(reg, replacer, furigana)


def check_kunyomi_readings(
    highlight_args: HighlightArgs,
    word_data: WordData,
    furigana: str,
    target_furigana_section: str,
    edge: Edge,
    wrap_readings_with_tags: bool = True,
    process_type: MatchProcess = "match",
    skip_reading: Optional[str] = None,
    logger: Logger = Logger("error"),
) -> YomiMatchResult:
    """
    Function that checks the kunyomi readings against the target furigana section and okurigana

    :return: Result dict with the modified furigana
    """
    kunyomi = highlight_args.get("kunyomi", "")
    if not kunyomi:
        return {
            "text": "",
            "type": "none",
            "match_edge": "none",
            "actual_match": "",
            "matched_reading": "",
            "all_readings_processed": True,
        }

    kunyomi_readings = kunyomi.split("、")
    skip_reading_found = False
    stem_match_results: list[YomiMatchResult] = []
    kunyomi_stems: set[Tuple[str, str]] = set()
    kunyomi_stem_and_okuris: list[Tuple[str, str, str]] = []
    furigana_is_katakana = word_data.get("furigana_is_katakana", False)
    for reading_index, kunyomi_reading in enumerate(kunyomi_readings):
        if not kunyomi_reading:
            continue
        kunyomi_reading = to_hiragana(kunyomi_reading)
        logger.debug(f"check_kunyomi_readings - kunyomi_reading: {kunyomi_reading}")

        # Skip readings that have been tried before
        if skip_reading and not skip_reading_found:
            if kunyomi_reading == skip_reading:
                skip_reading_found = True
                logger.debug(f"check_kunyomi_readings - skipping reading: {kunyomi_reading}")
            # We skip until we find the reading to skip, and the next reading will have
            # skip_reading_found=True and won't be skipped
            continue

        # Split the reading into the stem and the okurigana
        kunyomi_stem = kunyomi_reading
        kunyomi_dict_form_okuri = ""
        if "." in kunyomi_reading:
            try:
                kunyomi_stem, kunyomi_dict_form_okuri = kunyomi_reading.split(".")
            except ValueError:
                logger.debug(
                    "\nError in kana_highlight[]: kunyomi contained multiple dots:"
                    f" {kunyomi_reading}"
                )
                return {
                    "text": furigana,
                    "type": "kunyomi",
                    "match_edge": edge,
                    "actual_match": "",
                    "matched_reading": "",
                    "all_readings_processed": reading_index == len(kunyomi_readings) - 1,
                }
        # We only need to check unique stems
        if furigana_is_katakana:
            kunyomi_stem = to_katakana(kunyomi_stem)
        kunyomi_stems.add((kunyomi_stem, kunyomi_reading))
        # And noun forms for readings that have okuri
        if kunyomi_dict_form_okuri:
            kunyomi_stem_and_okuris.append((kunyomi_stem, kunyomi_dict_form_okuri, kunyomi_reading))

    kanji_to_match = highlight_args.get("kanji_to_match", "")
    if kanji_to_match == "為":
        # Special case for 為, add し as a stem
        for suru_stem in ["し", "さ"]:
            kunyomi_stems.add((suru_stem, "す.る"))
            kunyomi_stem_and_okuris.append((suru_stem, "", "す.る"))
            if furigana_is_katakana:
                kunyomi_stems.add((to_katakana(suru_stem), "す.る"))
                kunyomi_stem_and_okuris.append((to_katakana(suru_stem), "", "す.る"))

    okurigana = word_data.get("okurigana", "")
    # First check matches against the stem
    for kunyomi_stem, full_reading in kunyomi_stems:
        if not kunyomi_stem:
            continue
        match_in_section, match_type = is_reading_in_furigana_section(
            kunyomi_stem,
            target_furigana_section,
            furigana_is_katakana,
            okurigana,
            edge,
            logger=logger,
        )
        logger.debug(
            f"check_kunyomi_readings - kunyomi_stem: {kunyomi_stem}, in_section:"
            f" {match_in_section}, type: {match_type}"
        )
        if match_in_section:
            stem_match_results.append({
                "text": process_kunyomi_match(
                    furigana,
                    match_in_section,
                    edge,
                    process_type,
                    wrap_readings_with_tags,
                ),
                "match_edge": edge,
                "type": "kunyomi",
                "actual_match": match_in_section,
                "matched_reading": full_reading,
            })
    kanji_to_match = highlight_args.get("kanji_to_match", "")

    # Then also readings with okurigana included in the furigana, noun forms and others
    # In this case there should be no okurigana as it would be a reading where those are omitted
    # e.g. 曳舟--曳き舟, 取調--取り調べ, 書留--書き留め
    okuri_included_results: list[YomiMatchResult] = []
    for kunyomi_stem, kunyomi_dict_form_okuri, full_reading in kunyomi_stem_and_okuris:
        noun_form_okuri = get_verb_noun_form_okuri(
            kunyomi_dict_form_okuri, kanji_to_match, kunyomi_reading
        )
        logger.debug(
            f"check_kunyomi_readings - kunyomi_stem: {kunyomi_stem}, kunyomi_dict_form_okuri:"
            f" {kunyomi_dict_form_okuri}\nokurigana: {okurigana}, kanji_to_match:"
            f" {kanji_to_match}, noun_form_okuri: {noun_form_okuri}"
        )
        if furigana_is_katakana:
            noun_form_okuri = to_katakana(noun_form_okuri)
        okuris_in_furi = [kunyomi_dict_form_okuri, noun_form_okuri]
        for okuri_in_furi in okuris_in_furi:
            if (
                (not okurigana and edge in ["right", "whole"]) or (edge in ["left", "middle"])
            ) and kunyomi_dict_form_okuri:
                # Replace last kana in dict form okuri with the noun form ending
                okuri_included_reading = f"{kunyomi_stem}{kunyomi_dict_form_okuri}"
                if okuri_in_furi:
                    okuri_included_reading = f"{kunyomi_stem}{okuri_in_furi}"
                match_in_section, match_type = is_reading_in_furigana_section(
                    okuri_included_reading,
                    target_furigana_section,
                    furigana_is_katakana,
                    okurigana,
                    edge,
                    logger=logger,
                )
                logger.debug(
                    f"check_kunyomi_readings - okuri_included form: {okuri_included_reading},"
                    f" in_section: {match_in_section}, type: {match_type}"
                )
                if match_in_section:
                    okuri_included_results.append({
                        "text": process_kunyomi_match(
                            furigana,
                            match_in_section,
                            edge,
                            process_type,
                            wrap_readings_with_tags,
                        ),
                        "match_edge": edge,
                        "type": "kunyomi",
                        "actual_match": match_in_section,
                        "matched_reading": full_reading,
                    })
    logger.debug(
        f"check_kunyomi_readings - stem_match_results: {stem_match_results},"
        f" okuri_included_results: {okuri_included_results}"
    )
    # If both results are found, return the one with the longest match
    results_by_length: list[list[YomiMatchResult]] = []
    for result in stem_match_results + okuri_included_results:
        result_length = len(result["actual_match"])
        while len(results_by_length) < result_length:
            results_by_length.append([])
        results_by_length[result_length - 1].append(result)
    if results_by_length:
        longest_results = results_by_length[-1]
        # Even if there are multiple results with the same length, just return the first one
        # they all have the same kana, after all
        return longest_results[0]

    # No match for either check exceptions...

    # Exception for 尻尾[しっぽ] where 尾[ぽ] should be considered a kunyomi, not jukujikun
    # 尻 already gets matched with small tsu conversion so handle 尾[ぽ] here
    if highlight_args["kanji_to_match"] == "尾" and furigana == "ぽ":
        return {
            "text": process_kunyomi_match(
                furigana,
                "ぽ",
                edge,
                process_type,
                wrap_readings_with_tags,
            ),
            "match_edge": edge,
            "type": "kunyomi",
            "actual_match": "ぽ",
            "matched_reading": "ほ",
            "all_readings_processed": True,
        }
    logger.debug("\ncheck_kunyomi_readings - no match")
    return {
        "text": "",
        "type": "none",
        "match_edge": "none",
        "actual_match": "",
        "matched_reading": "",
        "all_readings_processed": True,
    }


def process_kunyomi_match(
    furigana: str,
    kunyomi_that_matched: str,
    edge: Edge,
    process_type: MatchProcess,
    wrap_readings_with_tags: bool,
) -> str:
    """
    Function that replaces the furigana with the kunyomi reading that matched
    :return: string, the modified furigana or the matched part, depending on the process_type
    """
    if edge == "right":
        reg = re_match_from_right(kunyomi_that_matched)
    elif edge == "left":
        reg = re_match_from_left(kunyomi_that_matched)
    else:
        reg = re_match_from_middle(kunyomi_that_matched)
    if process_type == "match":
        match = reg.match(furigana)
        if match:
            return match.group(2)
        return ""
    replacer = partial(kunyomi_replacer, wrap_readings_with_tags=wrap_readings_with_tags)
    return re.sub(reg, replacer, furigana)


def handle_furigana_doubling(
    partial_result: YomiMatchResult,
    cur_furigana_section: str,
    matched_furigana: str,
    check_in_katakana: bool,
    onyomi_to_katakana: bool = True,
    logger: Logger = Logger("error"),
) -> str:
    """
    Function that handles the case of a word with doubled furigana, due it using the repeater
    kanji 々.
    """
    doubled_furigana = ""
    # If this was a normal match, the furigana should be repeating
    # check if there's rendaku in the following furigana
    furigana_after_matched = cur_furigana_section[len(matched_furigana) :]
    rendaku_conversion_dict = (
        RENDAKU_CONVERSION_DICT_KATAKANA if check_in_katakana else RENDAKU_CONVERSION_DICT_HIRAGANA
    )
    rendaku_matched_furigana = (
        [f"{kana}{matched_furigana[1:]}" for kana in rendaku_conversion_dict[matched_furigana[0]]]
        if matched_furigana[0] in rendaku_conversion_dict
        else []
    )
    rendaku_matched_furigana.append(to_hiragana(matched_furigana))  # Add the original
    logger.debug(
        f"repeater kanji - doubling furigana: {matched_furigana},"
        f" furigana_after_matched: {furigana_after_matched},"
        f" rendaku_matched_furigana:{rendaku_matched_furigana}"
    )
    if furigana_after_matched:
        for rf in rendaku_matched_furigana:
            if furigana_after_matched.startswith(rf):
                doubled_furigana = matched_furigana + (
                    to_katakana(rf)
                    if partial_result["match_type"] == "onyomi" and onyomi_to_katakana
                    else rf
                )
                logger.debug(
                    f"repeater kanji - found rendaku match: {rf} in"
                    f" furigana_after_matched: {furigana_after_matched}"
                )
                break
    else:
        logger.debug(
            "repeater kanji - no furigana_after_matched, simply doubling with"
            f" matched_furigana: {matched_furigana}"
        )
        doubled_furigana = matched_furigana * 2

    return doubled_furigana


def handle_jukujikun_case(
    word_data: WordData,
    highlight_args: HighlightArgs,
    wrap_readings_with_tags: bool,
    logger: Logger = Logger("error"),
) -> YomiMatchResult:
    """
    Function that handles the case of a jukujikun/ateji word where the furigana
    doesn't match the onyomi or kunyomi. Highlights the part of the furigana matching
    the kanji position
    :return: Result dict with the modified furigana
    """
    kanji_to_highlight = highlight_args.get("kanji_to_highlight", "")
    kanji_count = word_data.get("kanji_count", 0)
    word = word_data.get("word", "")
    try:
        assert kanji_count > 0, (
            f"handle_jukujikun_case[]: incorrect kanji_count: {word_data.get('kanji_count')}, word:"
            f" {word}, kanji_to_highlight: {kanji_to_highlight}"
        )
    except AssertionError as e:
        logger.error(e)
        return {
            "text": word_data.get("furigana", ""),
            "type": "none",
            "match_edge": word_data.get("edge", "none"),
            "actual_match": "",
            "matched_reading": "",
        }
    kanji_pos = word.find(kanji_to_highlight) if kanji_to_highlight else -1
    # kanji_pos can be -1, in which case no highlighting happens
    assert kanji_pos < kanji_count, (
        f"handle_jukujikun_case[]: incorrect kanji_pos: {kanji_pos}, kanji_to_highlight:"
        f" {kanji_to_highlight}"
    )
    furigana = word_data.get("furigana", "")

    # First split the word into mora
    is_furigana_in_katakana = KATAKANA_REC.match(furigana) is not None
    if is_furigana_in_katakana:
        furigana = to_hiragana(furigana)
    mora_list = ALL_MORA_REC.findall(furigana)
    # Merge ん with the previous mora into a new list except when it would result in less more than
    # kanji
    if "ん" in mora_list and len(mora_list) > kanji_count:
        new_list: list[str] = []
        new_list_index = 0
        for mora in mora_list:
            if mora == "ん" and new_list_index > 0:
                new_list[new_list_index - 1] += mora
            else:
                new_list.append(mora)
                new_list_index += 1
        mora_list = new_list

    logger.debug(f"handle_jukujikun_case - mora_list: {mora_list}")
    # Divide the mora by the number of kanji in the word
    mora_count = len(mora_list)
    mora_per_kanji = mora_count // kanji_count
    # Split the remainder evenly among the kanji,
    # by adding one mora to each kanji until the remainder is 0
    remainder = mora_count % kanji_count
    new_furigana = ""
    match_edge: Edge = "left"
    cur_mora_index = 0
    kanji_index = 0
    actual_match = ""
    is_kanji_match = False
    while kanji_index < kanji_count:
        next_kanji = word[kanji_index + 1] if kanji_index < kanji_count - 1 else ""
        cur_mora_range_max = cur_mora_index + mora_per_kanji
        is_rep_kanji = next_kanji == "々"
        logger.debug(
            f"juku mora 1, kanji_index: {kanji_index}, kanji_pos: {kanji_pos}, cur_mora_index:"
            f" {cur_mora_index}, cur_mora_range_max: {cur_mora_range_max}, mora_per_kanji:"
            f" {mora_per_kanji}, remainder: {remainder}, cur_kanji: {word[kanji_index]} next_kanji:"
            f" {next_kanji}"
        )
        if is_rep_kanji:
            # If the next kanji is the repeater, this tag should get one set of mora
            cur_mora_range_max += mora_per_kanji
        if remainder > 0:
            cur_mora_range_max += 1
            remainder -= 1
        is_kanji_match = kanji_index == kanji_pos
        if is_kanji_match:
            new_furigana += "<b>"
            if kanji_index == 0:
                match_edge = "left"
            elif kanji_index == kanji_count - 1:
                match_edge = "right"
            else:
                match_edge = "middle"
        elif kanji_index == kanji_pos + 1 and kanji_pos != -1:
            logger.debug(
                f"juku mora 3 closing bold - kanji_index: {kanji_index}, kanji_pos: {kanji_pos},"
                f" has_bold: {new_furigana[-3:] == '<b>'}, new_furigana: {new_furigana}"
            )
            new_furigana += "</b>" if new_furigana[-4:] != "</b>" else ""

        mora = "".join(mora_list[cur_mora_index:cur_mora_range_max])
        logger.debug(f"juku mora 2 - mora: {mora}")
        if wrap_readings_with_tags:
            new_furigana += f"<juk>{mora}</juk>"
        else:
            new_furigana += mora
        if is_kanji_match:
            actual_match = mora
        logger.debug(f"juku mora 5 - new_furigana: {new_furigana}")

        if kanji_index == kanji_pos:
            logger.debug(
                f"juku mora 4 closing bold - kanji_index: {kanji_index}, kanji_pos: {kanji_pos},"
                f" has_bold: {new_furigana[-3:] == '<b>'}, new_furigana: {new_furigana}"
            )
            new_furigana += "</b>" if new_furigana[-4:] != "</b>" else ""
        cur_mora_index = cur_mora_range_max
        if is_rep_kanji:
            # Skip the next kanji since it's the repeater and we handled it already
            kanji_index += 2
        else:
            kanji_index += 1
    logger.debug(f"handle_jukujikun_case - new_furigana: {new_furigana}")
    if is_furigana_in_katakana:
        new_furigana = to_katakana(new_furigana)
    return {
        "text": new_furigana,
        "type": "jukujikun",
        "match_edge": match_edge,
        "actual_match": actual_match,
        "matched_reading": "",
    }


def reconstruct_from_alignment(
    word: str,
    alignment: MoraAlignment,
    juku_parts: dict[int, str],
    kanji_to_highlight: str,
    with_tags_def: WithTagsDef,
    okurigana: str,
    rest_kana: str,
    was_katakana: bool,
    reconstruct_type: FuriReconstruct,
    logger: Logger = Logger("error"),
) -> str:
    """
    Build furigana string from mora alignment and jukujikun parts.

    Combines matched readings with jukujikun portions, applies tags, handles
    katakana conversion, and builds the final FinalResult structure.

    :param word: The full word being processed
    :param alignment: MoraAlignment result with kanji_matches
    :param juku_parts: Dictionary mapping kanji_index → jukujikun furigana portion
    :param kanji_to_highlight: The kanji character to highlight with <b> tags
    :param with_tags_def: Tag configuration (with_tags, merge_consecutive, onyomi_to_katakana)
    :param okurigana: The okurigana portion (from alignment or jukujikun extraction)
    :param rest_kana: The remaining kana after okurigana
    :param was_katakana: Whether original furigana was in katakana
    :param logger: Logger for debugging
    :return: FinalResult with complete furigana and word parts
    """
    furigana_parts: list[str] = []
    alignment_len = len(alignment["kanji_matches"])
    word_len = len(word)

    def compress_numeric_runs(text: str) -> str:
        return re.sub(r"[0-9０-９]+", lambda m: number_to_kanji(m.group(0)), text)

    word_for_alignment = word
    if alignment_len != word_len:
        # When the word contains numeric characters, the alignment is done on kanji
        # with numeric characters converted to kanji numerals
        word_for_alignment = compress_numeric_runs(word)
    kanji_to_highlight_pos = (
        word_for_alignment.find(kanji_to_highlight) if kanji_to_highlight else -1
    )

    # Build furigana by concatenating each kanji's portion
    for i, kanji in enumerate(word_for_alignment):
        # Check if this is jukujikun or matched reading
        if i in juku_parts:
            # Jukujikun portion (already tagged if with_tags=True)
            part = juku_parts[i]
            if was_katakana:
                # Convert inner juku reading to katakana to preserve original script
                if with_tags_def.with_tags and part.startswith("<juk>"):
                    inner = part.replace("<juk>", "").replace("</juk>", "")
                    inner_kata = to_katakana(inner)
                    part = f"<juk>{inner_kata}</juk>"
                else:
                    part = to_katakana(part)
            furigana_parts.append(part)
        elif alignment["kanji_matches"][i]:
            # Matched reading
            match_info = alignment["kanji_matches"][i]
            reading = match_info["matched_mora"]
            match_type = match_info["match_type"]

            # Apply selective katakana conversion for onyomi
            if with_tags_def.onyomi_to_katakana and match_type == "onyomi":
                reading = to_katakana(reading)

            # Wrap in type tags if requested (EACH KANJI gets its own tag)
            if with_tags_def.with_tags:
                if match_type == "onyomi":
                    reading = f"<on>{reading}</on>"
                elif match_type == "kunyomi":
                    reading = f"<kun>{reading}</kun>"
                elif match_type == "jukujikun":
                    # Preserve original script: if original furigana was katakana, convert juku
                    if was_katakana:
                        reading = to_katakana(reading)
                    reading = f"<juk>{reading}</juk>"

            furigana_parts.append(reading)
        else:
            # This shouldn't happen if juku_parts is complete, but handle it
            logger.error(
                f"reconstruct_from_alignment: No match or juku_part for kanji {kanji} at index {i}"
            )
            furigana_parts.append("")

    # Join all parts
    complete_furigana = "".join(furigana_parts)

    if (
        with_tags_def.with_tags
        and with_tags_def.merge_consecutive
        and reconstruct_type == "kana_only"
    ):
        pattern = re.compile(r"<(on|kun|juk)>(.*?)</\1><\1>(.*?)</\1>")

        def merge_same_tags(text: str) -> str:
            while True:
                new_text = pattern.sub(
                    lambda m: f"<{m.group(1)}>{m.group(2)}{m.group(3)}</{m.group(1)}>", text
                )
                if new_text == text:
                    return new_text
                text = new_text

        complete_furigana = merge_same_tags(complete_furigana)

    # Uniform script conversion when original furigana was katakana
    if was_katakana:
        if with_tags_def.with_tags:
            complete_furigana = apply_katakana_conversion(complete_furigana, preserve_tags=True)
        else:
            complete_furigana = to_katakana(complete_furigana)

        if okurigana:
            okurigana = to_katakana(okurigana)
        if rest_kana:
            rest_kana = to_katakana(rest_kana)

    # Add <b> tags around portion where kanji_to_highlight appears
    if kanji_to_highlight and kanji_to_highlight_pos >= 0:
        # Find which furigana portion corresponds to kanji_to_highlight_pos
        # We need to insert <b> before and </b> after the corresponding portion
        # If next kanji is repeater (々), include both portions in highlight
        highlight_end_pos = kanji_to_highlight_pos + 1
        if (
            kanji_to_highlight_pos + 1 < len(word_for_alignment)
            and word_for_alignment[kanji_to_highlight_pos + 1] == "々"
        ):
            highlight_end_pos = kanji_to_highlight_pos + 2

        portions_before = furigana_parts[:kanji_to_highlight_pos]
        highlight_portions = furigana_parts[kanji_to_highlight_pos:highlight_end_pos]
        portions_after = furigana_parts[highlight_end_pos:]

        logger.debug(
            f"reconstruct_from_alignment - word: {word_for_alignment}, kanji_to_highlight_pos:"
            f" {kanji_to_highlight_pos}, highlight_end_pos: {highlight_end_pos}, furigana_parts:"
            f" {furigana_parts}, highlight_portions: {highlight_portions}"
        )
        before_text = "".join(portions_before)
        highlight_text = "".join(highlight_portions)
        after_text = "".join(portions_after)

        complete_furigana = f"{before_text}<b>{highlight_text}</b>{after_text}"

    # Determine edge position
    edge: Edge = "whole"
    if kanji_to_highlight and kanji_to_highlight_pos >= 0:
        # Check if next character is repeater - if so, the pair extends the highlighted portion
        has_repeater_after = (
            kanji_to_highlight_pos + 1 < len(word_for_alignment)
            and word_for_alignment[kanji_to_highlight_pos + 1] == "々"
        )
        effective_end_pos = (
            kanji_to_highlight_pos + 2 if has_repeater_after else kanji_to_highlight_pos + 1
        )

        if kanji_to_highlight_pos == 0:
            # At the start - could be left or whole edge
            if effective_end_pos >= len(word_for_alignment):
                edge = "whole"  # Repeater pair covers whole word
            else:
                edge = "left"
        elif effective_end_pos >= len(word_for_alignment):
            # At or extends to the end
            edge = "right"
        else:
            edge = "middle"

    # Build word parts based on edge position
    # The naming is based on the parts array structure used in reconstruct_furigana:
    # [(left_word, left_furigana, "left"), (middle_word, middle_furigana, "middle"), (right_word, right_furigana, "right")]
    # - For edge == "left": left_word = highlighted kanji, right_word = rest of word, middle_word = ""
    # - For edge == "right": left_word = beginning of word, right_word = highlighted kanji, middle_word = ""
    # - For edge == "middle": left_word = before highlight, middle_word = highlighted, right_word = after highlight
    # - For edge == "whole": middle_word = full word, left_word = "", right_word = ""
    #
    # NOTE: When a repeater (々) follows the highlighted kanji, both characters are included in the
    # highlighted word part to match the furigana which has both readings in the <b> tags.
    word_output = word if word else word_for_alignment

    if kanji_to_highlight_pos < 0:
        # No highlighting - put full word in middle_word for "whole" edge compatibility
        left_word = ""
        middle_word = word_output
        right_word = ""
    elif edge == "whole":
        # Entire word is highlighted
        left_word = ""
        middle_word = word_output
        right_word = ""
    elif edge == "left":
        # Include repeater if present
        if (
            kanji_to_highlight_pos + 1 < len(word_for_alignment)
            and word_for_alignment[kanji_to_highlight_pos + 1] == "々"
        ):
            left_word = word_output[: kanji_to_highlight_pos + 2]
            right_word = word_output[kanji_to_highlight_pos + 2 :]
        else:
            left_word = kanji_to_highlight
            right_word = word_output[1:]
        middle_word = ""
    elif edge == "right":
        # Include repeater if present (check if next char is repeater or if this IS the repeater)
        if kanji_to_highlight == "々" and kanji_to_highlight_pos > 0:
            # kanji_to_highlight is the repeater itself, include the kanji before it
            right_word = word_output[kanji_to_highlight_pos - 1 :]
            left_word = word_output[: kanji_to_highlight_pos - 1]
        elif (
            kanji_to_highlight_pos + 1 < len(word_for_alignment)
            and word_for_alignment[kanji_to_highlight_pos + 1] == "々"
        ):
            # Next char is repeater, include both
            right_word = word_output[kanji_to_highlight_pos:]
            left_word = word_output[:kanji_to_highlight_pos]
        else:
            right_word = kanji_to_highlight
            left_word = word_output[:-1]
        middle_word = ""
    elif edge == "middle":
        # Include repeater if present
        if (
            kanji_to_highlight_pos + 1 < len(word_for_alignment)
            and word_for_alignment[kanji_to_highlight_pos + 1] == "々"
        ):
            middle_word = word_output[kanji_to_highlight_pos : kanji_to_highlight_pos + 2]
            left_word = word_output[:kanji_to_highlight_pos]
            right_word = word_output[kanji_to_highlight_pos + 2 :]
        else:
            left_word = word_output[:kanji_to_highlight_pos]
            middle_word = kanji_to_highlight
            right_word = word_output[kanji_to_highlight_pos + 1 :]
    else:
        # Fallback (shouldn't happen)
        left_word = ""
        middle_word = kanji_to_highlight
        right_word = ""

    # Determine match type (most common type in matches)
    match_types = [m["match_type"] for m in alignment["kanji_matches"] if m]
    if match_types:
        # Use the type of the highlighted kanji if available
        if kanji_to_highlight_pos >= 0 and alignment["kanji_matches"][kanji_to_highlight_pos]:
            match_type = alignment["kanji_matches"][kanji_to_highlight_pos]["match_type"]
        else:
            # Otherwise use first match type
            match_type = match_types[0]
    elif juku_parts:
        match_type = "jukujikun"
    else:
        match_type = "none"

    final_result: FinalResult = {
        "furigana": complete_furigana,
        "okurigana": okurigana,
        "rest_kana": rest_kana,
        "left_word": left_word,
        "middle_word": middle_word,
        "right_word": right_word,
        "edge": edge,
        "match_type": match_type,
        "was_katakana": was_katakana,
    }

    return reconstruct_furigana(
        final_result,
        with_tags_def,
        reconstruct_type=reconstruct_type,
        logger=logger,
    )


def whole_word_mora_split(word: str, furigana: str) -> tuple[list[list[str]], bool]:
    """Simple mora split for whole-word case - either the whole furigana or split in half"""
    was_katakana = is_katakana_str(furigana)
    if was_katakana:
        furigana = to_hiragana(furigana)
    if len(word) == 2 and word[1] == "々":
        midpoint = max(1, len(furigana) // 2)
        first = furigana[:midpoint]
        second = furigana[midpoint:]
        # Since find_first_complete_alignment expects list of lists, simply return all the chars
        # as separate strings, we don't care about mora here
        return [[list(first), list(second)]], was_katakana
    return [[list(furigana)]], was_katakana


def kana_highlight(
    kanji_to_highlight: Optional[str],
    text: str,
    return_type: FuriReconstruct = "kana_only",
    with_tags_def: Optional[WithTagsDef] = None,
    logger: Logger = Logger("error"),
) -> str:
    if with_tags_def is None:
        with_tags_def = WithTagsDef(
            True,  # with_tags
            True,  # merge_consecutive
            True,  # onyomi_to_katakana
            False,  # include_suru_okuri
        )
    """
    Function that replaces the furigana of a kanji with the furigana that corresponds to the kanji's
    onyomi or kunyomi reading. The furigana is then highlighted with<b> tags.
    Text received could be a sentence or a single word with furigana.
    :param kanji_to_highlight: should be a single kanji character
    :param text: The text to process
    :param return_type: string. Return either normal furigana, reversed furigana AKA furikanji or
        remove the kanji and return only the kana
    :param with_tags_def: tuple, with_tags and merge_consecutive keys. Whether to wrap the readings
        with tags and whether to merge consecutive tags
    :param logger: Logger instance to log errors
    :return: The text cleaned from any previous<b> tags and<b> added around the furigana
        when the furigana corresponds to the kanji_to_highlight
    """

    def furigana_replacer(match: re.Match):
        """
        Replacer function for KANJI_AND_FURIGANA_REC. This function is called for every match
        found by the regex. It processes the furigana and returns the modified furigana.
        :param match: re.Match, the match object
        :return: string, the modified furigana
        """
        nonlocal kanji_to_highlight
        full_word = match.group(1)
        full_furigana = match.group(2)
        okurigana = match.group(3)
        logger.debug(
            f"furigana_replacer - word: {full_word}, furigana: {full_furigana}, okurigana:"
            f" {okurigana}"
        )
        # Replace doubled kanji with the repeater character
        full_word = DOUBLE_KANJI_REC.sub(lambda m: m.group(1) + "々", full_word)
        logger.debug(f"furigana_replacer - word after double kanji: {full_word}")

        if full_furigana.startswith("sound:"):
            # This was something like 漢字[sound:...], we shouldn't modify the text in the brackets
            # as it'd break the audio tag. But we know the text to the right is kanji
            # (what is it doing there next to a sound tag?) so we'll just leave it out anyway
            return full_furigana + okurigana

        highlight_kanji_is_whole_word = kanji_to_highlight is not None and (
            full_word == kanji_to_highlight
            or f"{kanji_to_highlight}々" == full_word
            or kanji_to_highlight * 2 == full_word
        )
        word_is_repeated_kanji = len(full_word) == 2 and full_word[1] == "々"
        is_whole_word_case = highlight_kanji_is_whole_word or word_is_repeated_kanji

        def replace_numeric_substrings(text: str) -> str:
            return re.sub(r"[0-9０-９]+", lambda m: number_to_kanji(m.group(0)), text)

        # Step 1: Check exception dictionary first
        exception_alignment = check_exception(
            word=full_word,
            furigana=full_furigana,
            kanji_to_highlight=kanji_to_highlight or "",
            return_type=return_type,
            with_tags_def=with_tags_def,
        )
        if exception_alignment is not None:
            logger.debug(f"furigana_replacer - using exception alignment: {exception_alignment}")
            juku_parts, juku_okurigana, juku_rest_kana = process_jukujikun_positions(
                word=full_word,
                alignment=exception_alignment,
                with_tags=with_tags_def.with_tags,
                remaining_kana=okurigana,
            )
            use_okurigana = ""
            use_rest_kana = okurigana
            if len(full_word) - 1 in exception_alignment["jukujikun_positions"]:
                use_okurigana = juku_okurigana
                use_rest_kana = juku_rest_kana

            final_result = reconstruct_from_alignment(
                word=full_word,
                alignment=exception_alignment,
                juku_parts=juku_parts,
                kanji_to_highlight=kanji_to_highlight or "",
                with_tags_def=with_tags_def,
                okurigana=use_okurigana,
                rest_kana=use_rest_kana,
                was_katakana=False,
                reconstruct_type=return_type,
                logger=logger,
            )
            return final_result

        # Steps 2-3: Handle mora split either as whole-word or partial-word and find alignment
        # Convert numeric digits to kanji to enable proper reading matching (e.g., ７ → 七)
        alignment_word = replace_numeric_substrings(full_word)
        alignment = None
        was_katakana = False

        if is_whole_word_case:
            possible_whole_word_splits, was_katakana = whole_word_mora_split(
                full_word, full_furigana
            )
            logger.debug(
                "furigana_replacer - whole_word_case possible_splits:"
                f" {possible_whole_word_splits}, was_katakana: {was_katakana}"
            )
            alignment = find_first_complete_alignment(
                word=alignment_word,
                okurigana=okurigana,
                possible_splits=possible_whole_word_splits,
                is_whole_word=True,
                logger=logger,
            )
        else:
            mora_result = split_to_mora_list(full_furigana, len(full_word))
            was_katakana = mora_result["was_katakana"]
            logger.debug(f"furigana_replacer - partial_word_case mora_result: {mora_result}")
            alignment = find_first_complete_alignment(
                word=alignment_word,
                okurigana=okurigana,
                mora_list=mora_result["mora_list"],
                is_whole_word=False,
                logger=logger,
            )

        logger.debug(
            f"furigana_replacer - alignment complete: {alignment['is_complete']}, juku_positions:"
            f" {alignment['jukujikun_positions']}"
        )

        # Step 4: Handle jukujikun positions if any
        final_okurigana = alignment["final_okurigana"]
        final_rest_kana = alignment["final_rest_kana"]
        juku_parts: dict[int, str] = {}

        if not alignment["is_complete"] or alignment["jukujikun_positions"]:
            # Process jukujikun positions (even for complete alignments) to allow okurigana
            # extraction for jukujikun exception cases like 清々しい.
            juku_parts, juku_okurigana, juku_rest_kana = process_jukujikun_positions(
                word=full_word,
                alignment=alignment,
                with_tags=with_tags_def.with_tags,
                remaining_kana=okurigana,
            )
            logger.debug(
                f"furigana_replacer - juku_parts: {juku_parts}, juku_okurigana: {juku_okurigana}"
            )

            # Use jukujikun okurigana when the last kanji is jukujikun. If we already have
            # okurigana from alignment, prefer the longer match from the juku extraction.
            if len(full_word) - 1 in alignment["jukujikun_positions"]:
                if len(juku_okurigana) >= len(final_okurigana):
                    final_okurigana = juku_okurigana
                    final_rest_kana = juku_rest_kana
            elif not final_okurigana and juku_okurigana:
                final_okurigana = juku_okurigana
                final_rest_kana = juku_rest_kana

        # Step 5: Reconstruct furigana from alignment
        final_result = reconstruct_from_alignment(
            word=full_word,
            alignment=alignment,
            juku_parts=juku_parts,
            kanji_to_highlight=kanji_to_highlight or "",
            with_tags_def=with_tags_def,
            okurigana=final_okurigana,
            rest_kana=final_rest_kana,
            was_katakana=was_katakana,
            reconstruct_type=return_type,
            logger=logger,
        )
        logger.debug(f"furigana_replacer - final_result: {final_result}")
        return final_result

    # Clean any potential mixed okurigana cases, turning them normal
    clean_text = OKURIGANA_MIX_CLEANING_REC.sub(okurigana_mix_cleaning_replacer, text)
    processed_text = KANJI_AND_FURIGANA_AND_OKURIGANA_REC.sub(furigana_replacer, clean_text)
    logger.debug(f"processed_text: {processed_text}")
    # Clean any double spaces that might have been created by the furigana reconstruction
    # Including those right before a<b> tag as the space is added with those
    processed_text = re.sub(r" {2}", " ", processed_text)
    processed_text = re.sub(r" <(b|on|kun|juk|mix)> ", r"<\1> ", processed_text)
    return re.sub(r" <b><(on|kun|juk|mix)> ", r"<b><\1> ", processed_text)
