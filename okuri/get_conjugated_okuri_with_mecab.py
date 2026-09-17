import logging

from .mecab_common import (
    OkuriPrefix,
    get_all_conjugation_conditions,
    get_word_type_from_mecab_token,
    mecab,
)
from ..all_types.main_types import (
    OkuriResults,
    OkuriType,
)
from ..utils.logger import package_logger as logger

from ..mecab_controller.basic_types import (
    MecabParsedToken,
)


def get_conjugated_okuri_with_mecab(
    word: str,
    reading: str,
    maybe_okuri: str,
    okuri_prefix: OkuriPrefix = "word",
    strict_inflection: bool = False,
) -> tuple[OkuriResults, bool]:
    """
    Determines the portion of text that is the conjugated okurigana for a kanji reading.
    :param word: The kanji or word
    :param maybe_okuri: The okurigana to check
    :param reading: The reading of the kanji or word occurring before the okurigana
    :param okuri_prefix: Whether the maybe_okuri is attached to the "word" (kanji) or "reading" (kana) portion
    :param strict_inflection: Whether to enforce strict inflection rules
    :return: A tuple of the okurigana that is part of the conjugation for threading
            and the rest of the okurigana, along with a boolean indicating if it is a suru verb
    """
    logger.debug(
        "get_conjugated_okuri - maybe_okuri: %s, word: %s, reading: %s, okuri_prefix: %s,"
        " strict_inflection: %s",
        maybe_okuri,
        word,
        reading,
        okuri_prefix,
        strict_inflection,
    )
    if not maybe_okuri:
        logger.debug("get_conjugated_okuri - No okurigana provided, no processing needed.")
        return OkuriResults("", "", "no_okuri", None), False
    parse_text_prefix = None
    if okuri_prefix == "word":
        if word:
            # Exception for 為 as its headword doesn't get detected correctly so process it using
            # the kanji reading
            if (word == "為" and reading == "し") or word == "抉":
                parse_text_prefix = reading
                okuri_prefix = "reading"
            else:
                parse_text_prefix = word
        elif reading:
            parse_text_prefix = reading
            okuri_prefix = "reading"
    elif okuri_prefix == "reading":
        if reading:
            parse_text_prefix = reading
        elif word:
            parse_text_prefix = word
            okuri_prefix = "word"
    if not parse_text_prefix:
        logger.error(
            "get_conjugated_okuri - cannot set parse_text_prefix, okuri_prefix: '%s', word: '%s',"
            " reading: '%s'",
            okuri_prefix,
            word,
            reading,
        )
        return OkuriResults("", maybe_okuri, "no_okuri", None), False
    text_to_parse = f"{parse_text_prefix}{maybe_okuri}"

    okuri_type: OkuriType = "detected_okuri"
    is_suru_verb = False

    # exceptions that parsing gets wrong
    if word == "久" and reading == "ひさ" and maybe_okuri.startswith("しぶり"):
        return OkuriResults("し", maybe_okuri[1:], okuri_type, "adj-i"), is_suru_verb
    if word == "仄々" and reading == "ほのぼの":
        if maybe_okuri.startswith("した"):
            rest_kana = maybe_okuri[2:]
            return OkuriResults("した", rest_kana, okuri_type, None), is_suru_verb
        if maybe_okuri.startswith("しい"):
            rest_kana = maybe_okuri[2:]
            return OkuriResults("しい", rest_kana, okuri_type, "adj-i"), is_suru_verb
        if maybe_okuri.startswith("し"):
            rest_kana = maybe_okuri[1:]
            return OkuriResults("し", rest_kana, okuri_type, "adj-i"), is_suru_verb

    tokens: list[MecabParsedToken] = list(mecab.translate(text_to_parse))
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Parsed text: %s ->\n%s",
            text_to_parse,
            "\n".join(f"{token.word}, PartOfSpeech: {token.part_of_speech}" for token in tokens),
        )
    if not tokens:
        logger.debug(
            "get_conjugated_okuri - No tokens found for text: %s, returning no okuri.",
            text_to_parse,
        )
        return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
    first_token = tokens[0]
    if not first_token.part_of_speech:
        logger.error("get_conjugated_okuri - No PartOfSpeech found for %s", text_to_parse)
        return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb

    word_type = get_word_type_from_mecab_token(first_token)
    logger.debug(
        "First token: %s,  PartOfSpeech: %s, first_token word_type: %s",
        first_token.word,
        first_token.part_of_speech,
        word_type,
    )
    if not word_type:
        # If the first token is not one of the processable types, try again with kanji_reading
        # as the prefix
        if okuri_prefix == "word":
            logger.debug(
                "First token not valid: %s, PartOfSpeech: %s, Retrying with reading as prefix.",
                first_token.word,
                first_token.part_of_speech,
            )
            if reading:
                return get_conjugated_okuri_with_mecab(
                    word,
                    reading,
                    maybe_okuri,
                    okuri_prefix="reading",
                    strict_inflection=strict_inflection,
                )
            else:
                logger.debug("No reading available to retry with, returning no okuri.")
                return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
        elif okuri_prefix == "reading":
            logger.debug(
                "First token is not a verb or adjective: %s, PartOfSpeech: %s, Returning empty"
                " okuri.",
                first_token.word,
                first_token.part_of_speech,
            )
            return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
        else:
            logger.error("Unknown okuri_prefix: %s. Expected 'word' or 'reading'.", okuri_prefix)
            return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
    # The first token will actually include the conjugation stem, so we need to extract it
    conjugated_okuri = first_token.word[len(parse_text_prefix) :]
    # Exception for nouns like 恥ずかしげな where the げ should be considered not a conjugation
    # as it is in fact 恥ずかし気な
    if word_type == "noun" and first_token.word.endswith("げ"):
        conjugated_okuri = first_token.word[len(parse_text_prefix) : -1]
        okuri_type = "full_okuri"
        logger.debug(
            "Detected okuri for noun: %s, rest: %s",
            conjugated_okuri,
            maybe_okuri[len(conjugated_okuri):],
        )
        return (
            OkuriResults(conjugated_okuri, maybe_okuri[len(conjugated_okuri) :], okuri_type, None),
            is_suru_verb,
        )
    rest_kana = maybe_okuri[len(conjugated_okuri) :]
    logger.debug(
        "Initial conjugated okuri: %s, rest_kana: %s, first token: %s, PartOfSpeech: %s",
        conjugated_okuri,
        rest_kana,
        first_token.word,
        first_token.part_of_speech,
    )
    rest_tokens = tokens[1:]
    added_conjugation_token = False
    for token in rest_tokens:
        add_to_conjugated_okuri, was_suru_verb = get_all_conjugation_conditions(
            token,
            rest_tokens,
            word_type,
        )
        if add_to_conjugated_okuri:
            added_conjugation_token = True
            conjugated_okuri += token.word
            # Remove the text from the rest of the okurigana
            rest_kana = rest_kana[len(token.word) :]
            logger.debug(
                "Added to okuri: %s, headword: %s, POS: %s, new okuri: %s, rest_kana: %s",
                token.word,
                token.headword,
                token.part_of_speech,
                conjugated_okuri,
                rest_kana,
            )
            if was_suru_verb:
                is_suru_verb = True
        else:
            # If we hit a non-auxiliary token, stop processing
            logger.debug(
                "Stopping at non-auxiliary token: %s, PartOfSpeech: %s,",
                token.word,
                token.part_of_speech,
            )
            break

    # In strict mode, avoid treating lexical noun/adverb suffixes as okurigana when there is
    # no actual conjugation evidence (e.g., 餡こ should not tag こ as <oku>). Keep suru-verb
    # chains and other token-based conjugations intact.
    if (
        strict_inflection
        and word_type in ["noun", "adverb"]
        and conjugated_okuri
        and not added_conjugation_token
        and not is_suru_verb
    ):
        logger.debug(
            "get_conjugated_okuri - strict_inflection: rejecting noun/adverb lexical suffix as"
            " okuri, conjugated_okuri: %s, maybe_okuri: %s, token: %s",
            conjugated_okuri,
            maybe_okuri,
            first_token.word,
        )
        return OkuriResults("", maybe_okuri, "rejected_lexical_suffix", None), is_suru_verb

    return OkuriResults(conjugated_okuri, rest_kana, "detected_okuri", None), is_suru_verb
