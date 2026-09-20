"""Cases for the mora alignment search, with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/kana/mora_alignment_tests.py

The search itself is covered through kana_highlight_tests; what is here is the machinery under
it that those cases cannot see.
"""

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
