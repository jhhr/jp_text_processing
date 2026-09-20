from typing import Optional

from ..all_types.main_types import PartOfSpeech
from ..mecab_controller.basic_types import MecabParsedToken
from ..okuri.mecab_common import (
    get_all_conjugation_conditions,
    get_word_type_from_mecab_token,
    mecab,
    MecabWordType,
)
from ..mecab_controller.kana_conv import (
    to_hiragana,
    to_katakana,
    is_hiragana_str,
    is_katakana_str,
)
from .use_text_part_storage import use_text_part_storage

from .use_tag_cleaning import use_tag_cleaning_with_b_insertion, increment_for_b_tag_insertion
from ..okuri.get_conjugatable_okurigana_stem import CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH
from ..okuri.okurigana_dict import (
    GODAN_FORM_VERB_STARTINGS,
    POSSIBLE_OKURIGANA_PROGRESSION_DICT,
)
from ..utils.logger import package_logger as logger


def highlight_inflected_words_with_mecab(text: str, base_form_word: str, depth: int = 0) -> str:
    """
    Find inflected words in the given text using MeCab.
    :param text: The text to analyze.
    :return: String with <b> tags around each inflected occurrence of the base form word
    """
    if not text or not base_form_word:
        return text
    if depth >= 2:
        logger.debug(
            "Maximum recursion depth reached (%s) for text: '%s', base_form_word: '%s'",
            depth,
            text,
            base_form_word,
        )
        return text

    # Determine the word type from the base form word
    word_type: Optional[MecabWordType] = None
    base_form_word_ending = to_hiragana(base_form_word[-1])
    possible_parts_of_speech: list[PartOfSpeech] = []
    # Check if the last character is in the conjugatable okuri list
    if base_form_word_ending in CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH:
        possible_parts_of_speech = CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH[base_form_word_ending]
    elif base_form_word_ending in GODAN_FORM_VERB_STARTINGS:
        # Or, if it's a godan verb in noun form, convert to dictionary form
        base_form_word_ending = GODAN_FORM_VERB_STARTINGS[base_form_word_ending]
        possible_parts_of_speech = CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH.get(
            base_form_word_ending, []
        )

    word_stem = base_form_word[:-1]
    if not word_stem:
        # A one-character word has no stem to inflect and the verbatim search already failed
        return text
    # Set noun form verbs to basic verb from, so that token.headword can match them
    if is_katakana_str(word_stem):
        base_form_word_ending = to_katakana(base_form_word_ending)
    base_form_word = word_stem + base_form_word_ending
    for pos in possible_parts_of_speech:
        if pos.startswith("v"):
            word_type = "verb"
            break
        if pos == "adj-i":
            word_type = "i_adjective"
            break
    logger.debug(
        "Determined word_type: '%s' for base_form_word: '%s', possible_parts_of_speech: %s",
        word_type,
        base_form_word,
        possible_parts_of_speech,
    )

    def inflected_stem_okurigana_len(tokens: list[MecabParsedToken], index: int) -> int:
        """
        Length of the conjugation following a token spelling the word's stem, 0 if it has none.

        MeCab does not know every verb; for an unknown one it splits the word into a noun-ish
        stem plus the conjugation, so the stem token's headword is the word's stem. The stem
        alone is no evidence though - はし is the noun 橋 as much as it is the stem of はしる -
        so require that the text following the token continues as one of the conjugations
        possible for this word. The longest such conjugation is the one the word actually got,
        and it is also how far the highlight has to reach: MeCab mis-parsed the word, so its
        tokens cannot be asked where the conjugation ends.
        """
        if tokens[index].headword != word_stem:
            return 0
        following_text = "".join(t.word for t in tokens[index + 1 :])
        okurigana_len = 0
        for pos in possible_parts_of_speech:
            progression = POSSIBLE_OKURIGANA_PROGRESSION_DICT.get(pos)
            for char_index, char in enumerate(following_text):
                progression = progression.get(char) if progression else None
                if not progression:
                    break
                if progression.get("is_last"):
                    okurigana_len = max(okurigana_len, char_index + 1)
        return okurigana_len

    # Store indexes of all whitespace as mecab wipes them out
    space_free_text, increment_space_indexes, restore_spaces, _ = use_text_part_storage(
        text, part_regex=r"\s+"
    )

    # Clean html tags from the text temporarily
    html_and_space_free_text, increment_tag_indexes, restore_tags, _ = (
        use_tag_cleaning_with_b_insertion(space_free_text)
    )

    def increment_indexes_for_b(start: int, end: int) -> None:
        increment_for_b_tag_insertion(increment_space_indexes, start, end)
        increment_tag_indexes(start, end)

    all_tokens: list[MecabParsedToken] = list(mecab.translate(html_and_space_free_text))
    result = ""

    found_word = False
    opened_bold = False
    text_char_idx = 0
    open_bold_idx = -1
    # Okurigana of a stem match still waiting to be covered by the highlight, in characters
    stem_okuri_remaining = 0
    for token_idx, token in enumerate(all_tokens):
        logger.debug("token.word: '%s', cur result: \033[32m'%s'\033[0m", token.word, result)
        if found_word:
            # How many characters at the start of this token still belong inside the highlight.
            # Only a stem match has any: it is the one case where the highlight's end is known
            # up front rather than token by token.
            highlighted_chars = 0
            if stem_okuri_remaining > 0:
                # The word was found by its stem, which means MeCab mis-parsed it - the
                # conjugation conditions read its tokens as if they were their own words
                # (バズった gives っ the headword く) and would end the highlight on the first of
                # them. Follow the okurigana matched on the stem instead, and since those
                # tokens are not the word's, let the highlight end inside one of them
                # (バズ/っ/てる, where the conjugation って ends mid-てる).
                highlighted_chars = min(len(token.word), stem_okuri_remaining)
                stem_okuri_remaining -= highlighted_chars
                add_to_conjugated_okuri = highlighted_chars == len(token.word)
            else:
                add_to_conjugated_okuri, _ = get_all_conjugation_conditions(
                    token,
                    all_tokens,
                    word_type,
                )
            if add_to_conjugated_okuri:
                logger.debug("Continuing highlight for conjugated okuri: %s", token.word)
                result += token.word
                text_char_idx += len(token.word)
            else:
                logger.debug("Ending highlight for conjugated okuri: %s", token.word)
                result += token.word[:highlighted_chars] + "</b>" + token.word[highlighted_chars:]
                # We need to subtract the length of the opening tag because the text_char_idx
                # is counting text including it
                before_b_close_idx = text_char_idx + highlighted_chars - 3
                text_char_idx += len(token.word) + 4
                logger.debug(
                    "open_bold_idx: %s, before_b_close_idx: %s", open_bold_idx, before_b_close_idx
                )
                increment_indexes_for_b(open_bold_idx, before_b_close_idx)
                opened_bold = False
                found_word = False
        elif (
            stem_okuri_remaining := inflected_stem_okurigana_len(all_tokens, token_idx)
        ) or (
            token.headword == base_form_word and get_word_type_from_mecab_token(token) == word_type
        ):
            logger.debug("Found beginning of word to highlight: %s", token.word)
            found_word = True
            result += "<b>" + token.word
            open_bold_idx = text_char_idx
            text_char_idx += len(token.word) + 3
            opened_bold = True
        else:
            logger.debug("Not highlighting token: %s", token.word)
            result += token.word
            text_char_idx += len(token.word)
            found_word = False
            # This is just safe-keeping in case of some logic error, we shouldn't really get here
            if opened_bold:
                logger.debug("Closing previously opened bold tag")
                result += "</b>"
                before_b_close_idx = text_char_idx - 3
                text_char_idx += 4
                logger.debug(
                    "open_bold_idx: %s, before_b_close_idx: %s", open_bold_idx, before_b_close_idx
                )
                increment_indexes_for_b(open_bold_idx, before_b_close_idx)
                opened_bold = False

    if opened_bold:
        logger.debug("Closing bold tag at end of text")
        result += "</b>"
        text_char_idx += 4

    if "<b>" not in result:
        # Try again with word converted to hiragana/katakana
        logger.debug(
            "No highlights found, retrying with base_form_word converted to hiragana/katakana."
        )
        if is_hiragana_str(base_form_word):
            return highlight_inflected_words_with_mecab(
                text, to_katakana(base_form_word), depth + 1
            )
        elif is_katakana_str(base_form_word):
            return highlight_inflected_words_with_mecab(
                text, to_hiragana(base_form_word), depth + 1
            )
        else:
            # Mixed kana, convert to hiragana, the next recursion will convert to katakana
            return highlight_inflected_words_with_mecab(text, to_hiragana(base_form_word), 0)
    logger.debug("Final highlighted result before restoring tags/spaces: '%s'", result)

    # Restore removed parts in reverse order
    # First tags
    result = restore_tags(result)
    logger.debug("Restored html tags result: '%s'", result)

    # Then spaces
    result = restore_spaces(result)
    logger.debug("Restored spaces result: '%s'", result)

    # Make some fixes to spaces
    result = result.replace("</b >", "</b> ")

    return result
