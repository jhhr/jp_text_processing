from typing import Optional
from .get_conjugatable_okurigana_stem import get_conjugatable_okurigana_stem
from .starts_with_okurigana_conjugation import (
    OkuriResults,
    starts_with_okurigana_conjugation,
)

from ..all_types.main_types import (
    PartOfSpeech,
)
from ..utils.logger import Logger


def check_okurigana_for_inflection(
    reading_okurigana: str,
    reading: str,
    maybe_okuri: str,
    kanji_to_match: str,
    part_of_speech: Optional[PartOfSpeech] = None,
    logger: Logger = Logger("error"),
) -> OkuriResults:
    """
    Function that checks the okurigana for a match with the okurigana
    :param reading_okurigana: the okurigana to check
    :param reading: the kunyomi/onyomi reading to check against
    :param maybe_okuri: the okurigana string to check for inflections
    :param kanji_to_match: the kanji string to match against
    :param logger: the logger to use for debugging
    :param part_of_speech: optional override for the part of speech to use

    :return: (string, string) the okurigana that should be highlighted and the rest of the okurigana
    """
    # Kana text occurring after the kanji in the word, may not be okurigana and can
    # contain other kana after the okurigana
    maybe_okuri
    logger.debug(
        f"check okurigana 0 - reading_okurigana: {reading_okurigana}, maybe_okuri:"
        f" {maybe_okuri}, reading: {reading}, part_of_speech: {part_of_speech}"
    )

    if not maybe_okuri or not reading_okurigana:
        logger.debug("check okurigana 0 - no okurigana or reading_okurigana")
        # If there is no okurigana or reading_okurigana, we can't check for inflections
        return OkuriResults("", "", "no_okuri")

    # Simple case, exact match, no need to check conjugations
    if reading_okurigana == maybe_okuri:
        logger.debug("check okurigana 1 - exact match")
        return OkuriResults(reading_okurigana, "", "full_okuri", None)

    # Check what kind of inflections we should be looking for from the kunyomi okurigana
    conjugatable_stem, possible_parts_of_speech = get_conjugatable_okurigana_stem(reading_okurigana)

    # Another simple case, stem is the same as the okurigana, no need to check conjugations
    if conjugatable_stem == maybe_okuri:
        # If we wanted to accurately get the part of speech, we'd need to do the full okuri check
        if len(possible_parts_of_speech) == 1:
            detected_part_of_speech = possible_parts_of_speech[0]
        elif part_of_speech:
            detected_part_of_speech = part_of_speech
        else:
            detected_part_of_speech = None
        logger.debug("check okurigana 2 - stem matches okurigana exactly")
        return OkuriResults(conjugatable_stem, "", "full_okuri", detected_part_of_speech)

    logger.debug(
        f"check okurigana with reading_okurigana 1 - conjugatable_stem: {conjugatable_stem}"
    )
    if conjugatable_stem is None or not maybe_okuri.startswith(conjugatable_stem):
        logger.debug(
            "\ncheck okurigana with reading_okurigana 2 - no conjugatable_stem or no match"
        )
        # Not a verb or i-adjective, so just check for an exact match within the okurigana
        if maybe_okuri.startswith(reading_okurigana):
            logger.debug(
                f"check okurigana with reading_okurigana 3 - maybe_okuri_text: {maybe_okuri}"
            )
            return OkuriResults(
                reading_okurigana,
                maybe_okuri[len(reading_okurigana) :],
                "full_okuri",
            )
        logger.debug("\ncheck okurigana with reading_okurigana 4 - no match")
        return OkuriResults("", maybe_okuri, "no_okuri")

    # Remove the conjugatable_stem from maybe_okurigana
    trimmed_maybe_okuri = maybe_okuri[len(conjugatable_stem) :]
    logger.debug(f"check okurigana 5 - trimmed_maybe_okuri: {trimmed_maybe_okuri}")

    # Then check if that contains a conjugation for what we're looking for
    conjugated_okuri, rest, return_type, detected_part_of_speech = (
        starts_with_okurigana_conjugation(
            trimmed_maybe_okuri,
            reading_okurigana,
            kanji_to_match,
            reading,
            part_of_speech=part_of_speech,
            logger=logger,
        )
    )
    logger.debug(
        f"check okurigana 6 - conjugated_okuri: {conjugated_okuri}, rest: {rest},"
        f" return_type: {return_type}, detected_part_of_speech: {detected_part_of_speech}"
    )

    if return_type != "no_okuri":
        logger.debug(
            f"check okurigana 7 - result: {conjugatable_stem + conjugated_okuri}, rest: {rest}"
        )
        # remember to add the stem back!
        return OkuriResults(
            conjugatable_stem + conjugated_okuri, rest, return_type, detected_part_of_speech
        )

    # No match, this text doesn't contain okurigana for the kunyomi word
    logger.debug("\ncheck okurigana 8 - no match")
    return OkuriResults("", maybe_okuri, "no_okuri")
