"""Cases for the parts `highlight_inflected_words_with_mecab` is made of, run with pytest from
`anki_shared/`:

    python -m pytest jp_text_processing/word/highlight_inflected_words_with_mecab_tests.py

Pass `--log-cli-level=debug` to see what a case logged; pytest captures the package logger on
its own, so nothing here has to turn logging on.

What counts as an occurrence of a word is pinned end to end in `word_highlight_tests.py`, in
the "Kana only" cases. The cases here are about what those rules stand on: how a kana word is
taken to inflect, how far a conjugation reaches in a text, and that an occurrence is a place
in the text as it was given.
"""

import pytest

from ..all_types.main_types import PartOfSpeech
from ..okuri.mecab_common import MecabWordType, mecab
from .highlight_inflected_words_with_mecab import (
    conjugation_length,
    find_inflected_word,
    highlight_inflected_words_with_mecab,
    inflecting_word,
)

# The expected value is (dictionary form, stem, inflection classes, word type)
INFLECTING_WORD_CASES = [
    pytest.param("そぐう", ("そぐう", "そぐ", ["v5u"], "verb"), id="godan verb"),
    pytest.param("ださい", ("ださい", "ださ", ["adj-i"], "i_adjective"), id="adjective"),
    pytest.param(
        "ぐれる",
        ("ぐれる", "ぐれ", ["v5r", "v1"], "verb"),
        id="verb in る with an え-row stem is godan or ichidan",
    ),
    pytest.param(
        "いじる",
        ("いじる", "いじ", ["v5r", "v1"], "verb"),
        id="verb in る with a voiced い-row stem is godan or ichidan",
    ),
    pytest.param(
        "へばる",
        ("へばる", "へば", ["v5r"], "verb"),
        id="verb in る with a stem no ichidan verb has is godan",
    ),
    pytest.param(
        "グレる",
        ("ぐれる", "ぐれ", ["v5r", "v1"], "verb"),
        id="katakana is read as hiragana",
    ),
    pytest.param(
        "バズり",
        ("ばずる", "ばず", ["v5r"], "verb"),
        id="godan verb's noun form is the verb",
    ),
    pytest.param(
        "びっくりする",
        ("びっくりする", "びっくりす", ["v5r"], "verb"),
        id="する verb gets none of する's own forms",
    ),
    pytest.param("ピント", ("ぴんと", "ぴん", [], None), id="word that does not inflect"),
]


@pytest.mark.parametrize("word, expected", INFLECTING_WORD_CASES)
def test_inflecting_word(
    word: str, expected: tuple[str, str, list[PartOfSpeech], MecabWordType | None]
):
    assert tuple(inflecting_word(word)) == expected


CONJUGATION_LENGTH_CASES = [
    pytest.param(["v5r"], "ったね", 2, id="conjugation followed by something else"),
    pytest.param(["v5r"], "ったらね", 3, id="the longest of two conjugations"),
    pytest.param(["v5r"], "がすごい", 0, id="no conjugation"),
    pytest.param(["v5r"], "", 0, id="nothing after the stem"),
    pytest.param(["v5r"], "らせられたね", 5, id="causative passive goes on as an ichidan verb"),
    pytest.param(["v5r", "v1"], "てない", 1, id="ichidan form of a verb that may be ichidan"),
    pytest.param(["v5r"], "てない", 0, id="ichidan form of a verb that is godan"),
    pytest.param(["v5u"], "わない術", 3, id="negative"),
    pytest.param(["v5k"], "き勝ち", 1, id="continuative form"),
    pytest.param(["adj-i"], "さ、", 1, id="adjective's noun in さ"),
    pytest.param([], "った", 0, id="word that does not inflect"),
]


@pytest.mark.parametrize("parts_of_speech, text, expected", CONJUGATION_LENGTH_CASES)
def test_conjugation_length(parts_of_speech: list[PartOfSpeech], text: str, expected: int):
    assert conjugation_length(parts_of_speech, text) == expected


def marked(text: str, occurrences: list[tuple[int, int]]) -> str:
    """The text with each occurrence in brackets, so that a case reads as a text."""
    for start, end in reversed(occurrences):
        text = f"{text[:start]}【{text[start:end]}】{text[end:]}"
    return text


# The text is as MeCab gets it: no tags, no spaces, no furigana
FIND_CASES = [
    pytest.param("はしってはしって", "はしる", "【はしって】【はしって】", id="two occurrences"),
    pytest.param("はしをわたる", "はしる", "はしをわたる", id="no occurrence"),
    pytest.param("", "はしる", "", id="empty text"),
    pytest.param("はしった", "", "はしった", id="empty word"),
    pytest.param("食べた", "る", "食べた", id="one-kana word"),
    # MeCab hands ～ back as ~ and ｡ as it is; either way the places are the text's
    pytest.param(
        "ああ～其のチクられた子～何だっけ？",
        "ちくる",
        "ああ～其の【チクられた】子～何だっけ？",
        id="character MeCab rewrites before the occurrence",
    ),
    pytest.param(
        "のに～～！おちゃらけてないのに～～！",
        "おちゃらける",
        "のに～～！【おちゃらけてない】のに～～！",
        id="characters MeCab rewrites before the occurrence, stem read off the text",
    ),
]


@pytest.mark.parametrize("text, word, expected", FIND_CASES)
def test_find_inflected_word(text: str, word: str, expected: str):
    assert marked(text, find_inflected_word(text, word)) == expected


def test_tokens_that_do_not_add_up_to_the_text_find_nothing(monkeypatch: pytest.MonkeyPatch):
    """
    MeCab handing back fewer characters than it got is not something a text is known to cause,
    so it is made to here. The word is then not placed by guessing: nothing is found.
    """
    text = "きのうサボったよ"
    assert find_inflected_word(text, "さぼる") == [(3, 7)]
    all_tokens = list(mecab.translate(text))
    monkeypatch.setattr(mecab, "translate", lambda _text: all_tokens[1:])
    assert find_inflected_word(text, "さぼる") == []


# Texts with what the highlighting takes out and puts back around the word: tags, spaces,
# furigana, a line break, a sound tag, and characters MeCab does not hand back as given
SAME_TEXT_CASES = [
    pytest.param("ああ～<k> 其[そ]の</k>チクられた 子[こ]～", "ちくる", id="tilde, tags, furigana"),
    pytest.param("サボった\nサボった", "さぼる", id="line break between two occurrences"),
    pytest.param("[sound:a.mp3]サボった　よ～", "さぼる", id="sound tag and a wide space"),
    pytest.param("ほら，サボってる｡", "さぼる", id="half-width and full-width punctuation"),
]


@pytest.mark.parametrize("text, word", SAME_TEXT_CASES)
def test_highlight_leaves_the_text_as_given(text: str, word: str):
    highlighted = highlight_inflected_words_with_mecab(text, word)
    assert "<b>" in highlighted
    assert highlighted.replace("<b>", "").replace("</b>", "") == text


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
