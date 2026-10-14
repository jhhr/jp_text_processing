import re

from ..regex.kanji_furi import KANJI_RANGES
from ..utils.logger import package_logger as logger
from .kana_highlight import WithTagsDef, kana_highlight

KANJI_RE = rf"[\d々{KANJI_RANGES}]"


def make_furigana_from_reading(word: str, reading: str) -> str:
    """Generate furigana for a given word based on its reading.

    Args:
        word (str): The kanji word.
        reading (str): The full reading of the word in kana.

    Returns:
        str: The word in furigana syntax, without tags. Each kanji run gets its own part of the
        reading where the reading can be split over the word, else the whole word gets the whole
        reading: ` 泣き明かし[なきかし]`. A word without kanji comes back as it is.
    """
    # If word doesn't contain kanji, return the word as is
    if re.search(KANJI_RE, word) is None:
        return word
    added_word_with_furigana = f"{word}[{reading}]"
    logger.debug("Added word with furigana: %s", added_word_with_furigana)
    furigana = kana_highlight(
        kanji_to_highlight="",
        text=added_word_with_furigana,
        return_type="furigana",
        with_tags_def=WithTagsDef(
            with_tags=False,
            merge_consecutive=True,
            onyomi_to_katakana=False,
            include_suru_okuri=True,
        ),
    )
    if furigana == added_word_with_furigana:
        # Nothing in it could be split, so the reading stays over the whole word, kana and all.
        # The space is what marks where the word starts, as a split result has one before each
        # kanji run: without it Anki's furigana filter takes in whatever text comes before the
        # word, and あの泣き明かし[なきかし] puts the reading over あの as well.
        logger.debug("Reading could not be split over the word: %s", furigana)
        return f" {furigana}"
    return furigana
