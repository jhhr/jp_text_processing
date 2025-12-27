try:
    from mecab_controller.kana_conv import to_katakana
except ImportError:
    from ..mecab_controller.kana_conv import to_katakana

RENDAKU_CONVERSION_DICT_HIRAGANA = {
    "か": ["が"],
    "き": ["ぎ"],
    "く": ["ぐ"],
    "け": ["げ"],
    "こ": ["ご"],
    "さ": ["ざ"],
    "し": ["じ"],
    "す": ["ず"],
    "せ": ["ぜ"],
    "そ": ["ぞ"],
    "た": ["だ"],
    "ち": ["ぢ"],
    "つ": ["づ"],
    "て": ["で"],
    "と": ["ど"],
    "は": ["ば", "ぱ"],
    "ひ": ["び", "ぴ"],
    "ふ": ["ぶ", "ぷ"],
    "へ": ["べ", "ぺ"],
    "ほ": ["ぼ", "ぽ"],
    "う": ["ぬ"],
}
# Convert HIRAGANA_CONVERSION_DICT to katakana with to_katakana
RENDAKU_CONVERSION_DICT_KATAKANA = {
    to_katakana(k): [to_katakana(v) for v in vs]
    for k, vs in RENDAKU_CONVERSION_DICT_HIRAGANA.items()
}
