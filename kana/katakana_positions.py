from ..mecab_controller.kana_conv import is_katakana_char


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
