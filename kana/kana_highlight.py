from functools import partial
import re
from typing import Literal, Optional, Tuple, cast

from .construct_wrapped_furi_word import (
    construct_wrapped_furi_word,
    FuriReconstruct,
)

try:
    from mecab_controller.kana_conv import to_katakana, to_hiragana, is_katakana_str, is_kana_str
except ImportError:
    from ..mecab_controller.kana_conv import to_katakana, to_hiragana, is_katakana_str, is_kana_str
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger
try:
    from kanji.number_to_kanji import number_to_kanji
except ImportError:
    from ..kanji.number_to_kanji import number_to_kanji
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
        NON_KANA_REC,
    )
except ImportError:
    from ..regex.kanji_furi import (
        DOUBLE_KANJI_REC,
        KANJI_AND_FURIGANA_AND_OKURIGANA_REC,
        FURIGANA_REC,
        NON_KANA_REC,
    )
try:
    from regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA, RENDAKU_CONVERSION_DICT_KATAKANA
except ImportError:
    from ..regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA, RENDAKU_CONVERSION_DICT_KATAKANA
try:
    from all_types.main_types import (
        Edge,
        WithTagsDef,
        YomiMatchResult,
        FinalResult,
        MoraAlignment,
        ReadingType,
        WrapMatchEntry,
    )
