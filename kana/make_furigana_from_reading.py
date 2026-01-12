import re
from .kana_highlight import kana_highlight, WithTagsDef

try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger

KANJI_RE = r"[\d々\u4e00-\u9faf\u3400-\u4dbf]"


def make_furigana_from_reading(word: str, reading: str, logger: Logger = Logger("error")) -> str:
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
    logger.debug(f"Added word with furigana: {added_word_with_furigana}")
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
