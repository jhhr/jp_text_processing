from typing import Optional, Literal, TypedDict, NamedTuple


class WithTagsDef(NamedTuple):
    """
    NamedTuple for the definition of the tags to wrap the furigana in
    :param with_tags
    :param merge_consecutive
    :param onyomi_to_katakana
    :param include_suru_okuri
    """

    with_tags: bool
    merge_consecutive: bool
    onyomi_to_katakana: bool
    include_suru_okuri: bool


Edge = Literal["left", "right", "middle", "whole", "none"]


MatchType = Literal["onyomi", "kunyomi", "jukujikun", "none"]


class WrapMatchEntry(TypedDict):
    """
    Structure describing a single kanji ↔ furigana pairing for reconstruction.

    :param kanji: Surface kanji (or digit/repeater) this entry corresponds to
    :param tag: The furigana tag type (on/kun/juk/mix)
    :param furigana: Reading for the kanji
    :param highlight: Whether this entry belongs to the highlighted span
    :param is_num: Whether the kanji represents a numeric block
    :param is_noun_suru_verb: Whether this match is to a noun that functions as a suru-verb and has
        okurigana attached (which is a する conjugation)
    """

    kanji: str
    tag: Literal["on", "kun", "juk", "mix"]
    furigana: str
    highlight: bool
    is_num: bool
    is_noun_suru_verb: Optional[bool]


class YomiMatchResult(TypedDict):
    """
    TypedDict for the result of the onyomi or kunyomi match check
    :param text
    :param type
    :param match_edge
    :param actual_match
    :param matched_reading
    :param all_readings_processed: True when the loop over readings reached the last reading
    """

    text: str
    type: MatchType
    match_edge: Edge
    actual_match: str
    matched_reading: str


class FinalResult(TypedDict):
    """
    TypedDict for the final result of the onyomi or kunyomi match check
    :param segments: Sequence of wrap entries split into portions (before, highlight, after)
    :param highlight_segment_index: Index of the highlighted segment in `segments` or None
    :param word: The full word being reconstructed (used for spacing/okuri decisions)
    :param edge: Legacy edge position of the highlight for okuri tagging
    :param highlight_match_type: The match type that was highlighted
    :param okurigana
    :param rest_kana
    :param was_katakana: Whether the original furigana was in katakana
    """

    segments: list[list[WrapMatchEntry]]
    highlight_segment_index: Optional[int]
    word: str
    edge: Edge
    match_type: MatchType
    okurigana: str
    rest_kana: str
    was_katakana: bool


PartOfSpeech = Literal[
    "adj-i",
    "adj-na",
    "adj-ix",
    "v1",
    "v1-s",
    "v5aru",
    "v5b",
    "v5g",
    "v5k",
    "v5k-s",
    "v5m",
    "v5n",
    "v5r",
    "v5r-i",
    "v5s",
    "v5t",
    "v5u",
    "v5u-s",
    "vk",
    "vs",
    "vs-s",
    "vs-i",
]

PARTS_OF_SPEECH: list[PartOfSpeech] = [
    "adj-i",
    "adj-na",
    "adj-ix",
    "v1",
    "v1-s",
    "v5aru",
    "v5b",
    "v5g",
    "v5k",
    "v5k-s",
    "v5m",
    "v5n",
    "v5r",
    "v5r-i",
    "v5s",
    "v5t",
    "v5u",
    "v5u-s",
    "vk",
    "vs",
    "vs-s",
    "vs-i",
]

OkuriType = Literal["full_okuri", "partial_okuri", "empty_okuri", "no_okuri", "detected_okuri"]


class OkuriResults(NamedTuple):
    okurigana: str
    rest_kana: str
    result: OkuriType
    part_of_speech: Optional[PartOfSpeech] = None


ReadingType = Literal["none", "plain", "rendaku", "small_tsu", "rendaku_small_tsu", "vowel_change"]


class ReadingMatchInfo(TypedDict):
    """
    Information about a successful reading match for a kanji.

    :param reading: The actual reading that matched (may include rendaku/small tsu variations)
    :param dict_form: The dictionary form reading (for kunyomi, includes okurigana marker like "か.く")
    :param match_type: Type of match (onyomi, kunyomi, or jukujikun if unmatched)
    :param reading_variant: How the reading was modified (plain, rendaku, small_tsu, etc.)
    :param matched_mora: The mora string that was matched from the furigana
    :param kanji: The kanji character this match is for
    :param okurigana: Extracted okurigana (only for last kanji when is_last_kanji=True)
    :param rest_kana: Remaining kana after okurigana extraction
    :param is_noun_suru_verb: Whether this match is to a noun that functions as a suru-verb and has
        okurigana attached (which is a する conjugation)
    """

    reading: str
    dict_form: str
    match_type: MatchType
    reading_variant: ReadingType
    matched_mora: str
    kanji: str
    okurigana: str
    rest_kana: str
    is_noun_suru_verb: Optional[bool]


class MoraAlignment(TypedDict):
    """
    Result of aligning mora to kanji in a word.

    :param kanji_matches: List of ReadingMatchInfo for each kanji (None if jukujikun/unmatched)
    :param mora_split: The actual mora split used (list of mora sublists, one per kanji)
    :param jukujikun_positions: List of indices where no reading matched (jukujikun positions)
    :param is_complete: True if all kanji matched a reading (no jukujikun positions)
    :param final_okurigana: Okurigana extracted from last kanji (if any)
    :param final_rest_kana: Remaining kana after okurigana extraction
    """

    kanji_matches: list[Optional[ReadingMatchInfo]]
    mora_split: list[list[str]]
    jukujikun_positions: list[int]
    is_complete: bool
    final_okurigana: str
    final_rest_kana: str