except ImportError:
    from ..all_types.main_types import (
        Edge,
        WithTagsDef,
        YomiMatchResult,
        FinalResult,
        MoraAlignment,
        ReadingType,
        WrapMatchEntry,
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
    segments: list[list[WrapMatchEntry]] = furi_okuri_result.get("segments", [])
    highlight_idx: Optional[int] = furi_okuri_result.get("highlight_segment_index")
    okurigana: str = furi_okuri_result.get("okurigana", "")
    rest_kana: str = furi_okuri_result.get("rest_kana", "")

    if okurigana and with_tags_def.with_tags:
        okurigana = f"<oku>{okurigana}</oku>"

    def render_segment(segment: list[WrapMatchEntry], merge_override: bool = False) -> str:
        # No tags, just return simple format
        if not with_tags_def.with_tags:
            segment_word = "".join([entry["kanji"] for entry in segment if entry["kanji"]])
            segment_furi = "".join([entry["furigana"] for entry in segment])
            if reconstruct_type == "kana_only":
                return segment_furi
            # Sanity check, can't make furigana/furikanji without the word (kanji)
            if not segment_word:
                return ""
            if reconstruct_type == "furikanji":
                return f" {segment_furi}[{segment_word}]"
            # furigana type
            return f" {segment_word}[{segment_furi}]"

        # With tags, needs more complex processing
        merge_flag = with_tags_def.merge_consecutive or force_merge or merge_override
        return construct_wrapped_furi_word(
            segment,
            reconstruct_type,
            merge_flag,
            with_tags_def.with_tags,
            apply_highlight=False,
            logger=logger,
        )

    rendered_segments: list[str] = []
    merge_all = not with_tags_def.with_tags
    for segment in segments:
        rendered = render_segment(segment, merge_override=merge_all)
        rendered_segments.append(rendered)

    highlight_segment = None
    if highlight_idx is not None and 0 <= highlight_idx < len(rendered_segments):
        highlight_segment = rendered_segments[highlight_idx]
        logger.debug(
            f"reconstruct_furigana - highlight segment in index {highlight_idx}:"
            f" {highlight_segment}"
        )
    logger.debug(
        "reconstruct_furigana - rendered segments before okurigana/rest kana handling:"
        f" {rendered_segments}, okurigana: {okurigana}, rest_kana: {rest_kana}"
    )
    if rendered_segments and okurigana:
        last_segment_part: Optional[WrapMatchEntry] = segments[-1][-1] if segments[-1] else None
        okuri_out_of_highlight = (
            not with_tags_def.include_suru_okuri
            and last_segment_part is not None
            and last_segment_part.get("is_noun_suru_verb", False)
        )
        logger.debug(
            "reconstruct_furigana - okurigana exists, checking if okurigana should be outside"
            f" highlight: {okuri_out_of_highlight}"
        )
        # Append okurigana to the last segment if it exists, also handling highlight
        last_rendered_segment = rendered_segments[-1]
        if last_rendered_segment != highlight_segment:
            # No highlight in last segment, just add okurigana
            rendered_segments[-1] = f"{rendered_segments[-1]}{okurigana}"
            # Handle highlight segment if it exists
            if highlight_segment is not None:
                rendered_segments[highlight_idx] = f"<b>{highlight_segment}</b>"
            logger.debug(
                "reconstruct_furigana - no highlight in last segment, appended okurigana:"
                f" {rendered_segments[-1]}"
            )
        elif not okuri_out_of_highlight:
            # Highlight segment is last and okurigana should be inside it
            rendered_segments[-1] = f"<b>{rendered_segments[-1]}{okurigana}</b>"
            logger.debug(
                "reconstruct_furigana - highlight in last segment, included okurigana:"
                f" {rendered_segments[-1]}"
            )
        elif okuri_out_of_highlight:
            # Highlight segment is last but okurigana should be outside it
            rendered_segments[-1] = f"<b>{rendered_segments[-1]}</b>{okurigana}"
            logger.debug(
                "reconstruct_furigana - highlight in last segment, okurigana outside highlight:"
                f" {rendered_segments[-1]}"
            )
    elif okurigana:
        logger.debug("reconstruct_furigana - no segments but okurigana exists, adding okurigana")
        rendered_segments.append(okurigana)
    else:
        logger.debug("reconstruct_furigana - no okurigana to handle, adding highlight if needed")
        if highlight_segment is not None:
            rendered_segments[highlight_idx] = f"<b>{highlight_segment}</b>"

    result = "".join(rendered_segments)

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


def reconstruct_from_alignment(
    word: str,
    alignment: MoraAlignment,
    juku_parts: dict[int, WrapMatchEntry],
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
    alignment_len = len(alignment["kanji_matches"])
    word_len = len(word)

    def compress_numeric_runs(text: str) -> str:
        return re.sub(r"[0-9０-９]+", lambda m: number_to_kanji(m.group(0)), text)

    word_for_alignment = word
    surface_slices: list[str] = list(word)
    if alignment_len != word_len:
        # When the word contains numeric characters, the alignment is done on kanji
        # with numeric characters converted to kanji numerals. Build a mapping from the
        # compressed alignment positions back to the original surface slices so merged
        # numeric runs keep the original digits.
        word_for_alignment = compress_numeric_runs(word)
        surface_slices = []
        pos = 0
        for match in re.finditer(r"[0-9０-９]+", word):
            if match.start() > pos:
                surface_slices.extend(list(word[pos : match.start()]))
            digits = match.group(0)
            converted = number_to_kanji(digits)
            repeat = max(1, len(converted))
            surface_slices.extend([digits] + [""] * (repeat - 1))
            pos = match.end()
        if pos < len(word):
            surface_slices.extend(list(word[pos:]))
        if len(surface_slices) != len(word_for_alignment):
            surface_slices = list(word_for_alignment)
    kanji_to_highlight_pos = (
        word_for_alignment.find(kanji_to_highlight) if kanji_to_highlight else -1
    )

    entries: list[WrapMatchEntry] = []

    for i, kanji in enumerate(word_for_alignment):
        surface_kanji = surface_slices[i] if i < len(surface_slices) else kanji
        if i in juku_parts:
            part = juku_parts[i]
            reading = part["furigana"]
            tag = part["tag"]
            is_num = part["is_num"]
            is_noun_suru_verb = part.get("is_noun_suru_verb", False)
        elif alignment["kanji_matches"][i]:
            match_info = alignment["kanji_matches"][i]
            is_noun_suru_verb = match_info.get("is_noun_suru_verb", False)
            reading = match_info["matched_mora"]
            highlight_match_type = match_info["match_type"]

            if with_tags_def.onyomi_to_katakana and highlight_match_type == "onyomi":
                reading = to_katakana(reading)

            tag = (
                "on"
                if highlight_match_type == "onyomi"
                else "kun" if highlight_match_type == "kunyomi" else "juk"
            )
            is_num = surface_kanji.isdigit()
        else:
            logger.error(
                f"reconstruct_from_alignment: No match or juku_part for kanji {kanji} at index {i}"
            )
            reading = ""
            tag = "mix"
            is_num = False

        entries.append({
            "kanji": surface_kanji,
            "tag": tag,
            "furigana": reading,
            "highlight": False,
            "is_num": is_num,
            "is_noun_suru_verb": is_noun_suru_verb,
        })
    logger.debug(f"reconstruct_from_alignment - initial entries: {entries}")

    # Uniform script conversion when original furigana was katakana
    if was_katakana:
        for entry in entries:
            entry["furigana"] = to_katakana(entry["furigana"])

    # Determine highlight span (include repeater following the target kanji)
    highlight_start = kanji_to_highlight_pos
    highlight_end = (
        kanji_to_highlight_pos + 1 if kanji_to_highlight_pos >= 0 else kanji_to_highlight_pos
    )
    if kanji_to_highlight_pos >= 0 and kanji_to_highlight_pos + 1 < len(word_for_alignment):
        if word_for_alignment[kanji_to_highlight_pos + 1] == "々":
            highlight_end = kanji_to_highlight_pos + 2

    # Mark highlighted entries
    if highlight_start >= 0:
        for idx in range(highlight_start, min(highlight_end, len(entries))):
            entries[idx]["highlight"] = True

    # Merge consecutive numeric entries so they behave like a single logical block when their
    # tag/highlight context matches (e.g., ３０ → one on-tag chunk). Keep tag boundaries intact
    # to allow mixed-tag readings like 40分 (よん + ジュッ) to remain split. Only apply when
    # callers want merged tags; otherwise preserve per-digit structure for split outputs.
    if with_tags_def.merge_consecutive:
        merged_entries: list[WrapMatchEntry] = []
        idx = 0
        while idx < len(entries):
            cur = entries[idx]
            if not cur["is_num"]:
                merged_entries.append(cur)
                idx += 1
                continue

            combined_kanji = cur["kanji"]
            combined_furi = cur["furigana"]
            tag = cur["tag"]
            highlight_flag = cur["highlight"]
            j = idx + 1
            while (
                j < len(entries)
                and entries[j]["is_num"]
                and entries[j]["highlight"] == highlight_flag
                and entries[j]["tag"] == tag
            ):
                next_entry = entries[j]
                combined_kanji += next_entry["kanji"]
                combined_furi += next_entry["furigana"]
                j += 1

            merged_entries.append({
                "kanji": combined_kanji,
                "tag": tag,
                "furigana": combined_furi,
                "highlight": highlight_flag,
                "is_num": True,
            })
            idx = j

        entries = merged_entries

    # Split entries into segments: before highlight, highlight, after highlight
    segments: list[list[WrapMatchEntry]] = []
    highlight_segment_index: Optional[int] = None

    first_highlight_idx = next((i for i, e in enumerate(entries) if e["highlight"]), None)
    last_highlight_idx = None
    if first_highlight_idx is not None:
        for i in range(len(entries) - 1, -1, -1):
            if entries[i]["highlight"]:
                last_highlight_idx = i
                break

    if first_highlight_idx is None:
        segments = [entries]
    else:
        end_idx = (last_highlight_idx or first_highlight_idx) + 1
        if first_highlight_idx > 0:
            segments.append(entries[:first_highlight_idx])
        segments.append(entries[first_highlight_idx:end_idx])
        highlight_segment_index = len(segments) - 1
        if end_idx < len(entries):
            segments.append(entries[end_idx:])

    logger.debug(
        "reconstruct_from_alignment - match type from highlighted kanji at position"
        f" {kanji_to_highlight_pos}, kanji_matches: {alignment['kanji_matches']},"
    )
    # Determine match type of the highlight segment
    highlight_match_type = "none"
    if kanji_to_highlight_pos >= 0 and alignment["kanji_matches"][kanji_to_highlight_pos]:
        highlight_match_type = alignment["kanji_matches"][kanji_to_highlight_pos]["match_type"]
    elif kanji_to_highlight_pos >= 0 and juku_parts:
        highlight_match_type = "jukujikun"

    final_result: FinalResult = {
        "segments": segments,
        "highlight_segment_index": highlight_segment_index,
        "word": word,
        "highlight_match_type": highlight_match_type,
        "okurigana": okurigana,
        "rest_kana": rest_kana,
        "was_katakana": was_katakana,
    }
    logger.debug(f"reconstruct_from_alignment - final_result: {final_result}")

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
        maybe_okuri = match.group(3)
        logger.debug(
            f"furigana_replacer - word: {full_word}, furigana: {full_furigana}, okurigana:"
            f" {maybe_okuri}"
        )
        # Clean off non-kana characters from furigana, unless it becomes empty
        cleaned_furigana = re.sub(NON_KANA_REC, "", full_furigana)
        if cleaned_furigana:
            logger.debug(
                f"furigana_replacer - cleaned furigana: {cleaned_furigana} from original:"
                f" {full_furigana}"
            )
            full_furigana = cleaned_furigana
        # if furigana is invalid - empty or all non-kana characters - try to return something
        # sensible
        if not full_furigana or not is_kana_str(full_furigana):
            logger.debug(f"furigana_replacer - empty or invalid furigana case: {full_furigana}")
            if return_type == "kana_only":
                # return furigana as is, since it's either empty or invalid
                # Since the kanji are omitted, there's nothing to highlight
                if not full_furigana or not with_tags_def.with_tags:
                    return f"{full_furigana}{maybe_okuri}"
                return f"<err>{full_furigana}</err>{maybe_okuri}"
            if kanji_to_highlight and kanji_to_highlight in full_word:
                # There's a kanji to highlight, add <b> around the kanji
                full_word = full_word.replace(kanji_to_highlight, f"<b>{kanji_to_highlight}</b>")
            if return_type == "furigana":
                if full_furigana:
                    if with_tags_def.with_tags:
                        # Wrap the whole word in <err> tag since the furigana is invalid
                        return f"<err> {full_word}[{full_furigana}]</err>{maybe_okuri}"
                    return f" {full_word}[{full_furigana}]{maybe_okuri}"
                else:
                    # no furigana, don't add brackets
                    if with_tags_def.with_tags:
                        # Wrap the whole word in <err> tag since we have no furigana
                        return f"<err>{full_word}</err>{maybe_okuri}"
                    return f"{full_word}{maybe_okuri}"
            # Since it's expected that the kanji should be hidden, add a placeholder for empty
            # furigana
            if not full_furigana:
                full_furigana = "□"
            if return_type == "furikanji":
                if with_tags_def.with_tags:
                    # Wrap with <err> tag too
                    return f"<err> {full_furigana}[{full_word}]</err>{maybe_okuri}"
                return f" {full_furigana}[{full_word}]{maybe_okuri}"

        # Replace doubled kanji with the repeater character
        full_word = DOUBLE_KANJI_REC.sub(lambda m: m.group(1) + "々", full_word)
        logger.debug(f"furigana_replacer - word after double kanji: {full_word}")

        if full_furigana.startswith("sound:"):
            # This was something like 漢字[sound:...], we shouldn't modify the text in the brackets
            # as it'd break the audio tag. But we know the text to the right is kanji
            # (what is it doing there next to a sound tag?) so we'll just leave it out anyway
            return full_furigana + maybe_okuri

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
            logger=logger,
        )
        logger.debug(f"furigana_replacer - exception_alignment: {exception_alignment}")
        if exception_alignment is not None:
            logger.debug(f"furigana_replacer - using exception alignment: {exception_alignment}")
            juku_parts, juku_okurigana, juku_rest_kana = process_jukujikun_positions(
                word=full_word,
                furigana=full_furigana,
                alignment=exception_alignment,
                remaining_kana=maybe_okuri,
                logger=logger,
            )
            use_okurigana = ""
            use_rest_kana = maybe_okuri
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
                furigana=full_furigana,
                maybe_okuri=maybe_okuri,
                possible_splits=possible_whole_word_splits,
                logger=logger,
            )
        else:
            mora_result = split_to_mora_list(full_furigana, len(full_word))
            was_katakana = mora_result["was_katakana"]
            logger.debug(f"furigana_replacer - partial_word_case mora_result: {mora_result}")
            alignment = find_first_complete_alignment(
                word=alignment_word,
                furigana=full_furigana,
                maybe_okuri=maybe_okuri,
                mora_list=mora_result["mora_list"],
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
                furigana=full_furigana,
                alignment=alignment,
                remaining_kana=maybe_okuri,
                logger=logger,
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
    # Including those right before a <b> tag as the space is added with those
    processed_text = re.sub(r" {2}", " ", processed_text)
    processed_text = re.sub(r" <(b|on|kun|juk|mix)> ", r"<\1> ", processed_text)
    return re.sub(r" <b><(on|kun|juk|mix)> ", r"<b><\1> ", processed_text)
