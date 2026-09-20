
from ..all_types.main_types import OkuriResults, OkuriType, PartOfSpeech
from ..okuri.okurigana_dict import get_okuri_dict_for_okurigana
from ..utils.logger import package_logger as logger


def starts_with_okurigana_conjugation(
    kana_text: str,
    kanji_okurigana: str,
    kanji: str,
    kanji_reading: str,
    part_of_speech: PartOfSpeech | None = None,
) -> OkuriResults:
    """
    Determine if a kana text starts with okurigana and return that portion and the rest of the text.
    The text should have already been trimmed of the verb or adjective stem.
    :param kana_text: text to check for okurigana.
    :param kanji_okurigana: okurigana of the kanji.
    :param kanji: kanji whose okurigana is being checked in kana_text.
    :param kanji_reading: reading of the kanji.
    :param part_of_speech: Optional override for the part of speech.
    :return: tuple of the okurigana (if any) and the rest of the text
    """
    # Sanity check, we need at least one character, and at least the kanji okurigana
    if not kana_text or not kanji_okurigana:
        return OkuriResults("", kana_text, "no_okuri", None)

    # Get the okurigana dict for the kanji
    okuri_dict, part_of_speech_for_okuri = get_okuri_dict_for_okurigana(
        kanji_okurigana,
        kanji,
        kanji_reading,
        part_of_speech=part_of_speech,
    )

    if not okuri_dict:
        return OkuriResults("", kana_text, "no_okuri", None)

    logger.debug(
        "kana_text: %s, kanji_okurigana: %s, kanji: %s, kanji_reading: %s",
        kana_text,
        kanji_okurigana,
        kanji,
        kanji_reading,
    )

    if kana_text[0] not in okuri_dict and not okuri_dict.get(""):
        logger.debug("no okurigana found and no empty string okurigana")
        return OkuriResults("", kana_text, "no_okuri", None)

    okurigana = ""
    rest = kana_text
    prev_dict = okuri_dict
    okuri_result: OkuriType = "no_okuri"
    # Recurse into the dict to find the longest okurigana
    # ending in either cur_char not being in the dict or the dict being empty
    while True:
        cur_char = rest[0]
        logger.debug(
            "okurigana: %s, rest: %s, cur_char: %s, in dict: %s",
            okurigana,
            rest,
            cur_char,
            cur_char in prev_dict,
        )
        if cur_char not in prev_dict:
            logger.debug(
                "reached dict end, empty_dict: %s, is_last: %s",
                not prev_dict,
                prev_dict.get('is_last'),
            )
            okuri_result = "full_okuri" if prev_dict.get("is_last") else "partial_okuri"
            break
        prev_dict = prev_dict[cur_char]
        okurigana += cur_char
        rest = rest[1:]
        if not rest:
            logger.debug("reached text end")
            okuri_result = "full_okuri" if prev_dict.get("is_last") else "partial_okuri"
            break
    if not okurigana and okuri_dict.get(""):
        # If no okurigana was found, but this conjugation can be valid with no okurigana,
        # then we indicate that this empty string is a full okurigana
        okuri_result = "empty_okuri"
    return OkuriResults(okurigana, rest, okuri_result, part_of_speech_for_okuri)
