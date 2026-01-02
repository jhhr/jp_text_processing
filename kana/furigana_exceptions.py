"""
Exception handling that integrates with alignment-based reconstruction.

Instead of returning pre-computed strings that don't interact well with highlighting,
exceptions now return a MoraAlignment dict that the main pipeline can feed into
`reconstruct_from_alignment`, ensuring consistent handling of bolding, tags,
and word edge splitting.
"""

from typing import TypedDict, Optional, List, Dict

try:
    from kana.mora_alignment import MoraAlignment
except ImportError:
    from .mora_alignment import MoraAlignment
try:
    from all_types.main_types import ReadingMatchInfo
except ImportError:
    from ..all_types.main_types import ReadingMatchInfo
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger


class ExceptionAlignmentEntry(TypedDict):
    """
    Per-kanji exception entry describing how that kanji's reading should be treated.

    :param type: One of 'jukujikun', 'onyomi', 'kunyomi'
    :param mora: The kana reading for this kanji portion (no tags)
    """

    type: str
    mora: str


FURIGANA_EXCEPTION_ALIGNMENTS: Dict[str, List[ExceptionAlignmentEntry]] = {
    # 麻雀[まーじゃん] - Both kanji are jukujikun
    "麻雀_まーじゃん": [
        {"type": "jukujikun", "mora": "まー"},
        {"type": "jukujikun", "mora": "じゃん"},
    ],
    # 菠薐草[ほうれんそう] - ほうれん is jukujikun, 草 is onyomi
    "菠薐草_ほうれんそう": [
        {"type": "jukujikun", "mora": "ほう"},
        {"type": "jukujikun", "mora": "れん"},
        {"type": "onyomi", "mora": "そう"},
    ],
    # 菠薐[ほうれん] - both jukujikun
    "菠薐_ほうれん": [
        {"type": "jukujikun", "mora": "ほう"},
        {"type": "jukujikun", "mora": "れん"},
    ],
    # 清々[すがすが]しい - 清々 are jukujikun
    "清々_すがすが": [
        {"type": "jukujikun", "mora": "すが"},
        {"type": "jukujikun", "mora": "すが"},
    ],
    # 田圃[たんぼ] - 田 is jukujikun, 圃 is onyomi
    "田圃_たんぼ": [
        {"type": "jukujikun", "mora": "たん"},
        {"type": "onyomi", "mora": "ぼ"},
    ],
    # 袋小路[ふくろこうじ] - 袋 is kunyomi, 小 is jukujikun, 路 is onyomi
    "袋小路_ふくろこうじ": [
        {"type": "kunyomi", "mora": "ふくろ"},
        {"type": "jukujikun", "mora": "こう"},
        {"type": "kunyomi", "mora": "じ"},
    ],
    # 尻尾[しっぽ] - both kunyomi
    "尻尾_しっぽ": [
        {"type": "kunyomi", "mora": "しっ"},
        {"type": "kunyomi", "mora": "ぽ"},
    ],
    # 風邪[かぜ] - jukujikun
    "風邪_かぜ": [
        {"type": "jukujikun", "mora": "か"},
        {"type": "jukujikun", "mora": "ぜ"},
    ],
    # 薔薇[ばら] - jukujikun
    "薔薇_ばら": [
        {"type": "jukujikun", "mora": "ば"},
        {"type": "jukujikun", "mora": "ら"},
    ],
    # 真面目[まじめ] - 真面 jukujikun, 目 onyomi
    "真面目_まじめ": [
        {"type": "jukujikun", "mora": "ま"},
        {"type": "jukujikun", "mora": "じ"},
        {"type": "kunyomi", "mora": "め"},
    ],
    # 蕎麦[そば] - jukujikun
    "蕎麦_そば": [
        {"type": "jukujikun", "mora": "そ"},
        {"type": "jukujikun", "mora": "ば"},
    ],
    # 襤褸[ぼろ] - jukujikun
    "襤褸_ぼろ": [
        {"type": "jukujikun", "mora": "ぼ"},
        {"type": "jukujikun", "mora": "ろ"},
    ],
    # 愈 has kunyomi reading いよいよ but can also be written repeated but read the same
    "愈々_いよいよ": [
        {"type": "kunyomi", "mora": "いよ"},
        {"type": "kunyomi", "mora": "いよ"},
    ],
    # 蝶々 can be written shortened where the furigana doesn't repeat completely
    "蝶々_ちょうちょ": [
        {"type": "onyomi", "mora": "ちょう"},
        {"type": "onyomi", "mora": "ちょ"},
    ],
}


def _build_alignment(word: str, parts: List[ExceptionAlignmentEntry]) -> MoraAlignment:
    kanji_count = len(word)
    assert kanji_count == len(
        parts
    ), f"Exception alignment parts length mismatch for '{word}': {len(parts)} vs {kanji_count}"
    kanji_matches: List[Optional[ReadingMatchInfo]] = []
    mora_split: List[List[str]] = []
    jukujikun_positions: List[int] = []

    for idx, entry in enumerate(parts):
        mora_split.append([entry["mora"]])
        t = entry["type"]
        if t == "jukujikun":
            kanji_matches.append({
                "reading": entry["mora"],
                "dict_form": entry["mora"],
                "match_type": "jukujikun",
                "reading_variant": "plain",
                "matched_mora": entry["mora"],
                "kanji": word[idx],
                "okurigana": "",
                "rest_kana": "",
            })
            # Keep positions list for reference (not necessary if reconstruct handles juk type)
            jukujikun_positions.append(idx)
        elif t in ("onyomi", "kunyomi"):
            kanji_matches.append({
                "reading": entry["mora"],
                "dict_form": entry["mora"],
                "match_type": t,
                "reading_variant": "plain",
                "matched_mora": entry["mora"],
                "kanji": word[idx],
                "okurigana": "",
                "rest_kana": "",
            })
        else:
            # Unknown type: treat as jukujikun
            kanji_matches.append({
                "reading": entry["mora"],
                "dict_form": entry["mora"],
                "match_type": "jukujikun",
                "reading_variant": "plain",
                "matched_mora": entry["mora"],
                "kanji": word[idx],
                "okurigana": "",
                "rest_kana": "",
            })
            jukujikun_positions.append(idx)

    return MoraAlignment(
        kanji_matches=kanji_matches,
        mora_split=mora_split,
        jukujikun_positions=jukujikun_positions,
        is_complete=True,
        final_okurigana="",
        final_rest_kana="",
    )


def check_exception(
    word: str,
    furigana: str,
    logger: Logger = Logger("error"),
) -> Optional[MoraAlignment]:
    """
    Check if word+furigana combination is in the exception dictionary and return a
    MoraAlignment object so the main pipeline can reconstruct furigana consistently.

    :param word: The full word (kanji form)
    :param furigana: The bracket furigana portion (without okurigana)
    :return: MoraAlignment for the exception, or None
    """
    exception_key = f"{word}_{furigana}"
    logger.debug(f"check_exception: checking for exception key: {exception_key}")
    parts = FURIGANA_EXCEPTION_ALIGNMENTS.get(exception_key)
    if not parts:
        return None
    return _build_alignment(word, parts)
