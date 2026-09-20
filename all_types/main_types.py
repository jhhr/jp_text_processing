from typing import Literal, NamedTuple, TypedDict


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


MatchType = Literal["onyomi", "kunyomi", "jukujikun", "none"]


WrapTag = Literal["on", "kun", "juk", "mix"]


class _WrapMatchEntryOptional(TypedDict, total=False):
    """Keys of WrapMatchEntry the builders may leave out. (NotRequired needs Python 3.11.)"""

    is_noun_suru_verb: bool | None


class WrapMatchEntry(_WrapMatchEntryOptional):
    """
    Structure describing a single kanji ↔ furigana pairing for reconstruction.

    :param kanji: Surface kanji (or digit/repeater) this entry corresponds to
    :param tag: The furigana tag type (on/kun/juk/mix)
    :param furigana: Reading for the kanji
    :param highlight: Whether this entry belongs to the highlighted span
    :param is_num: Whether the kanji represents a numeric block
    :param is_noun_suru_verb: Optional. Whether this match is to a noun that functions as a
        suru-verb and has okurigana attached (which is a する conjugation)
    """

    kanji: str
    tag: WrapTag
    furigana: str
    highlight: bool
    is_num: bool


class FinalResult(TypedDict):
    """
    TypedDict for the final result of the onyomi or kunyomi match check
    :param segments: Sequence of wrap entries split into runs that are all highlighted or all not
    :param highlight_segment_indices: Indices of the highlighted segments in `segments`, in order
    :param word: The full word being reconstructed (used for spacing/okuri decisions)
    :param highlight_match_type: The match type that was highlighted
    :param okurigana
    :param rest_kana
    :param katakana_positions: List of character indices in original furigana that were katakana
    :param restored_chars: Index in the matched furigana → the character the original had there,
        for the kana that were rewritten or dropped before matching, ー among them
    :param original_furigana: The original furigana before hiragana conversion
    """

    segments: list[list[WrapMatchEntry]]
    highlight_segment_indices: list[int]
    word: str
    highlight_match_type: MatchType
    okurigana: str
    rest_kana: str
    katakana_positions: list[int]
    restored_chars: dict[int, str]
    original_furigana: str


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

OkuriType = Literal[
    "full_okuri",
    "partial_okuri",
    "empty_okuri",
    "no_okuri",
    "detected_okuri",
    "rejected_lexical_suffix",
]


class OkuriResults(NamedTuple):
    okurigana: str
    rest_kana: str
    result: OkuriType
    part_of_speech: PartOfSpeech | None = None


ReadingType = Literal[
    "none", "plain", "rendaku", "small_tsu", "rendaku_small_tsu", "vowel_change", "n_change"
]


class _ReadingMatchInfoOptional(TypedDict, total=False):
    """Keys of ReadingMatchInfo the builders may leave out. (NotRequired needs Python 3.11.)"""

    is_noun_suru_verb: bool | None


class ReadingMatchInfo(_ReadingMatchInfoOptional):
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
    :param is_noun_suru_verb: Optional. Whether this match is to a noun that functions as a
        suru-verb and has okurigana attached (which is a する conjugation)
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
    :param mora_split: The actual mora split used (the mora assigned to each kanji, joined,
        one string per kanji)
    :param jukujikun_positions: List of indices where no reading matched (jukujikun positions)
    :param final_okurigana: Okurigana extracted from last kanji (if any)
    :param final_rest_kana: Remaining kana after okurigana extraction
    """

    kanji_matches: list[ReadingMatchInfo | None]
    mora_split: list[str]
    jukujikun_positions: list[int]
    final_okurigana: str
    final_rest_kana: str
