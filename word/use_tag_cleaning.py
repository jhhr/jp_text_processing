import re

from ..utils.logger import package_logger as logger
from .use_text_part_storage import (
    BTagIndexIncrementer,
    IndexIncrementer,
    TextPartIndexes,
    TextPartRestorer,
    use_text_part_storage,
)


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


TAG_RE = re.compile(r"<(/?)([a-zA-Z][^\s/>]*)[^>]*>")
EMPTY_PAIR = r"<([a-zA-Z][^\s/>]*)[^>]*></\1>"
# Tags that never enclose anything, so they can't be crossed by a <b> span
UNPAIRED_TAGS = {"br", "hr", "img", "wbr", "b"}


def crossed_tags(text: str, b_open: int, b_close: int) -> tuple[list[str], list[str]]:
    """
    Find the tags that a <b>...</b> span crosses instead of enclosing.

    Args:
        text: The text containing the b tags.
        b_open: Index of the opening <b>.
        b_close: Index of the closing </b>.
    Returns:
        A tuple of:
            - the tags opened inside the span and closed after it, outermost first
            - the tags opened before the span and closed inside it, innermost first
    """
    opened: list[str] = []
    closed_from_before: list[str] = []
    for m in TAG_RE.finditer(text, b_open + len("<b>"), b_close):
        tag = m.group(2)
        if tag in UNPAIRED_TAGS:
            continue
        if not m.group(1):
            opened.append(tag)
        elif opened and opened[-1] == tag:
            opened.pop()
        else:
            closed_from_before.append(tag)
    return opened, closed_from_before


def balance_b_tags(text: str) -> str:
    """
    Close and reopen the tags that a <b>...</b> crosses, which the reorderings in
    apply_tag_fixes can only do when the tag sits right next to a b tag:
    '<b><k>A</k>を<k>B</b>C</k>' becomes '<b><k>A</k>を<k>B</k></b><k>C</k>'.

    Args:
        text: The text after restoring tags.
    Returns:
        The text with every b span enclosing whole tags.
    """
    result = ""
    rest = text
    while True:
        b_open = rest.find("<b>")
        b_close = rest.find("</b>", b_open + 3) if b_open != -1 else -1
        if b_close == -1:
            return result + rest
        opened, closed_from_before = crossed_tags(rest, b_open, b_close)
        result += (
            rest[:b_open]
            # Tags the span started inside of are closed before it and reopened within it
            + "".join(f"</{tag}>" for tag in closed_from_before)
            + "<b>"
            + "".join(f"<{tag}>" for tag in reversed(closed_from_before))
            + rest[b_open + 3 : b_close]
            # Tags the span opened are closed within it and reopened after it
            + "".join(f"</{tag}>" for tag in reversed(opened))
            + "</b>"
            + "".join(f"<{tag}>" for tag in opened)
        )
        rest = rest[b_close + 4 :]


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
    # Any remaining tag the b span crosses instead of enclosing
    result = balance_b_tags(result)
    if result != restored_text:
        # The reopened tags can end up empty, e.g. when the reordering above already handled
        # them. Only what the reorderings left behind is cleaned up: an empty element the
        # caller wrote next to the word is theirs and stays.
        result = re.sub(rf"{EMPTY_PAIR}(?=<b>)", "", result)
        result = re.sub(rf"(?<=<b>){EMPTY_PAIR}", "", result)
        result = re.sub(rf"{EMPTY_PAIR}(?=</b>)", "", result)
        result = re.sub(rf"(?<=</b>){EMPTY_PAIR}", "", result)
    return result


TAG_PART_RE = r"<\/?[^>]+>"
# A splitter dot between the parts of a word (報・連・相) is stored like a tag as well, so the
# word matches without it and it comes back where it was.
SPLITTER_DOT_RE = r"・\s*"
# Whitespace and dots go into the same storage as the tags for a caller that loses them, rather
# than into a storage of their own: two storages each index a text the other one still has its
# parts in, so neither can place a <b> that the other's parts sit around. The tag comes first in
# the alternation, so the space inside <span class="x"> is part of that tag and stays in it.
TAG_AND_DOT_PART_RE = rf"{TAG_PART_RE}|{SPLITTER_DOT_RE}"
# The furigana paths match the space before a kanji as part of the word, so there the dot has to
# leave the space where it is.
TAG_AND_BARE_DOT_PART_RE = rf"{TAG_PART_RE}|・"
TAG_AND_SPACE_PART_RE = rf"{TAG_PART_RE}|\s+|{SPLITTER_DOT_RE}"
# A reading in brackets is not text the word occurs in, so the mecab path stores it away with
# the tags instead of letting MeCab read it as part of the sentence and highlight inside it.
FURIGANA_PART_RE = r"\[[^\]]*\]"
TAG_SPACE_AND_FURIGANA_PART_RE = rf"{TAG_PART_RE}|\s+|{SPLITTER_DOT_RE}|{FURIGANA_PART_RE}"


def use_tag_cleaning_with_b_insertion(
    text: str,
    part_regex: str = TAG_PART_RE,
) -> tuple[str, BTagIndexIncrementer, TextPartRestorer, TextPartIndexes]:
    """
    Stores indexes of all HTML tags and removes them temporarily, to
    be restored later. Also provides helper to increment indexes for <b> tag insertions.

    Args:
        text: The original text containing parts to be stored.
        part_regex: What to store; one of the TAG_AND_* alternations to take the whitespace
            or the splitter dots with the tags.
    Returns:
        A tuple containing:
            - The cleaned text with parts removed.
            - A function to increment indexes after modifications.
            - A function to restore the stored parts back into the text.
            - The indexes of the stored tags.
    """
    cleaned_text, increment_indexes, restore_parts, indexes = use_text_part_storage(
        text, part_regex=part_regex
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
        logger.debug("Text before applying tag fixes: '%s'", result)
        result = apply_tag_fixes(result)
        logger.debug("Text after applying tag fixes: '%s'", result)
        return result

    return cleaned_text, custom_incrementer, custom_restorer, indexes
