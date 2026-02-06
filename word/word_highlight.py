import re

try:
    from kana.reading_matcher import check_reading_match
except ImportError:
    from ..kana.reading_matcher import check_reading_match
try:
    from all_types.main_types import OkuriResults
except ImportError:
    from ..all_types.main_types import OkuriResults

try:
    from highlight_inflected_words_with_mecab import highlight_inflected_words_with_mecab
except ImportError:
    from .highlight_inflected_words_with_mecab import (
        highlight_inflected_words_with_mecab,
    )
try:
    from use_tag_cleaning import use_tag_cleaning_with_b_insertion
except ImportError:
    from .use_tag_cleaning import use_tag_cleaning_with_b_insertion
try:
    from okuri.get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab
except ImportError:
    from ..okuri.get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab
try:
    from kana.kana_highlight import kana_highlight, WithTagsDef
except ImportError:
    from ..kana.kana_highlight import kana_highlight, WithTagsDef
try:
    from mecab_controller.kana_conv import to_katakana, to_hiragana, is_kana_str
except ImportError:
    from ..mecab_controller.kana_conv import to_katakana, to_hiragana, is_kana_str
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger

KANJI_AND_MAYBE_FURIGANA_AND_OKURIGANA_RE = (
    r"([\d々\u4e00-\u9faf\u3400-\u4dbf]+)(?:\[([^\]]*?)\])?([ぁ-ん]*)$"
)
LAST_KANJI_FURIGANA_RE = r"([\u4e00-\u9faf\u3400-\u4dbf])(々?)(?:\[([^\]]*?)\])?$"

CONSECUTIVE_FURI_WORD_RE = (
    r"(?: ([\d々\u4e00-\u9faf\u3400-\u4dbf]+)\[([^\]]*?)\])(?:"
    r" ([\d々\u4e00-\u9faf\u3400-\u4dbf]+)\[([^\]]*?)\])"
)


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


