"""Cases for `use_text_part_storage`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/word/use_text_part_storage_tests.py

Pass `--log-cli-level=debug` to see what a case logged; pytest captures the package logger on
its own, so nothing here has to turn logging on.

Text that is stored and restored with no edits in between has to come back exactly as it went
in, so a case is just the text, and its id says what kind of text it is.
"""

import pytest

from .use_text_part_storage import use_text_part_storage

CASES = [
    pytest.param(
        "<div>「<k> 糞[クソ]</k><k> 程[ほど]</k><k> 詰[つま]らん</k>。<k> 何[なん]</k>でも<k>"
        " 無[な]い</k> 女[おんな]の 会話[かいわ]。」</div><div>「<k> 其[そ]れ</k>、"
        " 特大[とくだい]ブーメランじゃねぇ？」</div>",
        id="furigana in nested div and k tags",
    ),
]


@pytest.mark.parametrize("text", CASES)
def test_restores_unedited_text_unchanged(text: str):
    cleaned_text, _increment_indexes, restore_parts, _indexes = use_text_part_storage(text)
    assert restore_parts(cleaned_text) == text


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
