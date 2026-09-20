import re
from .kana_highlight import kana_highlight, WithTagsDef

from ..regex.kanji_furi import KANJI_RANGES
from ..utils.logger import package_logger as logger

KANJI_RE = rf"[\d々{KANJI_RANGES}]"


def make_furigana_from_reading(word: str, reading: str) -> str:
    """Generate furigana for a given word based on its reading.

    Args:
        word (str): The kanji word.
        reading (str): The full reading of the word in kana.

    Returns:
        str: The furigana string with appropriate tags.
    """
    # If word doesn't contain kanji, return the word as is
    if re.search(KANJI_RE, word) is None:
        return word
    added_word_with_furigana = f"{word}[{reading}]"
    logger.debug("Added word with furigana: %s", added_word_with_furigana)
    return kana_highlight(
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
