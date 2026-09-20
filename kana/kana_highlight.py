import re

from ..all_types.main_types import (
    FinalResult,
    MatchType,
    MoraAlignment,
    WithTagsDef,
    WrapMatchEntry,
    WrapTag,
)
from ..kanji.number_to_kanji import number_to_kanji
from ..mecab_controller.kana_conv import is_kana_str, to_hiragana, to_katakana
from ..okuri.okurigana_mix_cleaning_replacer import (
    LEADING_KANA_CLEANING_REC,
    OKURIGANA_MIX_CLEANING_REC,
    leading_kana_cleaning_replacer,
    okurigana_mix_cleaning_replacer,
)
from ..regex.kanji_furi import (
    DOUBLE_KANJI_REC,
    KANJI_AND_FURIGANA_AND_OKURIGANA_REC,
    KANJI_RE,
    NON_KANA_REC,
)
from ..utils.logger import package_logger as logger
from .construct_wrapped_furi_word import (
    FuriReconstruct,
    construct_wrapped_furi_word,
)
from .furigana_exceptions import check_exception
from .furigana_normalizer import normalize_furigana_for_matching
from .jukujikun_processor import process_jukujikun_positions
from .katakana_positions import get_katakana_positions
from .mora_alignment import find_first_complete_alignment
from .mora_splitter import normalize_long_vowel_marks, split_to_mora_list
from .orphaned_repeater_cleaning import (
    ORPHANED_REPEATER_CLEANING_REC,
    orphaned_repeater_cleaning_replacer,
)

# Kanji directly followed by their furigana, plus the optional space that furigana syntax puts
# before a word to mark where its kanji start. Group 1 is the kanji, group 2 the furigana.
KANA_FILTER_REC = re.compile(rf" ?{KANJI_RE}\[(.+?)\]")


def kana_filter(text):
    """
    Implementation of the basic Anki kana filter
    This is needed to clean up the text in cases where we know there's no matches to the kanji
    This works differently as it directly matches kanji characters instead of [^ >] as in the Anki
    built-in version. For whatever reason a python version using that doesn't work as expected.
    With [^ >], Anki's version turns これは漢字[かんじ] into かんじ, while this gives これはかんじ.
    Kanji without furigana, [sound:...] tags and HTML are left as they are.
    :param text: The text to clean
    :return: The cleaned text
    """

    def bracket_replace(match):
        if match.group(2).startswith("sound:"):
            # [sound:...] should not be replaced
            return match.group(0)
        # Return the furigana inside the brackets, dropping the kanji and the leading space
        return match.group(2)

    # Run the same cleaning passes kana_highlight does, in the same order: put a separated 々
    # back into its word's furigana group, so that 人 々[ひとびと] is not left with an unread 人,
    # then give back the kana a word opens with, so that お前[おまえ] does not spell its お twice,
    # then turn mixed okurigana furigana like 消え去[きえさ]る into 消[き]え去[さ]る, so that every
    # kanji is directly followed by its own furigana. Then replace each kanji[furigana] with the
    # furigana.
    clean_text = ORPHANED_REPEATER_CLEANING_REC.sub(
        orphaned_repeater_cleaning_replacer, text.replace("&nbsp;", " ")
    )
    clean_text = LEADING_KANA_CLEANING_REC.sub(leading_kana_cleaning_replacer, clean_text)
    clean_text = OKURIGANA_MIX_CLEANING_REC.sub(okurigana_mix_cleaning_replacer, clean_text)
    return KANA_FILTER_REC.sub(bracket_replace, clean_text)


