import re
from typing import Callable

from ..utils.logger import Logger

SplitterIndexes = list[tuple[int, int, str]]
OffsetIndexes = list[tuple[int, int]]
SplitterIndexIncrementer = Callable[[int, int], None]
SplitterRestorer = Callable[[str], str]
SplitFreeToOriginalIndex = Callable[[int], int]

SPLITTER_DOT_RE = r"・\s*"


def use_splitter_dot_cleaning_with_b_insertion(
    text: str,
    splitter_regex: str = SPLITTER_DOT_RE,
    logger: Logger = Logger("error"),
) -> tuple[
    str,
    SplitterIndexIncrementer,
    SplitterRestorer,
    SplitterIndexes,
    SplitFreeToOriginalIndex,
]:
    """Remove splitter dots (・) temporarily and provide restoration/index helpers.

    The helpers mirror the behavior of tag cleaning so b-tag insertion can be coordinated
    across both cleaned representations.
    """

    splitter_indexes: SplitterIndexes = []
    base_splitter_indexes: SplitterIndexes = []
    offset_indexes: OffsetIndexes = []

    cleaned_text = ""
    last_index = 0
    for match in re.finditer(splitter_regex, text):
        start, end = match.span()
        cleaned_text += text[last_index:start]
        part = match.group(0)
        splitter_indexes.append((start, end, part))
        base_splitter_indexes.append((start, end, part))
        last_index = end
    cleaned_text += text[last_index:]
    logger.debug(f"Text after splitter removal: '{cleaned_text}'")
    logger.debug(f"Splitter regex used: '{splitter_regex}'")
    logger.debug(f"Splitter indexes: {splitter_indexes}")

    def split_free_to_original_index(split_free_index: int) -> int:
        """Convert an index in splitter-free text to current original coordinates."""
        parts_offset = 0
        for start, end, _ in base_splitter_indexes:
            if start <= split_free_index + parts_offset:
                parts_offset += end - start
            else:
                break

        offsets_offset = 0
        for index, offset in offset_indexes:
            if index <= split_free_index:
                offsets_offset += offset
            else:
                break

        return split_free_index + parts_offset - offsets_offset

    def increment_splitter_indexes_for_b_insertion(b_open_index: int, b_close_index: int) -> None:
        if b_open_index > b_close_index:
            raise ValueError("b_open_index must be less than or equal to b_close_index")

        open_original = split_free_to_original_index(b_open_index)
        close_original = split_free_to_original_index(b_close_index)

        for i in range(len(splitter_indexes)):
            start, end, part = splitter_indexes[i]
            if start >= open_original:
                splitter_indexes[i] = (start + 3, end + 3, part)

        # Closing tag insertion happens after the opening tag has already shifted text by 3.
        close_boundary_after_open = close_original + 3
        for i in range(len(splitter_indexes)):
            start, end, part = splitter_indexes[i]
            if start >= close_boundary_after_open:
                splitter_indexes[i] = (start + 4, end + 4, part)

        offset_indexes.append((b_open_index, 3))
        offset_indexes.append((b_close_index + 3, 4))

    def restore_splitters(edited_text: str) -> str:
        for start, end, splitter_str in splitter_indexes:
            edited_text = edited_text[:start] + splitter_str + edited_text[start:]
        return edited_text

    return (
        cleaned_text,
        increment_splitter_indexes_for_b_insertion,
        restore_splitters,
        splitter_indexes,
        split_free_to_original_index,
    )
