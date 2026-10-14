from __future__ import annotations

import logging
from collections.abc import Sequence

from ..all_types.main_types import (
    OkuriResults,
    OkuriType,
)
from ..mecab_controller.basic_types import (
    MecabParsedToken,
)
from ..utils.logger import package_logger as logger
from .mecab_common import (
    OkuriPrefix,
    get_all_conjugation_conditions,
    get_word_type_from_mecab_token,
    mecab,
)


def find_stem_token(
    tokens: Sequence[MecabParsedToken], text: str, prefix_length: int
) -> tuple[int, str] | None:
    """
    The token the okurigana is read from, as `(index, part)`: the token the prefix ends in, and
    the part of it that lies past the prefix. `None` when the tokens do not spell `text` that
    far, which is mecab having dropped or rewritten something it was given.

    Mecab gets the prefix and the kana after it as one text and cuts that where it sees words.
    A word it knows comes back as one token running on into its inflection (食べ of 食べた), and
    that token is the stem. A word it does not know can come back in pieces, every one of them
    still the word: 來賓 is no word to it, and neither is らいひん, which it reads as the noun
    らい and the Kansai negative ひん. Only the piece the prefix ends in can carry okurigana, and
    the pieces before it are skipped. Taking the first token for the stem whatever its length
    made ひん the okurigana of らい, and 來賓[らいひん]には was written back as 來賓[らいひん]ひん.
    """
    spelled = ""
    for index, token in enumerate(tokens):
        spelled += token.word
        if not text.startswith(spelled):
            return None
        if len(spelled) >= prefix_length:
            return index, spelled[prefix_length:]
    return None


def get_conjugated_okuri_with_mecab(
    word: str,
    reading: str,
    maybe_okuri: str,
    okuri_prefix: OkuriPrefix = "word",
    strict_inflection: bool = False,
) -> tuple[OkuriResults, bool]:
    """
    Determines the portion of text that is the conjugated okurigana for a kanji reading.

    Whatever is found, the okurigana is the start of `maybe_okuri` and the rest is what remains
    of it: `okurigana + rest_kana == maybe_okuri`. The callers write both back out, so anything
    else would change the text.

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
    stem = find_stem_token(tokens, text_to_parse, len(parse_text_prefix))
    if stem is None:
        logger.debug(
            "get_conjugated_okuri - The tokens do not spell %s as far as its prefix %s,"
            " returning no okuri.",
            text_to_parse,
            parse_text_prefix,
        )
        return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
    stem_index, conjugated_okuri = stem
    stem_token = tokens[stem_index]
    if not stem_token.part_of_speech:
        logger.error("get_conjugated_okuri - No PartOfSpeech found for %s", text_to_parse)
        return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb

    word_type = get_word_type_from_mecab_token(stem_token)
    # A token that begins part-way through the prefix and runs on past its end is not the word
    # that was asked about, it only ends in the same place. A verb there still shows where the
    # ending is, because what a verb token holds after the kanji is its inflection: づい of
    # 躓[つまづ]いて, which mecab cuts つま|づい|て, or きまっ of に決[にき]まって. Nothing else
    # does. 分の in 五分の and 人たち in 老人たち are nouns that begin on the word's last kanji,
    # and their tails would pass for a lexical suffix of 五分 and 老人, which turns an onyomi
    # into a kunyomi; おも in 猫[まお]も is an adjective's bare stem, with no ending in it.
    if stem_index > 0 and conjugated_okuri and word_type != "verb":
        word_type = None
    logger.debug(
        "Stem token: %s,  PartOfSpeech: %s, word_type: %s",
        stem_token.word,
        stem_token.part_of_speech,
        word_type,
    )
    if not word_type:
        # If the stem token is not one of the processable types, try again with kanji_reading
        # as the prefix
        if okuri_prefix == "word":
            logger.debug(
                "Stem token not valid: %s, PartOfSpeech: %s, Retrying with reading as prefix.",
                stem_token.word,
                stem_token.part_of_speech,
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
                "Stem token is not a verb or adjective: %s, PartOfSpeech: %s, Returning empty"
                " okuri.",
                stem_token.word,
                stem_token.part_of_speech,
            )
            return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
        else:
            logger.error("Unknown okuri_prefix: %s. Expected 'word' or 'reading'.", okuri_prefix)
            return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
    # The stem token runs on past the prefix into the conjugation stem, and that part of it is
    # the okurigana so far.
    # Exception for nouns like 恥ずかしげな where the げ should be considered not a conjugation
    # as it is in fact 恥ずかし気な
    if word_type == "noun" and stem_token.word.endswith("げ"):
        conjugated_okuri = conjugated_okuri[:-1]
        okuri_type = "full_okuri"
        logger.debug(
            "Detected okuri for noun: %s, rest: %s",
            conjugated_okuri,
            maybe_okuri[len(conjugated_okuri) :],
        )
        return (
            OkuriResults(conjugated_okuri, maybe_okuri[len(conjugated_okuri) :], okuri_type, None),
            is_suru_verb,
        )
    rest_kana = maybe_okuri[len(conjugated_okuri) :]
    logger.debug(
        "Initial conjugated okuri: %s, rest_kana: %s, stem token: %s, PartOfSpeech: %s",
        conjugated_okuri,
        rest_kana,
        stem_token.word,
        stem_token.part_of_speech,
    )
    rest_tokens = tokens[stem_index + 1 :]
    added_conjugation_token = False
    for token in rest_tokens:
        add_to_conjugated_okuri, was_suru_verb = get_all_conjugation_conditions(
            token,
            rest_tokens,
            word_type,
        )
        # Mecab is not given markup and hands back no spaces, so a token is not always what
        # the text goes on with. One that is not ends the okurigana, like a token that does
        # not conjugate.
        if add_to_conjugated_okuri and rest_kana.startswith(token.word):
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
            stem_token.word,
        )
        return OkuriResults("", maybe_okuri, "rejected_lexical_suffix", None), is_suru_verb

    return OkuriResults(conjugated_okuri, rest_kana, "detected_okuri", None), is_suru_verb