def reconstruct_furigana(
    furi_okuri_result: FinalResult,
    with_tags_def: WithTagsDef,
    reconstruct_type: FuriReconstruct = "furigana",
    force_merge: bool = False,
) -> str:
    """
    Reconstruct the furigana from the replace result

    :return: The reconstructed furigana with the kanji and that kanji's furigana highlighted
    """
    logger.debug(
        "reconstruct_furigana - final_result: %s, reconstruct_type: %s, wrap_with_tags: %s,"
        " merge_consecutive: %s",
        furi_okuri_result,
        reconstruct_type,
        with_tags_def.with_tags,
        with_tags_def.merge_consecutive,
    )
    segments: list[list[WrapMatchEntry]] = furi_okuri_result.get("segments", [])
    highlight_indices: list[int] = furi_okuri_result.get("highlight_segment_indices", [])
    okurigana: str = furi_okuri_result.get("okurigana", "")
    rest_kana: str = furi_okuri_result.get("rest_kana", "")
    original_furigana: str = furi_okuri_result.get("original_furigana", "")
    original_hiragana = to_hiragana(original_furigana) if original_furigana else ""
    katakana_positions: list[int] = furi_okuri_result.get("katakana_positions", [])
    restored_chars: dict[int, str] = furi_okuri_result.get("restored_chars", {})

    if okurigana and with_tags_def.with_tags:
        okurigana = f"<oku>{okurigana}</oku>"

    render_cursor = 0

    def render_segment(segment: list[WrapMatchEntry], merge_override: bool = False) -> str:
        nonlocal render_cursor
        segment_furi_len = len("".join([entry["furigana"] for entry in segment]))
        # No tags, just return simple format
        if not with_tags_def.with_tags:
            segment_word = "".join([entry["kanji"] for entry in segment if entry["kanji"]])
            segment_furi = "".join([entry["furigana"] for entry in segment])

            # Put back the rewritten characters and the katakana, by position in the original.
            if segment_furi and original_furigana and (katakana_positions or restored_chars):
                furi_chars = list(segment_furi)
                for i in range(len(furi_chars)):
                    original_pos = render_cursor + i
                    if original_pos in restored_chars:
                        furi_chars[i] = restored_chars[original_pos]
                    elif (
                        original_pos in katakana_positions
                        and original_pos < len(original_hiragana)
                        # A ー that was spread out into a vowel instead of being restored is not
                        # that vowel's script to decide, leave it as the hiragana it became
                        and original_hiragana[original_pos] != "ー"
                    ):
                        furi_chars[i] = to_katakana(furi_chars[i])
                segment_furi = "".join(furi_chars)
            render_cursor += segment_furi_len

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
        rendered = construct_wrapped_furi_word(
            segment,
            reconstruct_type,
            merge_flag,
            with_tags_def.with_tags,
            apply_highlight=False,
            original_furigana=original_furigana,
            katakana_positions=katakana_positions,
            restored_chars=restored_chars,
            original_start_index=render_cursor,
        )
        render_cursor += segment_furi_len
        return rendered

    rendered_segments: list[str] = []
    merge_all = not with_tags_def.with_tags
    for segment in segments:
        rendered = render_segment(segment, merge_override=merge_all)
        rendered_segments.append(rendered)

    highlight_indices = [i for i in highlight_indices if 0 <= i < len(rendered_segments)]
    # The okurigana belongs to the last segment, so wrapping that one has to wait until we know
    # whether the okurigana goes inside the <b> or after it
    last_is_highlighted = bool(highlight_indices) and highlight_indices[-1] == (
        len(rendered_segments) - 1
    )

    def wrap_highlighted_segments(skip_last: bool = False) -> None:
        for i in highlight_indices:
            if skip_last and i == len(rendered_segments) - 1:
                continue
            rendered_segments[i] = f"<b>{rendered_segments[i]}</b>"

    logger.debug(
        "reconstruct_furigana - highlight segments at indices %s, last_is_highlighted: %s",
        highlight_indices,
        last_is_highlighted,
    )
    logger.debug(
        "reconstruct_furigana - rendered segments before okurigana/rest kana handling: %s,"
        " okurigana: %s, rest_kana: %s",
        rendered_segments,
        okurigana,
        rest_kana,
    )
    if rendered_segments and okurigana:
        last_segment_part: WrapMatchEntry | None = segments[-1][-1] if segments[-1] else None
        okuri_out_of_highlight = (
            not with_tags_def.include_suru_okuri
            and last_segment_part is not None
            and last_segment_part.get("is_noun_suru_verb", False)
        )
        logger.debug(
            "reconstruct_furigana - okurigana exists, checking if okurigana should be outside"
            " highlight: %s",
            okuri_out_of_highlight,
        )
        # Append okurigana to the last segment if it exists, also handling highlight
        if not last_is_highlighted:
            # No highlight in last segment, just add okurigana
            rendered_segments[-1] = f"{rendered_segments[-1]}{okurigana}"
            wrap_highlighted_segments()
            logger.debug(
                "reconstruct_furigana - no highlight in last segment, appended okurigana: %s",
                rendered_segments[-1],
            )
        elif not okuri_out_of_highlight:
            # Highlight segment is last and okurigana should be inside it
            wrap_highlighted_segments(skip_last=True)
            rendered_segments[-1] = f"<b>{rendered_segments[-1]}{okurigana}</b>"
            logger.debug(
                "reconstruct_furigana - highlight in last segment, included okurigana: %s",
                rendered_segments[-1],
            )
        else:
            # Highlight segment is last but okurigana should be outside it
            wrap_highlighted_segments(skip_last=True)
            rendered_segments[-1] = f"<b>{rendered_segments[-1]}</b>{okurigana}"
            logger.debug(
                "reconstruct_furigana - highlight in last segment, okurigana outside highlight: %s",
                rendered_segments[-1],
            )
    elif okurigana:
        logger.debug("reconstruct_furigana - no segments but okurigana exists, adding okurigana")
        rendered_segments.append(okurigana)
    else:
        logger.debug("reconstruct_furigana - no okurigana to handle, adding highlight if needed")
        wrap_highlighted_segments()

    result = "".join(rendered_segments)

    return f"{result}{rest_kana}"


