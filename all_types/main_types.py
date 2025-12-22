from typing import Optional, Literal, TypedDict, NamedTuple, NotRequired


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


class WordData(TypedDict):
    """
    TypedDict for data about a single word that was matched in the text for the kanji_to_match
    :param kanji_pos
    :param kanji_count
    :param word
    :param furigana
    :param okurigana
    :param edge
    """

    kanji_pos: int
    kanji_count: int
    word: str
    furigana: str
    furigana_is_katakana: bool
    okurigana: str
    edge: Edge


class HighlightArgs(TypedDict):
    """
    TypedDict for the base arguments passed to kana_highlight as these get passed around a lot
    :param text
    :param onyomi
    :param kunyomi
    :param kanji_to_match
    :param kanji_to_highlight
    :param add_highlight
    :param edge
    """

    onyomi: str
    kunyomi: str
    kanji_to_match: str
    kanji_to_highlight: Optional[str]
    add_highlight: bool
    edge: Edge
    full_word: str
    full_furigana: str


MatchType = Literal["onyomi", "kunyomi", "jukujikun", "none"]


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
    all_readings_processed: NotRequired[bool]


class PartialResult(TypedDict):
    """
    TypedDict for the partial result of the onyomi or kunyomi match check
    :param matched_furigana
    :param match_type
    :param rest_furigana
    :param okurigana
    :param rest_kana
    :param edge
    :param matched_reading: The reading that was matched for this kanji
    :param all_readings_processed: True when all readings for this kanji have been checked
    """

    matched_furigana: str
    match_type: MatchType
    rest_furigana: str
    okurigana: str
    rest_kana: str
    edge: Edge
    matched_reading: NotRequired[str]
    all_readings_processed: NotRequired[bool]


class FinalResult(TypedDict):
    """
    TypedDict for the final result of the onyomi or kunyomi match check
    :param furigana
    :param okurigana
    :param rest_kana
    :param left_word
    :param middle_word
    :param right_word
    :param edge
    :param match_type
    :param was_katakana: Whether the original furigana was in katakana
    """

    furigana: str
    okurigana: str
    rest_kana: str
    left_word: str
    middle_word: str
    right_word: str
    edge: Edge
    match_type: MatchType
    was_katakana: NotRequired[bool]


class FuriganaParts(TypedDict):
    """
    TypedDict for the parts of the furigana that were matched
    :param has_highlight
    :param left_furigana
    :param middle_furigana
    :param right_furigana
    :param matched_edge
    """

    has_highlight: bool
    left_furigana: Optional[str]
    middle_furigana: Optional[str]
    right_furigana: Optional[str]
    matched_edge: Edge


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
    """

    reading: str
    dict_form: str
    match_type: MatchType
    reading_variant: ReadingType
    matched_mora: str
    kanji: str
    okurigana: str
    rest_kana: str


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
