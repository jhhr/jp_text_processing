import logging
import re
from typing import Callable, Protocol

from ..utils.logger import package_logger as logger

TextPartIndexes = list[tuple[int, int, str]]
OffsetIndexes = list[tuple[int, int]]
TextPartRestorer = Callable[[str], str]


# Takes the indexes of a <b>...</b> pair being inserted, rather than one index and an offset
BTagIndexIncrementer = Callable[[int, int], None]


class IndexIncrementer(Protocol):
    """Shifts the stored parts' indexes to account for text inserted at a given index."""

    def __call__(self, after_part_free_index: int, offset: int, strict: bool = False) -> None: ...


def make_diff_string_for_indexes(
    cleaned_text: str,
    indexes: TextPartIndexes,
    offset_indexes: OffsetIndexes,
) -> str:
    """Creates a diff string showing the parts that were changed based on the given indexes.

    Args:
        cleaned_text: The cleaned text without parts.
        indexes: A list of tuples containing (start_index, end_index, part_str) for each part that
            should be reconstructed into the diff.
        offset_indexes: A list of tuples containing (index, offset) for each offset.

    Returns:
        A string showing the state of the text if reconstructed where add offsets are showing as _
        characters.
    """
    # Simulate the state of the edits made to the cleaned_text by adding _ characters for each
    # offset
    simulated_edited_text = cleaned_text
    total_offset = 0
    logger.debug("Offset indexes: %s", offset_indexes)
    for index, offset in sorted(offset_indexes, key=lambda x: x[0]):
        adjusted_index = index + total_offset
        simulated_edited_text = (
            simulated_edited_text[:adjusted_index]
            + ("_" * offset)
            + simulated_edited_text[adjusted_index:]
        )
        total_offset += offset
    logger.debug("Simulated edited text: \033[90m'%s'\033[0m", simulated_edited_text)
    # Then reconstruct the parts into the simulated edited text exactly as restore_parts
    for start, end, part_str in indexes:
        simulated_edited_text = (
            simulated_edited_text[:start] + part_str + simulated_edited_text[start:]
        )
    return simulated_edited_text


def use_text_part_storage(
    text: str, part_regex: str = r"<\/?[^>]+>"
) -> tuple[str, IndexIncrementer, TextPartRestorer, TextPartIndexes]:
    """
    Stores indexes of all parts matching the given regex and removes them temporarily, to
    be restored later.
    Args:
        text: The original text containing parts to be stored.
        part_regex: The regex pattern to identify parts to be stored. Defaults to HTML tags.
    Returns:
        A tuple containing:
            - The cleaned text with parts removed.
            - A function to increment indexes after modifications.
            - A function to restore the stored parts back into the text.
    """

    part_indexes: TextPartIndexes = []
    offset_indexes: OffsetIndexes = []
    last_index = 0

    logger.debug("Using part regex: '%s' to store text parts.", part_regex)

    cleaned_text = ""
    for match in re.finditer(part_regex, text):
        start, end = match.span()
        cleaned_text += text[last_index:start]
        part_indexes.append((start, end, match.group(0)))
        logger.debug(
            "Found part matching regex: '%s' at indexes (%s, %s)", match.group(0), start, end
        )
        last_index = end
    cleaned_text += text[last_index:]
    logger.debug("Text after removal of parts: '%s'", cleaned_text)
    logger.debug("Indexes of removed parts stored: %s", part_indexes)

    def part_free_to_original_index(part_free_index: int, strict: bool = False) -> int:
        """Convert index in text after removal to index in the text the parts are restored into.

        A part sitting exactly at the index is on one side of it or the other depending on what
        is being inserted there: the opening <b> goes after it (strict), the closing one before.
        """
        logger.debug("Converting part_free_index: %s to original index", part_free_index)
        # Calculate offset due to removed parts
        parts_offset = 0
        for start, end, _ in part_indexes:
            boundary = part_free_index + parts_offset
            if start < boundary or (strict and start == boundary):
                parts_offset += end - start
            else:
                break
        logger.debug("original_index with parts_offset: %s", part_free_index + parts_offset)
        return part_free_index + parts_offset

    def increment_indexes(after_part_free_index: int, offset: int, strict: bool = False) -> None:
        """Increment indexes after the given index (in coordinates after removal) by the given offset.

        Args:
            after_part_free_index: Start position in text after removal where <b> tag is inserted
            offset: Amount to increment by
            strict: If True, only increment indexes strictly after the given index.
        """
        # Convert part-free index to original text index
        after_original_index = part_free_to_original_index(after_part_free_index, strict)

        # Find the first part at or after the calculated position
        # We want to include parts that are right at the boundary
        actual_after_index = after_original_index
        for start, end, _ in part_indexes:
            if start < after_original_index and end > after_original_index:
                # Part spans across the insertion point, start from this tag
                actual_after_index = start
                break
            elif end == after_original_index and not strict:
                # Part ends exactly at insertion point, include it
                actual_after_index = start
                break

        logger.debug(
            "increment_indexes: after_original=%s (actual=%s), offset=%s",
            after_original_index,
            actual_after_index,
            offset,
        )

        for i in range(len(part_indexes)):
            start, end, tag_str = part_indexes[i]
            if start >= actual_after_index:
                part_indexes[i] = (start + offset, end + offset, tag_str)
                logger.debug("  Incremented part at %s to %s", start, start + offset)

        # Record the offset for future index calculations
        offset_indexes.append((after_part_free_index, offset))

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "Diff state after increment_indexes - part regex: %s\n\033[90m'%s'\033[0m",
                part_regex,
                make_diff_string_for_indexes(cleaned_text, part_indexes, offset_indexes),
            )

    def restore_parts(edited_text: str) -> str:
        """Restores the parts back into the text."""
        for start, end, part_str in part_indexes:
            edited_text = edited_text[:start] + part_str + edited_text[start:]
            logger.debug("Restored part: '%s' at index %s", part_str, start)

        return edited_text

    return cleaned_text, increment_indexes, restore_parts, part_indexes
