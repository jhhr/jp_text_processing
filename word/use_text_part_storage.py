import re
from typing import Callable

try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger

TextPartIndexes = list[tuple[int, int, str]]
OffsetIndexes = list[tuple[int, int]]
IndexIncrementer = Callable[[int, int, int | None], None]
TextPartRestorer = Callable[[str], str]


def make_diff_string_for_indexes(
    cleaned_text: str,
    indexes: TextPartIndexes,
    offset_indexes: OffsetIndexes,
    logger: Logger = Logger("error"),
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
    logger.debug(f"Offset indexes: {offset_indexes}")
    for index, offset in sorted(offset_indexes, key=lambda x: x[0]):
        adjusted_index = index + total_offset
        simulated_edited_text = (
            simulated_edited_text[:adjusted_index]
            + ("_" * offset)
            + simulated_edited_text[adjusted_index:]
        )
        total_offset += offset
    logger.debug(f"Simulated edited text: \33[90m'{simulated_edited_text}'\33[0m")
    # Then reconstruct the parts into the simulated edited text exactly as restore_parts
    for start, end, part_str in indexes:
        simulated_edited_text = (
            simulated_edited_text[:start] + part_str + simulated_edited_text[start:]
        )
    return simulated_edited_text


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

    part_indexes: TextPartIndexes = []
    offset_indexes: OffsetIndexes = []
    last_index = 0

    logger.debug(f"Using part regex: '{part_regex}' to store text parts.")

    cleaned_text = ""
    for match in re.finditer(part_regex, text):
        start, end = match.span()
        cleaned_text += text[last_index:start]
        part_indexes.append((start, end, match.group(0)))
        logger.debug(f"Found part matching regex: '{match.group(0)}' at indexes ({start}, {end})")
        last_index = end
    cleaned_text += text[last_index:]
    logger.debug(f"Text after removal of parts: '{cleaned_text}'")
    logger.debug(f"Indexes of removed parts stored: {part_indexes}")

    def part_free_to_original_index(part_free_index: int) -> int:
        """Convert index in text after removal to index in original text."""
        logger.debug(f"Converting part_free_index: {part_free_index} to original index")
        # Calculate offset due to removed parts
        parts_offset = 0
        for start, end, _ in part_indexes:
            if start <= part_free_index + parts_offset:
                parts_offset += end - start
            else:
                break
        logger.debug(f"original_index with parts_offset: {part_free_index + parts_offset}")
        # Now account for any offsets added during modifications
        offsets_offset = 0
        for index, offset in offset_indexes:
            if index <= part_free_index:
                offsets_offset += offset
            else:
                break
        logger.debug(
            "final original_index with offsets_offset:"
            f" {part_free_index + parts_offset - offsets_offset}"
        )

        return part_free_index + parts_offset - offsets_offset

    def increment_indexes(after_part_free_index: int, offset: int, strict: bool = False) -> None:
        """Increment indexes after the given index (in coordinates after removal) by the given offset.

        Args:
            after_part_free_index: Start position in text after removal where <b> tag is inserted
            offset: Amount to increment by
            strict: If True, only increment indexes strictly after the given index.
        """
        # Convert part-free index to original text index
        after_original_index = part_free_to_original_index(after_part_free_index)

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
            "increment_indexes:"
            f" after_original={after_original_index} (actual={actual_after_index}),"
            f" offset={offset}"
        )

        for i in range(len(part_indexes)):
            start, end, tag_str = part_indexes[i]
            if start >= actual_after_index:
                part_indexes[i] = (start + offset, end + offset, tag_str)
                logger.debug(f"  Incremented part at {start} to {start + offset}")

        # Record the offset for future index calculations
        offset_indexes.append((after_part_free_index, offset))

        logger.debug(
            f"Diff state after increment_indexes - part regex: {part_regex}\n"
            f"\33[90m'{make_diff_string_for_indexes(cleaned_text, part_indexes, offset_indexes, logger)}'\033[0m"
        )

    def restore_parts(edited_text: str) -> str:
        """Restores the parts back into the text."""
        for start, end, part_str in part_indexes:
            edited_text = edited_text[:start] + part_str + edited_text[start:]
            logger.debug(f"Restored part: '{part_str}' at index {start}")

        return edited_text

    return cleaned_text, increment_indexes, restore_parts, part_indexes


def run_tests():
    # Should reconstruct identically if no modifications
    text1 = (
        "<div>「<k> 糞[クソ]</k><k> 程[ほど]</k><k> 詰[つま]らん</k>。<k> 何[なん]</k>でも<k>"
        " 無[な]い</k> 女[おんな]の 会話[かいわ]。」</div><div>「<k> 其[そ]れ</k>、"
        " 特大[とくだい]ブーメランじゃねぇ？」</div>"
    )
    cleaned_text, increment_indexes, restore_parts, indexes = use_text_part_storage(text1)
    reconstructed_text = restore_parts(cleaned_text)
    assert reconstructed_text == text1, f"Expected: '{text1}', Got: '{reconstructed_text}'"
    print("\n\033[92mTests passed\033[0m")


if __name__ == "__main__":
    run_tests()
