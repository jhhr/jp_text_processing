import re
from typing import Optional

try:
    from all_types.main_types import PartOfSpeech
except ImportError:
    from ..all_types.main_types import PartOfSpeech
try:
    from mecab_controller.basic_types import MecabParsedToken
except ImportError:
    from ..mecab_controller.basic_types import MecabParsedToken
try:
    from okuri.mecab_common import (
        get_all_conjugation_conditions,
        get_word_type_from_mecab_token,
        mecab,
        MecabWordType,
    )
except ImportError:
    from ..okuri.mecab_common import (
        get_all_conjugation_conditions,
        get_word_type_from_mecab_token,
        mecab,
        MecabWordType,
    )
try:
    from mecab_controller.kana_conv import to_hiragana, to_katakana
except ImportError:
    from ..mecab_controller.kana_conv import to_hiragana, to_katakana
try:
    from okuri.get_conjugatable_okurigana_stem import CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH
except ImportError:
    from ..okuri.get_conjugatable_okurigana_stem import CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH
try:
    from okuri.okurigana_dict import GODAN_FORM_VERB_STARTINGS
except ImportError:
    from ..okuri.okurigana_dict import GODAN_FORM_VERB_STARTINGS
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger


def highlight_inflected_words_with_mecab(
    text: str, base_form_word: str, logger: Logger = Logger("error")
) -> str:
    """
    Find inflected words in the given text using MeCab.
    :param text: The text to analyze.
    :return: String with <b> tags around each inflected occurrence of the base form word
    """
    if not text or not base_form_word:
        return text

    # Determine the word type from the base form word
    word_type: Optional[MecabWordType] = None
    base_form_word_ending = base_form_word[-1]
    possible_parts_of_speech: list[PartOfSpeech] = []
    # Check if the last character is in the conjugatable okuri list
    if base_form_word_ending in CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH:
        possible_parts_of_speech = CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH.get(base_form_word_ending)
    elif base_form_word_ending in GODAN_FORM_VERB_STARTINGS:
        # Or, if it's a godan verb in noun form, convert to dictionary form
        base_form_word_ending = GODAN_FORM_VERB_STARTINGS[base_form_word_ending]
        possible_parts_of_speech = CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH.get(base_form_word_ending)
    word_stem = base_form_word[:-1]
    # Set noun form verbs to basic verb from, so that token.headword can match them
    base_form_word = word_stem + base_form_word_ending
    for pos in possible_parts_of_speech:
        if pos.startswith("v"):
            word_type = "verb"
            break
        if pos == "adj-i":
            word_type = "i_adjective"
            break
    logger.debug(
        f"Determined word_type: '{word_type}' for base_form_word: '{base_form_word}',"
        f" possible_parts_of_speech: {possible_parts_of_speech}"
    )

    # Convert text to hiragana with regex, store the matched indexes to later convert back
    katakana_indexes: list[tuple[int, int]] = []

    def replace_katakana(match: re.Match) -> str:
        start, end = match.span()
        katakana_indexes.append((start, end))
        return to_hiragana(match.group(0))

    hiragana_text = re.sub(r"[ァ-ン]+", replace_katakana, text)

    def increment_katakana_indexes(after_index, offset: int) -> None:
        """Helpter to increment katakana indexes after text modifications, e.g. adding tags."""
        for i in range(len(katakana_indexes)):
            start, end = katakana_indexes[i]
            if start >= after_index:
                katakana_indexes[i] = (start + offset, end + offset)

    # Also, store indexes of all whitespace as mecab wipes them out
    space_indexes: dict[int, str] = {}
    for match in re.finditer(r"\s+", hiragana_text):
        start, end = match.span()
        space_indexes[start] = match.group(0)

    def increment_space_indexes(after_index, offset: int) -> None:
        """Helper to increment space indexes after text modifications, e.g. adding tags."""
        new_space_indexes = {}
        for index, space_str in space_indexes.items():
            if index >= after_index:
                new_space_indexes[index + offset] = space_str
            else:
                new_space_indexes[index] = space_str
        space_indexes.clear()
        space_indexes.update(new_space_indexes)

    logger.debug(
        f"Converted text to hiragana: '{hiragana_text}', katakana_indexes: {katakana_indexes}"
    )

    all_tokens: list[MecabParsedToken] = list(mecab.translate(hiragana_text))
    result = ""

    found_word = False
    opened_bold = False
    text_char_idx = 0
    for token in all_tokens:
        logger.debug(
            f"Processing token: {token.word}, headword: {token.headword}, POS:"
            f" {token.part_of_speech}, Inflection: {token.inflection_type}, found_word:"
            f" {found_word}, opened_bold: {opened_bold}"
        )
        if found_word:
            add_to_conjugated_okuri, _ = get_all_conjugation_conditions(
                token,
                all_tokens,
                word_type,
            )
            if add_to_conjugated_okuri:
                logger.debug(f"Continuing highlight for conjugated okuri: {token.word}")
                result += token.word
                text_char_idx += len(token.word)
            else:
                logger.debug(f"Ending highlight for conjugated okuri: {token.word}")
                result += "</b>" + token.word
                increment_katakana_indexes(text_char_idx, 4)
                increment_space_indexes(text_char_idx, 4)
                text_char_idx += len(token.word) + 4
                opened_bold = False
                found_word = False
        elif (
            token.headword == base_form_word and get_word_type_from_mecab_token(token) == word_type
        ) or token.headword == word_stem:
            logger.debug(f"Found beginning of word to highlight: {token.word}")
            found_word = True
            result += "<b>" + token.word
            increment_katakana_indexes(text_char_idx, 3)
            increment_space_indexes(text_char_idx, 3)
            text_char_idx += len(token.word) + 3
            opened_bold = True
        else:
            logger.debug(f"Not highlighting token: {token.word}")
            result += token.word
            text_char_idx += len(token.word)
            found_word = False
            if opened_bold:
                logger.debug("Closing previously opened bold tag")
                result += "</b>"
                increment_katakana_indexes(text_char_idx, 4)
                increment_space_indexes(text_char_idx, 4)
                text_char_idx += 4
                opened_bold = False

    if opened_bold:
        logger.debug("Closing bold tag at end of text")
        result += "</b>"
        increment_katakana_indexes(text_char_idx, 4)

    logger.debug(f"Final highlighted result before restoring katakana/spaces: '{result}'")
    # Restore spaces in the result string first as the katakana restoration uses indexes created
    # before spaces were removed
    for index in sorted(space_indexes.keys()):
        space_str = space_indexes[index]
        result = result[:index] + space_str + result[index:]
    logger.debug(f"Restored spaces result: '{result}'")
    # Restore katakana in the result string with to_hiragana
    for start, end in katakana_indexes:
        result = result[:start] + to_katakana(result[start:end]) + result[end:]
    logger.debug(f"Restored katakana result: '{result}'")

    return result
