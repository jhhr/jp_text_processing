import re

from ..kana.reading_matcher import check_reading_match
from ..all_types.main_types import OkuriResults

from .highlight_inflected_words_with_mecab import (
    highlight_inflected_words_with_mecab,
)
from .use_tag_cleaning import use_tag_cleaning_with_b_insertion
from .use_splitter_dot_cleaning import use_splitter_dot_cleaning_with_b_insertion
from ..okuri.get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab
from ..kana.kana_highlight import kana_highlight, WithTagsDef
from ..mecab_controller.kana_conv import to_katakana, to_hiragana, is_kana_str
from ..regex.kanji_furi import KANJI_RANGES
from ..utils.logger import package_logger as logger

KANJI_AND_MAYBE_FURIGANA_AND_OKURIGANA_RE = (
    rf"([\d々{KANJI_RANGES}ヶヵ]+)(?:\[([^\]]*?)\])?([ぁ-ん]*)$"
)
LAST_KANJI_FURIGANA_RE = rf"([{KANJI_RANGES}ヶヵ])(々?)(?:\[([^\]]*?)\])?$"

CONSECUTIVE_FURI_WORD_RE = (
    rf"(?: ([\d々{KANJI_RANGES}ヶヵ]+)\[([^\]]*?)\])(?:"
    rf" ([\d々{KANJI_RANGES}ヶヵ]+)\[([^\]]*?)\])"
)
FURIGANA_TOKEN_RE = rf"([\d々{KANJI_RANGES}ヶヵ]+)\[([^\]]*?)\]"


def replace_hiragana_in_pattern(text: str) -> str:
    # Replace each hiragana character with a katanana or hiragana option
    def replace_hiragana(match: re.Match) -> str:
        char = match.group(0)
        katakana_char = to_katakana(char)
        return rf"(?:{char}|{katakana_char})"

    return re.sub(r"[ぁ-ん]", replace_hiragana, text)


def make_word_pattern(word: str) -> str:
    # Remove first space
    word = re.sub(r"^ ", "", word)
    # Escape the word for regex special characters
    escaped_word = re.escape(word)
    escaped_word = replace_hiragana_in_pattern(escaped_word)
    return rf"\s?{escaped_word}"


def make_furigana_agnostic_pattern(word: str) -> tuple[str, list[str]]:
    """Create a regex pattern that captures furigana sections for variant checking.

    The generated pattern keeps kanji and separators strict, but allows the furigana
    inside brackets to vary. Captured furigana values can then be validated via
    check_reading_match (rendaku/small-tsu/vowel-change, etc.).
    """
    word = re.sub(r"^ ", "", word)
    expected_readings: list[str] = []
    pattern_parts: list[str] = [r"\s?"]
    cursor = 0
    for idx, match in enumerate(re.finditer(FURIGANA_TOKEN_RE, word)):
        literal_prefix = word[cursor : match.start()]
        if literal_prefix:
            pattern_parts.append(replace_hiragana_in_pattern(re.escape(literal_prefix)))
        kanji = match.group(1)
        expected_readings.append(to_hiragana(match.group(2)))
        pattern_parts.append(rf"{re.escape(kanji)}\[(?P<furi_{idx}>[^\]]+)\]")
        cursor = match.end()
    literal_suffix = word[cursor:]
    if literal_suffix:
        pattern_parts.append(replace_hiragana_in_pattern(re.escape(literal_suffix)))
    return "".join(pattern_parts), expected_readings


def furigana_captures_match_readings(
    match: re.Match,
    expected_readings: list[str],
) -> bool:
    """Validate captured furigana readings against expected readings with variants."""
    for idx, expected in enumerate(expected_readings):
        observed = to_hiragana(match.group(f"furi_{idx}"))
        _, reading_match_type = check_reading_match(
            reading=expected,
            mora_string=observed,
            okurigana="",
        )
        if reading_match_type == "none":
            return False
    return True