def word_highlight(text: str, word: str, logger: Logger) -> str:
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
    logger.debug(f"word_highlight: text='{text}', word='{word}'")
    if not text or not word or not word.strip():
        return text

    if is_kana_str(word):
        logger.debug("Word is kana only, use highlight_inflected_words_with_mecab")
        # This is either a simple case or a complex one needing inflection matching
        # First try a simple regex match
        pattern = make_word_pattern(word)
        logger.debug(f"Using pattern: {pattern}")

        def replace_match(match: re.Match) -> str:
            return f"<b>{match.group(0)}</b>"

        result = re.sub(pattern, replace_match, text)

        if result != text:
            # If that worked, return the result
            return result

        # Otherwise, use MeCab to find inflected forms
        return highlight_inflected_words_with_mecab(text, word, logger=logger)

    # Convert word to hiragana for matching with other methods
    word = to_hiragana(word)

    # We have some kanji in the word to match
    # First, remove kana from the end of the word, to see if there is any okurigana
    word_match = re.search(KANJI_AND_MAYBE_FURIGANA_AND_OKURIGANA_RE, word)
    logger.debug(f"word_match groups: {word_match.groups() if word_match else None}")
    ending_okurigana = word_match.group(3) if word_match else ""
    word_without_furigana = word_match.group(1) if word_match else word[: -len(ending_okurigana)]
    furigana = word_match.group(2) if word_match else ""
    logger.debug(
        f"Parsed word - word_without_furigana: '{word_without_furigana}', furigana: '{furigana}',"
        f" ending_okurigana: '{ending_okurigana}'"
    )

    if not ending_okurigana and not furigana:
        logger.debug("No ending kana and no furigana but have kanji -> simple regex match")
        # Most simple case, we can regex search for the word directly
        pattern = make_word_pattern(word)

        # Remove tags from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text, logger=logger
        )

        def replace_match(match: re.Match) -> str:
            increment_tag_indexes(match.start(0), match.end(0))
            return f"<b>{match.group(0)}</b>"

        result = re.sub(pattern, replace_match, html_free_text)
        logger.debug(f"Intermediate result with <b> tags: '{result}'")
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
        logger.debug(f"word_with_readings_split: {word_with_readings_split}")

        text_with_readings_split = split_furi_text_into_individual_kanji_furigana(text)
        logger.debug(f"text_with_readings_split: {text_with_readings_split}")

        pattern = make_word_pattern(word_with_readings_split)
        logger.debug(f"Using pattern: {pattern}")

        # Remove tags from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text_with_readings_split, logger=logger
        )
        logger.debug(f"html_free_text for matching: '{html_free_text}'")

        def replace_match(match: re.Match) -> str:
            increment_tag_indexes(match.start(0), match.end(0))
            return f"<b>{match.group(0)}</b>"

        result = re.sub(pattern, replace_match, html_free_text)
        logger.debug(f"Intermediate result with <b> tags: '{result}'")

        # Restore tags now, as the tag indexes are based on the split text
        result = restore_tags(result)
        logger.debug(f"Restored html tags result: '{result}'")

        # Re-merge any consecutive furigana parts that were split earlier
        result = merge_consecutive_furigana(result)

        # Remove space from beginning as it's not required
        result = re.sub(r"^(<b>)? ", r"\1", result)
        return result

    # Getting more complicated, need to handle possible inflections
    word = word[: -len(ending_okurigana)]
    logger.debug(
        f"Found ending kana, handling possible inflections: ending_okurigana='{ending_okurigana}',"
        f" word='{word}', word_without_furigana='{word_without_furigana}'"
    )

    if not furigana:
        logger.debug("No furigana but have kanji with okuri, use get_conjugated_okuri_with_mecab")
        pattern = make_word_pattern(word)
        # Add regex for possible okurigana after the word, we'll try to match inflections to those
        pattern += rf"((?:{ending_okurigana})|(?:[ぁ-んア-ン]*))"
        # Remove tags from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text, logger=logger
        )
        logger.debug(f"html_free_text for matching: '{html_free_text}'")
        matches = re.finditer(pattern, html_free_text)
        result_indices: list[tuple[int, int]] = []
        for m in matches:
            maybe_okuri = m.group(1)
            logger.debug(
                f"Found potential match at indices ({m.start(0)}, {m.end(0)}),"
                f" maybe_okuri: '{maybe_okuri}'"
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
                logger=logger,
            )
            logger.debug(
                f"okuri_result: okurigana: '{okuri_result.okurigana}', rest_kana:"
                f" '{okuri_result.rest_kana}', result: '{okuri_result.result}', part_of_speech:"
                f" '{okuri_result.part_of_speech}'"
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
        result = html_free_text

        for idx in range(len(result_indices)):
            start, end = result_indices[idx]
            # Increment for tags inside (but not on exact same position) or after the opening tag
            increment_tag_indexes(start, end)
            result = result[:start] + "<b>" + result[start:end] + "</b>" + result[end:]
            logger.debug(f"Result after {idx + 1} <b> insertions: '{result}'")
            # Adjust subsequent indices due to added tag lengths
            for j in range(idx + 1, len(result_indices)):
                s, e = result_indices[j]
                result_indices[j] = (s + 7, e + 7)
        logger.debug(f"Intermediate result with <b> tags: '{result}'")
        result = restore_tags(result)
        logger.debug(f"Restored html tags result: '{result}'")
        return result
    else:
        logger.debug("Furigana present, using kana_highlight for inflection matching")
        # Furigana is present, so use kana_highlight to find the inflected forms for the last kanji
        # while matching the beginning part with direct regex search
        word_with_readings_split = split_furi_text_into_individual_kanji_furigana(word)
        logger.debug(f"word_with_readings_split: {word_with_readings_split}")
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
                f"Found last kanji in split word: '{last_kanji}', repeater: '{repeater}',"
                f" last_kanji_furigana: '{last_kanji_furigana}'"
            )
            return ""

        word_with_readings_split = re.sub(
            LAST_KANJI_FURIGANA_RE, remove_from_split_word, word_with_readings_split
        )

        logger.debug(
            f" last_kanji: '{last_kanji}', last_kanji_furigana: '{last_kanji_furigana}', "
            f" remaining word_with_readings_split: '{word_with_readings_split}'"
        )
        # Split the whole text similarly
        text_with_readings_split = split_furi_text_into_individual_kanji_furigana(text)
        logger.debug(f"text_with_readings_split: {text_with_readings_split}")
        # Find all occurrences of the word_with_readings_split in the text_with_readings_split
        pattern = make_word_pattern(word_with_readings_split)
        # Replace the furigana part for the last kanji in the regex pattern so that all
        # kana are allowed, this allows for matching inflected forms where the base reading
        # changes, like rendaku, small tsu, vowel changes etc.
        if last_kanji:
            pattern += rf"{last_kanji}{repeater}\[(?P<furigana>[^\]]+)\]"
        pattern += rf"(?P<maybe_okuri>(?:{ending_okurigana})|(?:[ぁ-んア-ン]*))"
        logger.debug(f"Regex pattern for matching: '{pattern}'")

        # Remove tags from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text_with_readings_split, logger=logger
        )
        logger.debug(f"html_free_text for matching: '{html_free_text}', pattern: '{pattern}'")
        matches = list(re.finditer(pattern, html_free_text))
        logger.debug(f"Found {len(matches)} matches")
        result_indices: list[tuple[int, int]] = []
        for m in matches:
            # For each match, check if the last kanji's furigana can be inflected to match
            # the ending_okurigana
            # Find the position of the last kanji in the matched text
            matched_text = html_free_text[m.start(0) : m.end(0)]
            furigana = m.group("furigana")
            maybe_okuri = m.group("maybe_okuri")
            if maybe_okuri == ending_okurigana:
                # Exact match, no inflection needed
                logger.debug(
                    f"Exact match found for matched text: '{matched_text}',"
                    f" maybe_okuri: '{maybe_okuri}'"
                )
                result_indices.append((m.start(0), m.end(0)))
                continue
            logger.debug(
                f"Matched text for kana_highlight inflection check: '{matched_text}',"
                f" maybe_okuri: '{maybe_okuri}', match: {m}"
            )

            # Check if after_last_kanji contains a valid inflection for the ending_okurigana
            logger.debug(
                f"Checking inflected forms for last kanji with mecab, last_kanji: '{last_kanji}',"
                f" last_kanji_furigana: '{last_kanji_furigana}'"
            )

            if last_kanji and furigana:
                # furigana should match the last_kanji_furigana, with all variations considered
                _, reading_match_type = check_reading_match(
                    reading=last_kanji_furigana,
                    mora_string=furigana,
                    okurigana=maybe_okuri,
                    logger=logger,
                )
                if reading_match_type == "none":
                    logger.debug(
                        f"Furigana '{furigana}' does not match last kanji furigana"
                        f" '{last_kanji_furigana}', so no okuri match"
                    )
                    kanji_okuri_result = OkuriResults(
                        result="no_okuri", okurigana="", rest_kana="", part_of_speech=""
                    )
                else:
                    kanji_okuri_result, _ = get_conjugated_okuri_with_mecab(
                        word=last_kanji,
                        reading=last_kanji_furigana,
                        maybe_okuri=to_hiragana(maybe_okuri),
                        okuri_prefix="word",
                        logger=logger,
                    )
            if kanji_okuri_result.result != "no_okuri":
                okuri_result = kanji_okuri_result
                logger.debug(
                    "Valid inflected form found for last kanji, okurigana:"
                    f" '{okuri_result.okurigana}'"
                )
            else:
                logger.debug(
                    "No valid inflected form found for last kanji, trying full word with furigana"
                    f" '{word_without_furigana}' and furigana '{furigana}'"
                )
                word_okuri_result, _ = get_conjugated_okuri_with_mecab(
                    word=word_without_furigana,
                    reading=furigana,
                    maybe_okuri=to_hiragana(maybe_okuri),
                    okuri_prefix="word",
                    logger=logger,
                )
                okuri_result = word_okuri_result
            logger.debug(
                f"Furigana split okuri_result: okurigana: '{okuri_result.okurigana}', rest_kana:"
                f" '{okuri_result.rest_kana}', result: '{okuri_result.result}', part_of_speech:"
                f" '{okuri_result.part_of_speech}'"
            )
            if okuri_result.result != "no_okuri":
                # We have a valid inflected form, extend end index to include the okurigana
                logger.debug(
                    "Found valid inflected form with kana_highlight, okurigana:"
                    f" '{okuri_result.okurigana}', maybe_okuri: '{maybe_okuri}'"
                )
                result_indices.append((
                    m.start(0),
                    m.end(0) - len(maybe_okuri) + len(okuri_result.okurigana),
                ))
            else:
                logger.debug("No valid inflected form found with kana_highlight")
                result_indices.append((m.start(0), m.end(0) - len(maybe_okuri)))

        # Insert <b> tags into the text at the found indices
        result = html_free_text
        for idx in range(len(result_indices)):
            start, end = result_indices[idx]
            increment_tag_indexes(start, end)
            result = result[:start] + "<b>" + result[start:end] + "</b>" + result[end:]
            # Adjust subsequent indices due to added tag lengths
            for j in range(idx + 1, len(result_indices)):
                s, e = result_indices[j]
                result_indices[j] = (s + 7, e + 7)
        logger.debug(f"Intermediate result with <b> tags: '{result}'")
        # Restore tags now, as the tag indexes are based on the split text
        result = restore_tags(result)
        logger.debug(f"Restored html tags result: '{result}'")
        # Re-merge any consecutive furigana parts that were split earlier
        result = merge_consecutive_furigana(result)
        # Remove space from beginning as it's not required
        result = re.sub(r"^(<b>)? ", r"\1", result)
        return result

    return text
