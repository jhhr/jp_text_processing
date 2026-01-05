import re
import sys

try:
    from use_text_part_storage import (
        use_text_part_storage,
        IndexIncrementer,
        TextPartIndexes,
        TextPartRestorer,
    )
except ImportError:
    from .use_text_part_storage import (
        use_text_part_storage,
        IndexIncrementer,
        TextPartIndexes,
        TextPartRestorer,
    )
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger


def increment_for_b_tag_insertion(
    increment_tag_indexes: IndexIncrementer,
    b_open_index: int,
    b_close_index: int,
) -> None:
    """
    Helper function to increment offset indexes for <b> tag insertion. For use in, e.g.
    re.sub replacement.

    Args:
        increment_tag_indexes: index incrementer from use_text_part_storage
        b_open_index: The index where the <b> tag is to be inserted in current text.
        b_close_index: The index where the </b> tag is to be inserted in current text *without*
            taking into account the length of the previously inserted <b> tag.
    """
    if b_open_index > b_close_index:
        raise ValueError("b_open_index must be less than or equal to b_close_index")
    # We make two separete calls to increment_tag_indexes as some tags need to incremented by only 3
    # and the rest for a total of 7 (4 for closing tag + 3 for opening tag).

    # Increment for tags inside (but not on exact same position) or after the opening tag
    increment_tag_indexes(b_open_index, 3, strict=True)
    # Increment for tags inside (including at exact same position) or after the closing tag
    # The offset is 4 because the first call will have already incremented by 3
    increment_tag_indexes(b_close_index + 3, 4)


def apply_tag_fixes(restored_text: str) -> str:
    """
    Apply fixes for issues that are hard to otherwise handle with changing how to increment
    indexes when restoring tags.

    Args:
        restored_text: The text after restoring tags.
    Returns:
        The text after applying fixes.
    """
    result = restored_text
    # An opening tag before opening <b>, but it's closing tag is before the b closing tag
    result = re.sub(r"(<([^>]+)>)(<b>)([^<]*</\2>)", r"\3\1\4", result)
    # An opening tag before closing </b>, but it's closing tag is after the </b>
    result = re.sub(r"(<([^>]+)>[^<]*)(</b>)(<\/\2>)", r"\1\4\3", result)
    return result


def use_tag_cleaning_with_b_insertion(
    text: str,
    logger: Logger = Logger("error"),
) -> tuple[str, IndexIncrementer, TextPartRestorer, TextPartIndexes]:
    """
    Stores indexes of all HTML tags and removes them temporarily, to
    be restored later. Also provides helper to increment indexes for <b> tag insertions.

    Args:
        text: The original text containing parts to be stored.
        logger: Logger instance for logging debug and error messages.
    Returns:
        A tuple containing:
            - The cleaned text with parts removed.
            - A function to increment indexes after modifications.
            - A function to restore the stored parts back into the text.
            - The indexes of the stored tags.
    """
    cleaned_text, increment_indexes, restore_parts, indexes = use_text_part_storage(
        text, part_regex=r"<\/?[^>]+>", logger=logger
    )

    def custom_incrementer(
        b_open_index: int,
        b_close_index: int,
    ) -> None:
        increment_for_b_tag_insertion(
            increment_indexes,
            b_open_index,
            b_close_index,
        )

    def custom_restorer(edited_text: str) -> str:
        result = restore_parts(edited_text)
        logger.debug(f"Text before applying tag fixes: '{result}'")
        result = apply_tag_fixes(result)
        logger.debug(f"Text after applying tag fixes: '{result}'")
        return result

    return cleaned_text, custom_incrementer, custom_restorer, indexes


def run_tests():
    unfixed_text = "<k><b> 何[なん]</k>でも<k> 無[な]い</b></k>"
    fixed_text = apply_tag_fixes(unfixed_text)
    try:
        assert fixed_text == "<b><k> 何[なん]</k>でも<k> 無[な]い</k></b>"
    except AssertionError:
        print("Test failed for apply_tag_fixes")
        print(f"\033[93mExpected: '{fixed_text}'\033[0m")
        print(f"\033[92mGot:      '{unfixed_text}'\033[0m")
        sys.exit(1)
    print("\n\033[92mTests passed\033[0m")


if __name__ == "__main__":
    run_tests()
