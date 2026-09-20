"""Cases for the mora alignment search, with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/kana/mora_alignment_tests.py

The search itself is covered through kana_highlight_tests; what is here is the machinery under
it that those cases cannot see.
"""

from .mora_alignment import find_first_complete_alignment
from .reading_matcher import cached_reading_match


def test_cached_reading_match_hands_out_copies():
    """The alignment writes into the match dicts it is given (blanking a repeater pair's
    okurigana, renaming its kanji), so a second call with the same arguments has to get the
    match as the matchers made it, not as the first caller left it."""
    args = ("食", "食", "たべ", "た", "べる", True, None)
    first_kunyomi, first_onyomi = cached_reading_match(*args)
    assert first_kunyomi is not None and first_onyomi is None
    original = dict(first_kunyomi)

    first_kunyomi["kanji"] = "々"
    first_kunyomi["okurigana"] = ""
    first_kunyomi["rest_kana"] = ""

    second_kunyomi, second_onyomi = cached_reading_match(*args)
    assert second_kunyomi == original
    assert second_kunyomi is not first_kunyomi
    assert second_onyomi is None


def test_repeater_constraint_is_dropped_when_no_split_satisfies_it():
    """A 々 is held to as many mora as the kanji before it, but 人々 over three mora cannot give
    both the same count, and the search then has to fall back to the unconstrained split rather
    than give up on the word."""
    alignment = find_first_complete_alignment("人々", "ひとび", "", mora_list=["ひ", "と", "び"])
    assert alignment["mora_split"] == ["ひと", "び"]
    assert alignment["jukujikun_positions"] == []


def test_youon_mora_can_be_cut_for_the_next_kanji():
    """端折る reads はし+ょる: no split at mora boundaries gives 折 a reading, so the search cuts
    inside the yōon mora and hands 折 the small kana alone."""
    alignment = find_first_complete_alignment("端折", "はしょ", "る", mora_list=["は", "しょ"])
    assert alignment["mora_split"] == ["はし", "ょ"]
    assert alignment["jukujikun_positions"] == []
    assert alignment["final_okurigana"] == "る"


def test_fewer_mora_than_kanji_is_all_jukujikun():
    alignment = find_first_complete_alignment("日本語", "にほ", "", mora_list=["に", "ほ"])
    assert alignment["kanji_matches"] == [None, None, None]
    assert alignment["jukujikun_positions"] == [0, 1, 2]
    assert alignment["mora_split"] == ["に", "ほ"]


def test_partial_alignment_explains_the_most_of_the_reading():
    """清々しい is not read by 清's listed readings, and 趙 has the reading ちょう. The alignment
    that explains most of the reading, ちょう+すがすが with the pair jukujikun, has to win over
    趙[ちょうすが]清[す]々[が], which leaves fewer kanji jukujikun but reads two of them by a
    one-mora stem and its rendaku."""
    alignment = find_first_complete_alignment(
        "趙清々", "ちょうすがすが", "しい", mora_list=["ちょ", "う", "す", "が", "す", "が"]
    )
    assert alignment["mora_split"] == ["ちょう", "すが", "すが"]
    assert alignment["jukujikun_positions"] == [1, 2]
