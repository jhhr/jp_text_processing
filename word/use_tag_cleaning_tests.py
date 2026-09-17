"""Cases for `apply_tag_fixes`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/word/use_tag_cleaning_tests.py

Pass `--log-cli-level=debug` to see what a case logged; pytest captures the package logger on
its own, so nothing here has to turn logging on.

A case's id says how the `<b>` span and the surrounding tag overlap, which is what each case is
about.
"""

import pytest

from .use_tag_cleaning import apply_tag_fixes


CASES = [
    # An opening tag right before <b>, closed within the b span
    pytest.param(
        "<k><b> 何[なん]</k>でも<k> 無[な]い</b></k>",
        "<b><k> 何[なん]</k>でも<k> 無[な]い</k></b>",
        id="tag opened before <b>, closed inside the span",
    ),
    # A tag opened within the b span and closed after it, with text in between
    pytest.param(
        "<k> 其[そ]れ</k>には<b><k> 優劣[ゆうれつ]</k>を<k> 付[つ]け</b> 難[がた]い</k>。",
        "<k> 其[そ]れ</k>には<b><k> 優劣[ゆうれつ]</k>を<k> 付[つ]け</k></b><k> 難[がた]い</k>。",
        id="tag opened inside the span, closed after it",
    ),
    # A tag opened before <b> and closed within it, with text in between
    pytest.param(
        "<k> 何[なん]<b>でも</k> 無[な]い</b>",
        "<k> 何[なん]</k><b><k>でも</k> 無[な]い</b>",
        id="tag opened before the span with text between, closed inside",
    ),
    # Whole tags within the b span, and b spans within a tag, are left alone
    pytest.param(
        "<k> 何[なん]<b>でも</b> 無[な]い</k>",
        "<k> 何[なん]<b>でも</b> 無[な]い</k>",
        id="span inside a tag is left alone",
    ),
    pytest.param(
        "<b><k> 何[なん]</k>でも</b>",
        "<b><k> 何[なん]</k>でも</b>",
        id="whole tag inside the span is left alone",
    ),
]


@pytest.mark.parametrize("unfixed_text, expected", CASES)
def test_apply_tag_fixes(unfixed_text: str, expected: str):
    assert apply_tag_fixes(unfixed_text) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
