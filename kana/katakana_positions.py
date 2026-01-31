try:
    from mecab_controller.kana_conv import (
        to_katakana,
        is_katakana_char,
    )
except ImportError:
    from ..mecab_controller.kana_conv import (
        to_katakana,
        is_katakana_char,
    )


def get_katakana_positions(text: str) -> list[int]:
    """
    Get the indices of katakana characters in a string.

    :param text: The text to check
    :return: List of indices where characters are katakana
    """
    if not text:
        return []
    positions = []
    for i, char in enumerate(text):
        if is_katakana_char(char):
            positions.append(i)
    return positions


def convert_positions_to_katakana(
    text: str, original_text: str, original_positions: list[int]
) -> str:
    """
    Convert specific positions in text to katakana based on positions in original_text.

    This function maps character positions from original_text to text and converts those
    positions to katakana. This handles the case where text is a substring of original_text.

    :param text: The text to convert (typically a portion of original_text)
    :param original_text: The original full text that has known katakana positions
    :param original_positions: List of indices in original_text that were katakana
    :return: Text with appropriate positions converted to katakana
    """
    if not text or not original_positions:
        return text

    # Find where text appears in original_text
    start_pos = original_text.find(text)
    if start_pos == -1:
        # Text not found in original, can't map positions
        return text

    # Convert positions relative to text
    text_chars = list(text)
    for pos in original_positions:
        # Check if this original position falls within our text span
        text_pos = pos - start_pos
        if 0 <= text_pos < len(text_chars):
            text_chars[text_pos] = to_katakana(text_chars[text_pos])

    return "".join(text_chars)
