"""Keeps the not-yet-converted suites out of a package-wide pytest run.

Each of these still carries the hand-rolled harness whose `test(test_name, text, expected)`
helper pytest reads as a test function with three missing fixtures. As each suite is converted
to parametrised cases, drop its line here; when the list is empty, delete this file.
"""

collect_ignore = [
    "okuri/okurigana_mix_cleaning_tests.py",
    "word/word_highlight_tests.py",
]