def preserve_small_counter_kana(text: str) -> str:
    # Keep Japanese counter kana in katakana form after to_hiragana conversion.
    return text.replace("ゕ", "ヵ").replace("ゖ", "ヶ")


def split_furi_text_into_individual_kanji_furigana(furi_text: str) -> str:
    """Splits a furigana text into individual kanji-furigana parts with kana_highlight.

    Args:
        furi_text (str): The furigana text to split.

    Returns:
        str: The split furigana text.
    """
    furi_text = kana_highlight(
        text=furi_text,
        kanji_to_highlight="",
        return_type="furigana",
        with_tags_def=WithTagsDef(
            with_tags=True,
            merge_consecutive=False,
            onyomi_to_katakana=False,
            include_suru_okuri=False,
        ),
    )
    # Replace tags so that we now have all kanji furigana split except for repeaters
    furi_text = re.sub(r"</?(?:on|kun|juk|mix|oku)>", "", furi_text)
    return furi_text


def merge_consecutive_furigana(split_furi_text: str) -> str:
    """Merges consecutive kanji-furigana parts back into a single furigana text.

    Args:
        split_furi_text (str): The split furigana text.
    Returns:
        str: The merged furigana text.
    """
    pattern = re.compile(CONSECUTIVE_FURI_WORD_RE)
    while match := pattern.search(split_furi_text):
        first_kanji = match.group(1)
        first_furi = match.group(2)
        second_kanji = match.group(3)
        second_furi = match.group(4)
        merged_kanji = first_kanji + second_kanji
        merged_furi = first_furi + second_furi
        merged_text = f" {merged_kanji}[{merged_furi}]"
        split_furi_text = (
            split_furi_text[: match.start(0)] + merged_text + split_furi_text[match.end(0) :]
        )
    return split_furi_text


