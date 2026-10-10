"""
The word `word_highlight` is asked for, brought into the furigana syntax its searches read.

The searches take the word to be a dictionary form in ordinary furigana syntax and nothing
else: a reading in brackets after each kanji run, the kana outside the brackets. A word that
comes from a note's field is not always that, and a search that is handed something else finds
nothing. `normalize_word` rewrites the shapes that can be told apart from an ordinary word with
confidence and gives every other word back as the very string it was given, which is what
happens to nearly all of them.

What is not the word is taken off it: the whitespace after it (a non-breaking space and its
entity included), html tags, and a bracket with no reading in it. The space in front of a word
is furigana syntax, marking where its kanji start, and stays.
"""

import re

from ..utils.logger import package_logger as logger
from .use_tag_cleaning import TAG_PART_RE

# A non-breaking space, as the character or as the entity an html field stores it as
NON_BREAKING_SPACE_REC = re.compile(r"&nbsp;|\u00a0")
# A bracket that holds no reading: nothing at all, or only whitespace
EMPTY_BRACKET_REC = re.compile(r"\[\s*\]")


def without_noise(word: str) -> str:
    """Take off the word what a note's field can hold besides it.

    A word that would have nothing left is given back whole: the searches are never handed an
    empty word, and one made only of noise is no word to look for either way.
    """
    cleaned = re.sub(TAG_PART_RE, "", word)
    cleaned = NON_BREAKING_SPACE_REC.sub(" ", cleaned)
    cleaned = EMPTY_BRACKET_REC.sub("", cleaned)
    cleaned = cleaned.rstrip()
    return cleaned if cleaned.strip() else word


def normalize_word(word: str) -> str:
    """Give the word back in ordinary furigana syntax, or as it was given when it already is.

    Args:
        word (str): The word as `word_highlight` was given it, neither empty nor only spaces.

    Returns:
        str: The word for the searches to take as written.
    """
    normalized = without_noise(word)
    if normalized != word:
        logger.debug("normalize_word: '%s' -> '%s'", word, normalized)
    return normalized