def reconstruct_from_alignment(
    word: str,
    alignment: MoraAlignment,
    juku_parts: dict[int, WrapMatchEntry],
    kanji_to_highlight: str,
    with_tags_def: WithTagsDef,
    okurigana: str,
    rest_kana: str,
    katakana_positions: list[int],
    restored_chars: dict[int, str],
    original_furigana: str,
    reconstruct_type: FuriReconstruct,
    furigana_prefix: str = "",
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
    :param katakana_positions: List of indices in original furigana that were katakana
    :param restored_chars: Index in original furigana → the character to write back there, for the
        kana that were rewritten before matching
    :param original_furigana: The original furigana before hiragana conversion
    :param furigana_prefix: Kana taken off the front of the furigana before matching, given back to
        the first kanji's reading here
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
    highlight_lookup_word = compress_numeric_runs(word)
    kanji_to_highlight_pos = (
        highlight_lookup_word.find(kanji_to_highlight) if kanji_to_highlight else -1
    )

    entries: list[WrapMatchEntry] = []

    for i, kanji in enumerate(word_for_alignment):
        surface_kanji = surface_slices[i] if i < len(surface_slices) else kanji
        # Every entry field gets a value before the branches, so a branch that does not speak for
        # one of them leaves this kanji's own default rather than whatever the previous kanji had.
        reading = ""
        tag: WrapTag = "mix"
        is_num = False
        is_noun_suru_verb: bool | None = False
        if i in juku_parts:
            part = juku_parts[i]
            reading = part["furigana"]
            tag = part["tag"]
            is_num = part["is_num"]
            is_noun_suru_verb = part.get("is_noun_suru_verb", False)
            if surface_kanji.isdigit():
                # The jukujikun processor is handed the converted word, where the digits read as
                # kanji numerals, so the surface is what still knows this position is a number.
                # A number's reading is a reading, not jukujikun, the same call the processor
                # makes for a digit of its own.
                tag = "kun"
                is_num = True
        elif match_info := alignment["kanji_matches"][i]:
            # The alignment is what decides a doubled kanji is really the repeater, so where it
            # says 々, 々 is what gets written - even if the word came in spelled out.
            if match_info.get("kanji") == "々":
                surface_kanji = "々"
            is_noun_suru_verb = match_info.get("is_noun_suru_verb", False)
            reading = match_info["matched_mora"]
            # This kanji's own match type, not the highlight's - that one is decided below
            match_type = match_info["match_type"]

            if with_tags_def.onyomi_to_katakana and match_type == "onyomi":
                reading = to_katakana(reading)

            tag = (
                "on" if match_type == "onyomi" else "kun" if match_type == "kunyomi" else "juk"
            )
            is_num = surface_kanji.isdigit()
        else:
            logger.error(
                "reconstruct_from_alignment: No match or juku_part for kanji %s at index %s",
                kanji,
                i,
            )

        entries.append({
            "kanji": surface_kanji,
            "tag": tag,
            "furigana": reading,
            "highlight": False,
            "is_num": is_num,
            "is_noun_suru_verb": is_noun_suru_verb,
        })
    # Give back the kana that was taken off the front of the furigana for matching. The first
    # kanji's reading is what it sat in front of, so that is where it goes, and from here on the
    # readings line up with the original furigana again.
    if furigana_prefix and entries:
        entries[0]["furigana"] = f"{furigana_prefix}{entries[0]['furigana']}"

    logger.debug("reconstruct_from_alignment - initial entries: %s", entries)

    # Mark every position the kanji occupies, not just the first: the point is to show the kanji
    # wherever it turns up, and a word can use it more than once - 生物物理学 is 生物 + 物理学 and
    # both its 物 are the kanji being studied. A 々 stands in for the kanji before it, so it is
    # highlighted along with it.
    highlight_positions: list[int] = []
    if kanji_to_highlight:
        # kanji_to_highlight is usually one kanji but doesn't have to be: 生物 in 生物学 covers two
        # positions, so search for it as a substring and mark every position it spans.
        span = len(kanji_to_highlight)
        start = highlight_lookup_word.find(kanji_to_highlight)
        while start != -1:
            end = start + span
            highlight_positions.extend(range(start, end))
            if end < len(word_for_alignment) and word_for_alignment[end] == "々":
                highlight_positions.append(end)
            start = highlight_lookup_word.find(kanji_to_highlight, end)

    if reconstruct_type != "kana_only" and highlight_positions:
        # A digit run converts into several kanji but renders as one chunk - only its first
        # position carries the digits, the rest have no surface of their own - so a highlight on
        # one of those kanji takes the whole run with it. Split at the kanji instead and the
        # segment holding it has nothing to write, so its reading - and every reading after it -
        # is dropped. The kana-only modes have no surface to keep together, so they keep the
        # finer split.
        digit_runs: list[list[int]] = []
        for i, surface in enumerate(surface_slices):
            if surface.isdigit():
                digit_runs.append([i])
            elif surface == "" and digit_runs and digit_runs[-1][-1] == i - 1:
                digit_runs[-1].append(i)
        marked = set(highlight_positions)
        for run in digit_runs:
            if marked.intersection(run):
                marked.update(run)
        highlight_positions = sorted(marked)

    for idx in highlight_positions:
        if idx < len(entries):
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

    # Split entries into segments, each a run of entries that are all highlighted or all not, so
    # that a kanji occurring twice with something between (国民国家) gets a <b> around each run
    # rather than one around everything from the first to the last.
    segments: list[list[WrapMatchEntry]] = []
    highlight_segment_indices: list[int] = []

    for entry in entries:
        if segments and segments[-1][-1]["highlight"] == entry["highlight"]:
            segments[-1].append(entry)
            continue
        segments.append([entry])
        if entry["highlight"]:
            highlight_segment_indices.append(len(segments) - 1)
    if not segments:
        segments = [entries]

    logger.debug(
        "reconstruct_from_alignment - match type from highlighted kanji at position %s,"
        " kanji_matches: %s,",
        kanji_to_highlight_pos,
        alignment['kanji_matches'],
    )
    # Determine match type of the highlight segment
    highlight_match_type: MatchType = "none"
    if kanji_to_highlight_pos >= 0:
        highlighted_match = alignment["kanji_matches"][kanji_to_highlight_pos]
        if highlighted_match:
            highlight_match_type = highlighted_match["match_type"]
        elif juku_parts:
            highlight_match_type = "jukujikun"

    final_result: FinalResult = {
        "segments": segments,
        "highlight_segment_indices": highlight_segment_indices,
        "word": word,
        "highlight_match_type": highlight_match_type,
        "okurigana": okurigana,
        "rest_kana": rest_kana,
        "katakana_positions": katakana_positions,
        "restored_chars": restored_chars,
        "original_furigana": original_furigana,
    }
    logger.debug("reconstruct_from_alignment - final_result: %s", final_result)

    return reconstruct_furigana(
        final_result,
        with_tags_def,
        reconstruct_type=reconstruct_type,
    )


def whole_word_mora_split(
    word: str, furigana: str
) -> tuple[list[list[list[str]]], list[int], list[int]]:
    """Simple mora split for whole-word case - either the whole furigana or split in half
    Returns: (possible_splits, katakana_positions, long_vowel_positions)
    """
    katakana_positions = get_katakana_positions(furigana)
    if katakana_positions:
        furigana = to_hiragana(furigana)
    furigana, long_vowel_positions = normalize_long_vowel_marks(furigana)
    if len(word) == 2 and word[1] in ("々", word[0]):
        midpoint = max(1, len(furigana) // 2)
        first = furigana[:midpoint]
        second = furigana[midpoint:]
        # Since find_first_complete_alignment expects list of lists, simply return all the chars
        # as separate strings, we don't care about mora here
        return [[list(first), list(second)]], katakana_positions, long_vowel_positions
    return [[list(furigana)]], katakana_positions, long_vowel_positions


def kana_highlight(
    kanji_to_highlight: str | None,
    text: str,
    return_type: FuriReconstruct = "kana_only",
    with_tags_def: WithTagsDef | None = None,
) -> str:
    """
    Function that replaces the furigana of a kanji with the furigana that corresponds to the kanji's
    onyomi or kunyomi reading. The furigana is then highlighted with<b> tags.
    Text received could be a sentence or a single word with furigana.

    A run of digits is read as the kanji it converts into - 24 is 二十四, three readings for two
    characters - and renders as one chunk, since its surface cannot be split per kanji. A
    kanji_to_highlight that a run only converts into therefore bolds the whole run in the furigana
    and furikanji modes: 十 in 24[にじゅうよん] gives<b><mix> 24[ニジュウよん]</mix></b>. The
    kana-only modes have no surface to keep together and bold that one kanji's reading.

    :param kanji_to_highlight: the kanji to highlight, usually a single character but any run of
        kanji works; every occurrence of it in a word is highlighted
    :param text: The text to process
    :param return_type: string. Return either normal furigana, reversed furigana AKA furikanji or
        remove the kanji and return only the kana
    :param with_tags_def: tuple, with_tags and merge_consecutive keys. Whether to wrap the readings
        with tags and whether to merge consecutive tags
    :return: The text with<b> added around the furigana when the furigana corresponds to the
        kanji_to_highlight. Any<b> tags the text already carries are left as they are: the caller
        either supplies text without<b> around the word to highlight, or accepts the nesting
    """
    if with_tags_def is None:
        with_tags_def = WithTagsDef(
            True,  # with_tags
            True,  # merge_consecutive
            True,  # onyomi_to_katakana
            False,  # include_suru_okuri
        )

    def furigana_replacer(match: re.Match):
        """
        Replacer function for KANJI_AND_FURIGANA_REC. This function is called for every match
        found by the regex. It processes the furigana and returns the modified furigana.
        :param match: re.Match, the match object
        :return: string, the modified furigana
        """
        full_word = match.group(1)
        full_furigana = match.group(2)
        maybe_okuri = match.group(3)
        logger.debug(
            "furigana_replacer - word: %s, furigana: %s, okurigana: %s",
            full_word,
            full_furigana,
            maybe_okuri,
        )
        # An audio tag is not furigana. Test the raw bracket content, before any cleaning can
        # turn sound:test.mp3 into an empty string or sound:かんじ.mp3 into a reading, and hand
        # the whole match back untouched — the same thing kana_filter does.
        if full_furigana.startswith("sound:"):
            logger.debug("furigana_replacer - sound tag, left as is: %s", match.group(0))
            return match.group(0)
        # Clean off non-kana characters from furigana, unless it becomes empty
        cleaned_furigana = re.sub(NON_KANA_REC, "", full_furigana)
        if cleaned_furigana:
            logger.debug(
                "furigana_replacer - cleaned furigana: %s from original: %s",
                cleaned_furigana,
                full_furigana,
            )
            full_furigana = cleaned_furigana
        # if furigana is invalid - empty or all non-kana characters - try to return something
        # sensible
        if not full_furigana or not is_kana_str(full_furigana):
            logger.debug("furigana_replacer - empty or invalid furigana case: %s", full_furigana)
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

        # A doubled kanji is only sometimes the repeater 々 written out: 清清[すがすが] is, while
        # the 物物 of 生物物理学[せいぶつぶつりがく] is two words meeting. We can't tell from the
        # spelling alone, so the repeater form is only a *lookup* key here; whether the word is
        # rewritten to use 々 is decided later, by whether the reading says it repeats.
        repeater_word = DOUBLE_KANJI_REC.sub(lambda m: m.group(1) + "々", full_word)
        logger.debug("furigana_replacer - repeater lookup form: %s", repeater_word)

        # Take the kana that carry no reading of their own out of the way, so that what is left can
        # be matched against the kanji's listed readings. They are written back in at the end from
        # the positions recorded here.
        original_furigana = full_furigana
        normalized = normalize_furigana_for_matching(full_furigana)
        full_furigana = normalized["furigana"]
        furigana_prefix = to_hiragana(normalized["prefix"])
        if original_furigana != full_furigana or furigana_prefix:
            logger.debug(
                "furigana_replacer - normalized furigana for matching: %s, prefix: %s,"
                " restored_chars: %s",
                full_furigana,
                normalized['prefix'],
                normalized['restored_chars'],
            )

        def build_restored_chars(long_vowel_positions: list[int]) -> dict[int, str]:
            """
            Index the characters to write back by their position in the original furigana.

            Everything upstream of this works on the normalized furigana, which is the original
            minus the prefix, so the positions shift by the prefix's length. The prefix itself is
            restored the same way, which is also what puts it back in its original script.
            """
            offset = len(furigana_prefix)
            restored = {pos + offset: char for pos, char in normalized["restored_chars"].items()}
            for pos in long_vowel_positions:
                restored[pos + offset] = "ー"
            if normalized["prefix"]:
                restored[0] = normalized["prefix"]
            return restored

        def shift_katakana_positions(positions: list[int]) -> list[int]:
            return [pos + len(furigana_prefix) for pos in positions]

        # The whole-word split hands the entire reading to one kanji, so it only fits a word that
        # *is* one kanji, or a kanji plus its repeater, which it splits in two. Whether that kanji
        # happens to be the one being highlighted has nothing to do with it - asking that let a
        # multi-kanji kanji_to_highlight in here, where the split came back a slot short of the
        # word's kanji count and the whole word fell through to jukujikun.
        word_is_repeated_kanji = len(repeater_word) == 2 and repeater_word[1] == "々"
        is_whole_word_case = len(full_word) == 1 or word_is_repeated_kanji

        def replace_numeric_substrings(text: str) -> str:
            return re.sub(r"[0-9０-９]+", lambda m: number_to_kanji(m.group(0)), text)

        # Step 1: Check exception dictionary first. Exceptions are keyed in the 々 spelling, so a
        # word written with the kanji doubled is looked up in that form - and a hit is proof that
        # the doubling really is a repeater, so the word takes that spelling from here on.
        exception_alignment = check_exception(
            word=repeater_word,
            furigana=full_furigana,
        )
        logger.debug("furigana_replacer - exception_alignment: %s", exception_alignment)
        if exception_alignment is not None:
            logger.debug("furigana_replacer - using exception alignment: %s", exception_alignment)
            full_word = repeater_word
            juku_parts, juku_okurigana, juku_rest_kana = process_jukujikun_positions(
                word=full_word,
                furigana=full_furigana,
                alignment=exception_alignment,
                remaining_kana=maybe_okuri,
            )
            use_okurigana = ""
            use_rest_kana = maybe_okuri
            # process_jukujikun_positions updated the alignment in place, so this and the
            # reconstruction below see the positions and mora it settled on.
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
                katakana_positions=[],
                restored_chars=build_restored_chars([]),
                original_furigana=original_furigana,
                reconstruct_type=return_type,
                furigana_prefix=furigana_prefix,
            )
            return final_result

        # Steps 2-3: Handle mora split either as whole-word or partial-word and find alignment
        # Convert numeric digits to kanji to enable proper reading matching (e.g., ７ → 七).
        # Everything from here to the reconstruction counts positions in this word, not in the
        # digits: 24 is two characters but 二十四 is three readings to place. The reconstruction
        # is the one that has to see the digits, and it maps the positions back to them itself.
        alignment_word = replace_numeric_substrings(full_word)
        alignment = None
        katakana_positions: list[int] = []
        long_vowel_positions: list[int] = []

        if is_whole_word_case:
            possible_whole_word_splits, katakana_positions, long_vowel_positions = (
                whole_word_mora_split(alignment_word, full_furigana)
            )
            logger.debug(
                "furigana_replacer - whole_word_case possible_splits: %s, katakana_positions: %s,"
                " long_vowel_positions: %s",
                possible_whole_word_splits,
                katakana_positions,
                long_vowel_positions,
            )
            alignment = find_first_complete_alignment(
                word=alignment_word,
                furigana=full_furigana,
                maybe_okuri=maybe_okuri,
                possible_splits=possible_whole_word_splits,
            )
        else:
            mora_result = split_to_mora_list(full_furigana, len(alignment_word))
            katakana_positions = mora_result["katakana_positions"]
            long_vowel_positions = mora_result["long_vowel_positions"]
            logger.debug("furigana_replacer - partial_word_case mora_result: %s", mora_result)
            alignment = find_first_complete_alignment(
                word=alignment_word,
                furigana=full_furigana,
                maybe_okuri=maybe_okuri,
                mora_list=mora_result["mora_list"],
            )

        logger.debug("furigana_replacer - juku_positions: %s", alignment['jukujikun_positions'])

        # Step 4: Handle jukujikun positions if any
        final_okurigana = alignment["final_okurigana"]
        final_rest_kana = alignment["final_rest_kana"]
        juku_parts = {}

        if alignment["jukujikun_positions"]:
            # Process the jukujikun positions, which the furigana exceptions may set even on
            # an otherwise complete alignment, to allow okurigana extraction for cases like
            # 清々しい.
            juku_parts, juku_okurigana, juku_rest_kana = process_jukujikun_positions(
                word=alignment_word,
                furigana=full_furigana,
                alignment=alignment,
                remaining_kana=maybe_okuri,
            )
            logger.debug(
                "furigana_replacer - juku_parts: %s, juku_okurigana: %s", juku_parts, juku_okurigana
            )

            # Use jukujikun okurigana when the last kanji is jukujikun. If we already have
            # okurigana from alignment, prefer the longer match from the juku extraction.
            # process_jukujikun_positions updated the alignment in place, so this and the
            # reconstruction below see the positions and mora it settled on.
            if len(alignment_word) - 1 in alignment["jukujikun_positions"]:
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
            katakana_positions=shift_katakana_positions(katakana_positions),
            restored_chars=build_restored_chars(long_vowel_positions),
            original_furigana=original_furigana,
            reconstruct_type=return_type,
            furigana_prefix=furigana_prefix,
        )
        logger.debug("furigana_replacer - final_result: %s\n", final_result)
        return final_result

    # Put a 々 that got separated from its word back into the same furigana group, so that what
    # follows sees one word rather than a 々 with no kanji in front of it to repeat
    clean_text = ORPHANED_REPEATER_CLEANING_REC.sub(orphaned_repeater_cleaning_replacer, text)
    # Give back the kana a word opens with, so the kanji is left holding only its own reading
    clean_text = LEADING_KANA_CLEANING_REC.sub(leading_kana_cleaning_replacer, clean_text)
    # Clean any potential mixed okurigana cases, turning them normal
    clean_text = OKURIGANA_MIX_CLEANING_REC.sub(okurigana_mix_cleaning_replacer, clean_text)
    processed_text = KANJI_AND_FURIGANA_AND_OKURIGANA_REC.sub(furigana_replacer, clean_text)
    logger.debug("processed_text: %s", processed_text)
    # Clean any double spaces that might have been created by the furigana reconstruction
    # Including those right before a <b> tag as the space is added with those
    processed_text = re.sub(r" {2}", " ", processed_text)
    processed_text = re.sub(r" <(b|on|kun|juk|mix)> ", r"<\1> ", processed_text)
    return re.sub(r" <b><(on|kun|juk|mix)> ", r"<b><\1> ", processed_text)