def word_highlight(text: str, word: str) -> str:
    """
    Takes a japanese word or phrase in dictionary form and finds any inflected occurrences of
    it in the given text. The word and text is expected to be in furigana syntax; with brackets
    containing the reading of the kanji words.

    Furigana syntax in text includes a space before the word begins, e.g "この 家[いえ]は" with the
    exception that the beginning of the string can omit the space, e.g "家[いえ]で 居[い]る".

    The word is then expected to be in the same syntax, e.g "家[いえ]". but the matched occurrence
    in the should include the space before the word. For example:

    word_highlight("この 家[いえ]は", "家[いえ]") --> "この<b> 家[いえ]</b>は"
    word_highlight("家[いえ]で 居[い]る", "家[いえ]") --> "<b>家[いえ]</b>で 居[い]る"

    Inflected forms are found for verbs up and including auxiliary verbs like いる, させる, せる
    negation forms like ない, させない, せない, な but not すぎる, すぎない.
    For example:
    word_highlight("私は 食[た]べている", "食[た]べる") --> "私は<b> 食[た]べている</b>"
    word_highlight() --> "<b>食[た]べさせる</b>な!"

    For adjectives, the inflected forms are found up to and including the い form, but not
    the な form except when な is included in the word to match.
    For example:
    word_highlight("これ、 大[おお]きすぎない？", "大[おお]きい") --> "これ、 <b> 大[おお]き</b>すぎない？"
    word_highlight("大[おお]きな 家[いえ]", "大[おお]きい") --> "<b>大[おお]き</b>な 家[いえ]"
    word_highlight("大[おお]きな 家[いえ]", "大[おお]きいな") --> "<b>大[おお]きな</b> 家[いえ]"
    word_highlight("安[やす]くて 良[い]いな～", "安[やす]い") --> "<b>安[やす]くて</b> 良[い]いな～"
    word_highlight("高[たか]いでも 良[よ]かろう", "良[い]い") --> "高[たか]いでも<b> 良[よ]かろう</b>"

    Args:
        text (str): The input text where the word needs to be highlighted.
        word (str): The word to highlight.

    Returns:
        list[tuple[int,int]]: A list of tuples containing the start and end indices of the
        word occurrences in the text.
    """
    logger.debug("word_highlight: text='%s', word='%s'", text, word)
    if not text or not word or not word.strip():
        return text

    if is_kana_str(word):
        logger.debug("Word is kana only, use highlight_inflected_words_with_mecab")
        # This is either a simple case or a complex one needing inflection matching
        # First try a simple regex match
        pattern = make_word_pattern(word)
        logger.debug("Using pattern: %s", pattern)

        def replace_match(match: re.Match) -> str:
            return f"<b>{match.group(0)}</b>"

        result = re.sub(pattern, replace_match, text)

        if result != text:
            # If that worked, return the result
            return result

        # Otherwise, use MeCab to find inflected forms
        return highlight_inflected_words_with_mecab(text, word)

    # Strip trailing katakana suffix after furigana (with optional hiragana okuri)
    # before to_hiragana so it is not mistaken for inflectable okurigana.
    katakana_suffix_after_furi_match = re.search(r"(\[[^\]]*?\])([ぁ-ん]*)([ァ-ン]+)$", word)
    katakana_fixed_suffix = (
        katakana_suffix_after_furi_match.group(3) if katakana_suffix_after_furi_match else ""
    )
    if katakana_fixed_suffix:
        word = word[: -len(katakana_fixed_suffix)]
        logger.debug(
            "Detected fixed katakana suffix: '%s', word without suffix: '%s'",
            katakana_fixed_suffix,
            word,
        )

    # Convert word to hiragana for matching with other methods while preserving
    # small counter kana (e.g. ヶ/ヵ), which are meaningful inside kanji words.
    word = preserve_small_counter_kana(to_hiragana(word))

    # We have some kanji in the word to match
    # First, remove kana from the end of the word, to see if there is any okurigana
    word_match = re.search(KANJI_AND_MAYBE_FURIGANA_AND_OKURIGANA_RE, word)
    logger.debug("word_match groups: %s", word_match.groups() if word_match else None)
    ending_okurigana = word_match.group(3) if word_match else ""
    word_without_furigana = word_match.group(1) if word_match else word[: -len(ending_okurigana)]
    furigana = word_match.group(2) if word_match else ""
    logger.debug(
        "Parsed word - word_without_furigana: '%s', furigana: '%s', ending_okurigana: '%s'",
        word_without_furigana,
        furigana,
        ending_okurigana,
    )

    if not ending_okurigana and not furigana:
        logger.debug("No ending kana and no furigana but have kanji -> simple regex match")
        # Most simple case, we can regex search for the word directly
        pattern = make_word_pattern(word)

        # Remove tags from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text
        )
        logger.debug("html_free_text for matching: '%s'", html_free_text)

        (
            splitter_free_text,
            increment_splitter_indexes,
            restore_splitters,
            _,
            split_free_to_original_index,
        ) = use_splitter_dot_cleaning_with_b_insertion(html_free_text)

        # re.sub reports every match's position in its input, which has none of the b tags the
        # earlier matches got. The splitter bookkeeping works in those same positions, but the
        # tag bookkeeping counts the inserted tags, so they are added on for it - once to get
        # from the reported position to the current one, and once more because converting
        # through the splitter indexes takes them back off.
        b_tags_inserted = 0

        def to_tag_index(split_free_index: int) -> int:
            edited_index = split_free_index + b_tags_inserted
            return split_free_to_original_index(edited_index) + b_tags_inserted

        def replace_match(match: re.Match) -> str:
            nonlocal b_tags_inserted
            split_start = match.start(0)
            split_end = match.end(0)
            increment_tag_indexes(to_tag_index(split_start), to_tag_index(split_end))
            increment_splitter_indexes(split_start, split_end)
            b_tags_inserted += len("<b></b>")
            return f"<b>{match.group(0)}</b>"

        result = re.sub(pattern, replace_match, splitter_free_text)
        logger.debug("Intermediate result with <b> tags: '%s'", result)
        result = restore_splitters(result)
        result = restore_tags(result)
        return result
    elif not ending_okurigana and furigana:
        logger.debug("No ending kana but has furigana -> split and regex match, then reconstruct")
        # Relatively simple case, we can regex search for the word
        # However, we need to make sure the word's furigana matches the text's furigana and
        # the text isn't including more or less kanji in the word

        # So, we need to split the word and text into individual kanji-furigana parts and
        # then match those parts, reconstructing the furigana back afterwards
        word_with_readings_split = split_furi_text_into_individual_kanji_furigana(word)
        logger.debug("word_with_readings_split: %s", word_with_readings_split)

        text_with_readings_split = split_furi_text_into_individual_kanji_furigana(text)
        logger.debug("text_with_readings_split: %s", text_with_readings_split)

        pattern, expected_readings = make_furigana_agnostic_pattern(word_with_readings_split)
        if katakana_fixed_suffix:
            # Append the fixed katakana suffix to the pattern, matching both katakana and hiragana.
            katakana_suffix_pattern = replace_hiragana_in_pattern(
                to_hiragana(katakana_fixed_suffix)
            )
            pattern += katakana_suffix_pattern
            logger.debug("Appended fixed katakana suffix pattern: '%s'", katakana_suffix_pattern)
        logger.debug("Using pattern: %s", pattern)

        # Remove tags from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text_with_readings_split
        )
        logger.debug("html_free_text for matching: '%s'", html_free_text)

        (
            splitter_free_text,
            increment_splitter_indexes,
            restore_splitters,
            _,
            split_free_to_original_index,
        ) = use_splitter_dot_cleaning_with_b_insertion(
            html_free_text,
            splitter_regex=r"・",
        )
        logger.debug("splitter_free_text for matching: '%s'", splitter_free_text)

        # As above: the positions re.sub reports know nothing of the b tags already inserted
        b_tags_inserted = 0

        def to_tag_index(split_free_index: int) -> int:
            edited_index = split_free_index + b_tags_inserted
            return split_free_to_original_index(edited_index) + b_tags_inserted

        def replace_match(match: re.Match) -> str:
            nonlocal b_tags_inserted
            has_variant = False
            for idx, expected in enumerate(expected_readings):
                observed = to_hiragana(match.group(f"furi_{idx}"))
                _, reading_match_type = check_reading_match(
                    reading=expected,
                    mora_string=observed,
                    okurigana="",
                )
                if reading_match_type == "none":
                    return match.group(0)
                if reading_match_type != "plain":
                    has_variant = True

            match_text = match.group(0)
            split_start = match.start(0)
            split_end = match.end(0)
            leading_ws = ""
            if has_variant and split_start > 0 and match_text[:1].isspace():
                leading_ws = match_text[0]
                match_text = match_text[1:]
                split_start += 1

            if not match_text:
                return match.group(0)

            increment_tag_indexes(to_tag_index(split_start), to_tag_index(split_end))
            increment_splitter_indexes(split_start, split_end)
            b_tags_inserted += len("<b></b>")
            return f"{leading_ws}<b>{match_text}</b>"

        result = re.sub(pattern, replace_match, splitter_free_text)
        logger.debug("Intermediate result with <b> tags: '%s'", result)

        result = restore_splitters(result)

        # Restore tags now, as the tag indexes are based on the split text
        result = restore_tags(result)
        logger.debug("Restored html tags result: '%s'", result)

        # Re-merge any consecutive furigana parts that were split earlier
        result = merge_consecutive_furigana(result)

        # Remove space from beginning as it's not required
        result = re.sub(r"^(<b>)? ", r"\1", result)
        return result

    # Getting more complicated, need to handle possible inflections
    word = word[: -len(ending_okurigana)]
    logger.debug(
        "Found ending kana, handling possible inflections: ending_okurigana='%s', word='%s',"
        " word_without_furigana='%s'",
        ending_okurigana,
        word,
        word_without_furigana,
    )

    if not furigana:
        logger.debug("No furigana but have kanji with okuri, use get_conjugated_okuri_with_mecab")
        pattern = make_word_pattern(word)
        # Add regex for possible okurigana after the word, we'll try to match inflections to those
        pattern += rf"((?:{ending_okurigana})|(?:[ぁ-んア-ン]*))"
        # Remove tags from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text
        )
        logger.debug("html_free_text for matching: '%s'", html_free_text)

        (
            splitter_free_text,
            increment_splitter_indexes,
            restore_splitters,
            _,
            split_free_to_original_index,
        ) = use_splitter_dot_cleaning_with_b_insertion(
            html_free_text,
            splitter_regex=r"・",
        )
        logger.debug("splitter_free_text for matching: '%s'", splitter_free_text)
        matches = list(re.finditer(pattern, splitter_free_text))
        result_indices: list[tuple[int, int]] = []
        for m in matches:
            maybe_okuri = m.group(1)
            logger.debug(
                "Found potential match at indices (%s, %s), maybe_okuri: '%s'",
                m.start(0),
                m.end(0),
                maybe_okuri,
            )
            if maybe_okuri == ending_okurigana:
                # Exact match, no need to check inflection
                logger.debug("Exact match found, no inflection check needed")
                result_indices.append((m.start(0), m.end(0)))
                continue
            # Check if the maybe_okuri contains a valid inflection for the ending_okurigana
            okuri_result, _ = get_conjugated_okuri_with_mecab(
                word=word_without_furigana,
                reading=furigana,
                maybe_okuri=to_hiragana(maybe_okuri),
                okuri_prefix="word",
            )
            logger.debug(
                "okuri_result: okurigana: '%s', rest_kana: '%s', result: '%s', part_of_speech:"
                " '%s'",
                okuri_result.okurigana,
                okuri_result.rest_kana,
                okuri_result.result,
                okuri_result.part_of_speech,
            )
            if okuri_result.result != "no_okuri":
                # We have a valid inflected form, extend end index to include the okurigana
                logger.debug("Found valid inflected form")
                result_indices.append(
                    (m.start(0), m.end(0) - len(maybe_okuri) + len(okuri_result.okurigana))
                )
            else:
                logger.debug("No valid inflected form found")
                result_indices.append((m.start(0), m.end(0) - len(maybe_okuri)))

        # Insert <b> tags into the text at the found indices
        result = splitter_free_text

        for idx in range(len(result_indices)):
            start, end = result_indices[idx]
            # Increment for tags inside (but not on exact same position) or after the opening tag
            increment_tag_indexes(
                split_free_to_original_index(start),
                split_free_to_original_index(end),
            )
            increment_splitter_indexes(start, end)
            result = result[:start] + "<b>" + result[start:end] + "</b>" + result[end:]
            logger.debug("Result after %s <b> insertions: '%s'", idx + 1, result)
            # Adjust subsequent indices due to added tag lengths
            for j in range(idx + 1, len(result_indices)):
                s, e = result_indices[j]
                result_indices[j] = (s + 7, e + 7)
        logger.debug("Intermediate result with <b> tags: '%s'", result)
        result = restore_splitters(result)
        result = restore_tags(result)
        logger.debug("Restored html tags result: '%s'", result)
        return result
    else:
        logger.debug("Furigana present, using kana_highlight for inflection matching")
        # Furigana is present, so use kana_highlight to find the inflected forms for the last kanji
        # while matching the beginning part with direct regex search
        word_with_readings_split = split_furi_text_into_individual_kanji_furigana(word)
        logger.debug("word_with_readings_split: %s", word_with_readings_split)
        # Get the last kanji character and its furigana, while removing it from the split word
        last_kanji = ""
        repeater = ""
        last_kanji_furigana = ""

        def remove_from_split_word(match: re.Match) -> str:
            nonlocal last_kanji, repeater, last_kanji_furigana
            last_kanji = match.group(1) if match else ""
            repeater = match.group(2) if match else ""
            last_kanji_furigana = match.group(3) if match else ""
            logger.debug(
                "Found last kanji in split word: '%s', repeater: '%s', last_kanji_furigana: '%s'",
                last_kanji,
                repeater,
                last_kanji_furigana,
            )
            return ""

        word_with_readings_split = re.sub(
            LAST_KANJI_FURIGANA_RE, remove_from_split_word, word_with_readings_split
        )

        logger.debug(
            " last_kanji: '%s', last_kanji_furigana: '%s',  remaining word_with_readings_split:"
            " '%s'",
            last_kanji,
            last_kanji_furigana,
            word_with_readings_split,
        )
        # Split the whole text similarly
        text_with_readings_split = split_furi_text_into_individual_kanji_furigana(text)
        logger.debug("text_with_readings_split: %s", text_with_readings_split)
        # Find all occurrences of the word_with_readings_split in the text_with_readings_split
        pattern, prefix_expected_readings = make_furigana_agnostic_pattern(word_with_readings_split)
        # Replace the furigana part for the last kanji in the regex pattern so that all
        # kana are allowed, this allows for matching inflected forms where the base reading
        # changes, like rendaku, small tsu, vowel changes etc.
        if last_kanji:
            pattern += rf"{last_kanji}{repeater}\[(?P<furigana>[^\]]+)\]"
        pattern += rf"(?P<maybe_okuri>(?:{ending_okurigana})|(?:[ぁ-んア-ン]*))"
        logger.debug("Regex pattern for matching: '%s'", pattern)

        # Remove tags from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text_with_readings_split
        )

        (
            splitter_free_text,
            increment_splitter_indexes,
            restore_splitters,
            _,
            split_free_to_original_index,
        ) = use_splitter_dot_cleaning_with_b_insertion(html_free_text)
        logger.debug(
            "splitter_free_text for matching: '%s', pattern: '%s'", splitter_free_text, pattern
        )
        matches = list(re.finditer(pattern, splitter_free_text))
        logger.debug("Found %s matches", len(matches))
        result_indices = []
        for m in matches:
            if not furigana_captures_match_readings(m, prefix_expected_readings):
                logger.debug("Skipping match; prefix furigana does not match expected readings")
                continue
            # For each match, check if the last kanji's furigana can be inflected to match
            # the ending_okurigana
            # Find the position of the last kanji in the matched text
            matched_text = splitter_free_text[m.start(0) : m.end(0)]
            furigana = m.group("furigana")
            maybe_okuri = m.group("maybe_okuri")
            reading_match_type = "plain"
            if last_kanji and furigana:
                _, reading_match_type = check_reading_match(
                    reading=last_kanji_furigana,
                    mora_string=to_hiragana(furigana),
                    okurigana=to_hiragana(maybe_okuri),
                )
            if maybe_okuri == ending_okurigana:
                if reading_match_type == "none":
                    logger.debug(
                        "Skipping exact okuri match; furigana '%s' does not match last kanji"
                        " reading '%s'",
                        furigana,
                        last_kanji_furigana,
                    )
                    continue
                # Exact match, no inflection needed
                logger.debug(
                    "Exact match found for matched text: '%s', maybe_okuri: '%s'",
                    matched_text,
                    maybe_okuri,
                )
                result_indices.append((m.start(0), m.end(0)))
                continue
            logger.debug(
                "Matched text for kana_highlight inflection check: '%s', maybe_okuri: '%s', match:"
                " %s",
                matched_text,
                maybe_okuri,
                m,
            )

            # Check if after_last_kanji contains a valid inflection for the ending_okurigana
            logger.debug(
                "Checking inflected forms for last kanji with mecab, last_kanji: '%s',"
                " last_kanji_furigana: '%s'",
                last_kanji,
                last_kanji_furigana,
            )

            kanji_okuri_result = OkuriResults(
                result="no_okuri",
                okurigana="",
                rest_kana="",
            )
            if last_kanji and furigana:
                if reading_match_type != "none":
                    kanji_okuri_result, _ = get_conjugated_okuri_with_mecab(
                        word=last_kanji,
                        reading=last_kanji_furigana,
                        maybe_okuri=to_hiragana(maybe_okuri),
                        okuri_prefix="word",
                    )
            if kanji_okuri_result.result != "no_okuri":
                okuri_result = kanji_okuri_result
                logger.debug(
                    "Valid inflected form found for last kanji, okurigana: '%s'",
                    okuri_result.okurigana,
                )
            else:
                logger.debug(
                    "No valid inflected form found for last kanji, trying full word with furigana"
                    " '%s' and furigana '%s'",
                    word_without_furigana,
                    furigana,
                )
                word_okuri_result, _ = get_conjugated_okuri_with_mecab(
                    word=word_without_furigana,
                    reading=furigana,
                    maybe_okuri=to_hiragana(maybe_okuri),
                    okuri_prefix="word",
                )
                okuri_result = word_okuri_result
            logger.debug(
                "Furigana split okuri_result: okurigana: '%s', rest_kana: '%s', result: '%s',"
                " part_of_speech: '%s'",
                okuri_result.okurigana,
                okuri_result.rest_kana,
                okuri_result.result,
                okuri_result.part_of_speech,
            )
            if okuri_result.result != "no_okuri":
                # We have a valid inflected form, extend end index to include the okurigana
                logger.debug(
                    "Found valid inflected form with kana_highlight, okurigana: '%s', maybe_okuri:"
                    " '%s'",
                    okuri_result.okurigana,
                    maybe_okuri,
                )
                result_indices.append((
                    m.start(0),
                    m.end(0) - len(maybe_okuri) + len(okuri_result.okurigana),
                ))
            else:
                logger.debug("No valid inflected form found with kana_highlight")
                result_indices.append((m.start(0), m.end(0) - len(maybe_okuri)))

        # Insert <b> tags into the text at the found indices
        # Extend each end index to include the fixed katakana suffix when present in the text
        if katakana_fixed_suffix:
            katakana_suffix_re = replace_hiragana_in_pattern(to_hiragana(katakana_fixed_suffix))
            suffix_len = len(katakana_fixed_suffix)
            logger.debug(
                "Extending result_indices end by fixed katakana suffix '%s'", katakana_fixed_suffix
            )
            # Only keep matches where the suffix is present immediately after the okuri end;
            # filter out incidental matches that lack the suffix (e.g. 彫[ほ]る without ナイフ).
            result_indices = [
                (start, end + suffix_len)
                for start, end in result_indices
                if re.match(katakana_suffix_re, splitter_free_text[end:])
            ]
        result = splitter_free_text
        for idx in range(len(result_indices)):
            start, end = result_indices[idx]
            increment_tag_indexes(
                split_free_to_original_index(start),
                split_free_to_original_index(end),
            )
            increment_splitter_indexes(start, end)
            result = result[:start] + "<b>" + result[start:end] + "</b>" + result[end:]
            # Adjust subsequent indices due to added tag lengths
            for j in range(idx + 1, len(result_indices)):
                s, e = result_indices[j]
                result_indices[j] = (s + 7, e + 7)
        logger.debug("Intermediate result with <b> tags: '%s'", result)
        result = restore_splitters(result)
        # Restore tags now, as the tag indexes are based on the split text
        result = restore_tags(result)
        logger.debug("Restored html tags result: '%s'", result)
        # Re-merge any consecutive furigana parts that were split earlier
        result = merge_consecutive_furigana(result)
        # Remove space from beginning as it's not required
        result = re.sub(r"^(<b>)? ", r"\1", result)
        return result

    return text
