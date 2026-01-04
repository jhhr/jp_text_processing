import re
from typing import Callable, Optional

try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger

TextPartIndexes = list[tuple[int, int, str]]
IndexIncrementer = Callable[[int, int, int | None], None]
TextPartRestorer = Callable[[str], str]


def use_text_part_storage(
    text: str, part_regex: str = r"<\/?[^>]+>", logger: Logger = Logger("error")
) -> tuple[str, IndexIncrementer, TextPartRestorer, TextPartIndexes]:
    """
    Stores indexes of all parts matching the given regex and removes them temporarily, to
    be restored later.
    Args:
        text: The original text containing parts to be stored.
        part_regex: The regex pattern to identify parts to be stored. Defaults to HTML tags.
        logger: Logger instance for logging debug and error messages.
    Returns:
        A tuple containing:
            - The cleaned text with parts removed.
            - A function to increment indexes after modifications.
            - A function to restore the stored parts back into the text.
    """

    indexes: TextPartIndexes = []
    cleaned_text = ""
    last_index = 0

    logger.debug(f"Using part regex: '{part_regex}' to store text parts.")

    for match in re.finditer(part_regex, text):
        start, end = match.span()
        cleaned_text += text[last_index:start]
        indexes.append((start, end, match.group(0)))
        logger.debug(f"Found part matching regex: '{match.group(0)}' at indexes ({start}, {end})")
        last_index = end
    cleaned_text += text[last_index:]
    logger.debug(f"Text after removal of parts: '{cleaned_text}'")
    logger.debug(f"Indexes of removed parts stored: {indexes}")

    def part_free_to_original_index(part_free_index: int) -> int:
        """Convert index in text after removal to index in original text."""
        offset = 0
        for start, end, _ in indexes:
            if start <= part_free_index + offset:
                offset += end - start
            else:
                break
        return part_free_index + offset

    def increment_indexes(
        after_part_free_index: int, offset: int, before_part_free_index: Optional[int] = None
    ) -> None:
        """Increment indexes after the given index (in coordinates after removal) by the given offset.

        Args:
            after_part_free_index: Start position in text after removal where <b> tag is inserted
            offset: Amount to increment by (7 for full <b></b> pair, 3 for opening <b> only)
            before_edited_index: Optional end position in text after removal where </b> is inserted.
                                If provided, tags between [after, before) are incremented by 3 (opening tag),
                                and tags >= before are incremented by the full offset (both tags).
        """
        # Convert part-free index to original text index
        after_original_index = part_free_to_original_index(after_part_free_index)

        # Find the first tag at or after the calculated position
        # We want to include tags that are right at the boundary
        actual_after_index = after_original_index
        for start, end, _ in indexes:
            if start < after_original_index and end > after_original_index:
                # Tag spans across the insertion point, start from this tag
                actual_after_index = start
                break
            elif end == after_original_index:
                # Tag ends exactly at insertion point, include it
                actual_after_index = start
                break

        if before_part_free_index is not None:
            before_original_index = part_free_to_original_index(before_part_free_index)
            logger.debug(
                "increment_indexes:"
                f" after_original={after_original_index} (actual={actual_after_index}),"
                f" before_original={before_original_index}, offset={offset}"
            )

            for i in range(len(indexes)):
                start, end, tag_str = indexes[i]
                # Tags between the <b> and </b> positions: increment by opening tag length only (3)
                if start >= actual_after_index and start < before_original_index:
                    indexes[i] = (start + 3, end + 3, tag_str)
                    logger.debug(f"  Incremented part (inside) at {start} to {start + 3}")
                # Tags at or after the </b> position: increment by full offset
                elif start >= before_original_index:
                    indexes[i] = (start + offset, end + offset, tag_str)
                    logger.debug(f"  Incremented part (after) at {start} to {start + offset}")
        else:
            logger.debug(
                "increment_indexes:"
                f" after_original={after_original_index} (actual={actual_after_index}),"
                f" offset={offset}"
            )

            for i in range(len(indexes)):
                start, end, tag_str = indexes[i]
                if start >= actual_after_index:
                    indexes[i] = (start + offset, end + offset, tag_str)
                    logger.debug(f"  Incremented part at {start} to {start + offset}")

    def restore_tags(edited_text: str) -> str:
        """Restores the parts back into the text."""
        for start, end, tag_str in indexes:
            edited_text = edited_text[:start] + tag_str + edited_text[start:]
            logger.debug(f"Restored part: '{tag_str}' at index {start}")

        return edited_text

    return cleaned_text, increment_indexes, restore_tags, indexes
