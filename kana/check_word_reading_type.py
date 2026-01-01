import re
from typing import Literal

try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger

WordReadingType = Literal["on", "kun", "juk", "mix", ""]


def check_word_reading_type(
    word_with_tags: str,
    logger: Logger = Logger("error"),
) -> WordReadingType:
    """Check if the processed furigana string contains only <kun> or <on> tags.
    Args:
        word_with_tags (str): The processed furigana string with tags.
    Returns:
    """
    if not word_with_tags:
        logger.debug("Empty word_with_tags string")
        return ""
    # A reading is kunyomi if it contains only <kun> tags and no <on> or <juk> tags
    # First strip any ending hiragana/katakana and/or <oku> tags
    word_with_tags = re.sub(r"(?:<oku>[ぁ-んァ-ン]+</oku>)?(?:[ぁ-んァ-ン]+)?$", "", word_with_tags)
    logger.debug(f"Stripped word_with_tags: {word_with_tags}")
    # Then if all remaining tags are <kun>, it's a kunyomi reading
    tags = re.findall(r"<(kun|on|juk)>", word_with_tags)
    if tags:
        # count tags
        unique_tags = set(tags)
        if unique_tags == {"kun"}:
            return "kun"
        elif unique_tags == {"on"}:
            return "on"
        elif unique_tags == {"juk"}:
            return "juk"
        elif len(unique_tags) > 1:
            # If there's more than one type of tag, it's a mixed reading
            return "mix"
    # Indicate that there's no tags with an empty string
    return ""
