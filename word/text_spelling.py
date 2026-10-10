"""
The word spelled the way the text spells it.

`word_highlight` finds a word by its characters: the word's kanji have to be the text's. Some
things are written in either of two ways that say the same, and a note's word and its sentence
need not have picked the same one. So a word that is not found as it is written is looked for
once more, with those things written as the text has them (`spelled_as_in_text`). The search
itself stays what it is: the respelled word goes down the same paths, and a reading the text
gives still has to be the word's.

Only a word that was not found is respelled. A text that has the word as written has said where
it is, and looking for another spelling as well could only lose that place or add one.

Numbers
-------
A number is the same number in digits, half-width or full-width, and in kanji numerals: ７つ
and 七つ, ２０ and 二十, １１９番 and 百十九番. `number_to_kanji` says which numerals a run of
digits is. Where the text has the digits and the word those numerals the word gets the text's
digits, and a word in digits gets the numerals of a text that has only those.

A number is all of its digits and all of its numerals. 1 is not the 1 of 10 or of 119, 十 is
not the 十 of 二十, and 二十 is not a 2 and a 10 standing somewhere in the text. Digits joined
by a decimal point or by the comma between thousands are one number too, and one this module
does not convert. 万 and the units above it are the exception that writing makes: they are
written out after digits as well (1万, ３００万), so the numerals before one are a number of
their own, as are the numerals after it.

The patterns of the search hold a digit run of the word to the same rule, and take a digit in
either width (`whole_number_pattern`), so that a word in digits is not found inside a longer
number of the text, respelled or not. One thing the patterns cannot see: the searches take the
splitter dots out of the text before they match, so the 2 and the 3 of ２・３ 人 stand side by
side there and neither is found as a number of its own.

None of this is about the reading. ７[なな] has to agree with the word's reading like any
kanji, and a bare ２０ has no reading to agree or disagree, so that its digits are all there
is to compare.

Repeated kanji
--------------
A kanji said twice is written twice or with the repeater: 駄駄 and 駄々. The furigana
splitting keeps the two apart, 駄々[だだ] staying one token and 駄駄[だだ] becoming two, so
the word is only found in the spelling it has. Where the text has the pair the other way, the
word gets the text's. That holds across what stands between the two kanji in the text, a
reading or a space: the 主主 of 民主[みんしゅ]主義[しゅぎ] is the 主々 of a word field that
writes 民主々義.
"""

import re

from ..kanji.number_to_kanji import KANJI_NUMERALS, SUB_MYRIAD_UNITS, number_to_kanji
from ..regex.kanji_furi import KANJI_RANGES
from ..utils.logger import package_logger as logger
from .use_tag_cleaning import FURIGANA_PART_RE, TAG_PART_RE

DIGITS = "0-9０-９"
# What joins the groups of digits of one number: a decimal point, the comma between thousands
SEPARATORS = ".．,，"
# The numerals a number below 万 is written with. One of them beside a run of them makes it
# another number, which 万 and the units above it do not; see the module docstring
NUMERALS = "".join(KANJI_NUMERALS.values()) + SUB_MYRIAD_UNITS
# As many digits as number_to_kanji has units for, 千京. A longer run is no number anyone
# writes in numerals, and converting it takes time that grows with its length
MAX_DIGITS = 20

# Where no number goes on to the left, and to the right: no digit there, and no separator with
# a digit on its far side
NOT_AFTER_NUMBER_RE = rf"(?<![{DIGITS}])(?<![{DIGITS}][{SEPARATORS}])"
NOT_BEFORE_NUMBER_RE = rf"(?![{SEPARATORS}]?[{DIGITS}])"
# A run of digits that is a number by itself
WHOLE_NUMBER_REC = re.compile(
    rf"{NOT_AFTER_NUMBER_RE}[{DIGITS}]{{1,{MAX_DIGITS}}}{NOT_BEFORE_NUMBER_RE}"
)
# (1) A number as it is written in digits, with the separators inside it
WRITTEN_NUMBER_REC = re.compile(rf"([{DIGITS}]+(?:[{SEPARATORS}][{DIGITS}]+)*)")
DIGIT_REC = re.compile(rf"[{DIGITS}]")
# A kanji said twice: (1) the kanji, (2) the repeater or the kanji again
REPEATED_KANJI_REC = re.compile(rf"([{KANJI_RANGES}])(々|\1)")


def whole_number_pattern(word_part: str) -> str:
    """Escape a part of the word for a pattern, its numbers matching only whole numbers.

    A number of the word is found where the text has that number and nothing more of one
    around it, with each digit in either width. Everything else is escaped as it is.
    """

    def either_width(digit: re.Match[str]) -> str:
        # int reads a full-width digit like a half-width one
        value = int(digit.group())
        return f"[{value}{chr(ord('０') + value)}]"

    # Split with a capturing group: the numbers are the odd parts
    parts = WRITTEN_NUMBER_REC.split(word_part)
    return "".join(
        f"{NOT_AFTER_NUMBER_RE}{DIGIT_REC.sub(either_width, re.escape(part))}{NOT_BEFORE_NUMBER_RE}"
        if index % 2
        else re.escape(part)
        for index, part in enumerate(parts)
    )


def number_of_its_own_rec(numerals: str) -> re.Pattern[str]:
    """Give the pattern that finds the numerals where they are not part of a longer number."""
    return re.compile(rf"(?<![{NUMERALS}]){re.escape(numerals)}(?![{NUMERALS}])")


def numbers_as_in_text(word: str, bare_text: str) -> str:
    """Write the word's numbers in digits or in numerals, whichever the text has them in.

    :param word: The word, in furigana syntax
    :param bare_text: The text without its tags and readings
    :return: The word, the same string when the text has none of its numbers the other way
    """
    # The numerals of each number the text has in digits, with the digits as written
    text_digits: dict[str, str] = {}
    for number in WHOLE_NUMBER_REC.finditer(bare_text):
        text_digits.setdefault(number_to_kanji(number.group()), number.group())

    def as_numerals(number: re.Match[str]) -> str:
        numerals = number_to_kanji(number.group())
        if numerals in text_digits or not number_of_its_own_rec(numerals).search(bare_text):
            # The text has the number in digits, which match in either width, or not at all
            return number.group()
        return numerals

    respelled = WHOLE_NUMBER_REC.sub(as_numerals, word)
    for numerals, digits in text_digits.items():
        respelled = number_of_its_own_rec(numerals).sub(digits, respelled)
    return respelled


def repeated_kanji_as_in_text(word: str, bare_text: str) -> str:
    """Write the word's repeated kanji twice or with 々, whichever the text has them in.

    :param word: The word, in furigana syntax
    :param bare_text: The text without its tags and readings
    :return: The word, the same string when the text has none of its pairs the other way
    """
    # The text's two kanji can be two furigana words, with a space between them
    text_kanji = re.sub(r"\s", "", bare_text)

    def as_in_text(pair: re.Match[str]) -> str:
        kanji, repeat = pair.groups()
        other_spelling = kanji + (kanji if repeat == "々" else "々")
        return other_spelling if other_spelling in text_kanji else pair.group()

    return REPEATED_KANJI_REC.sub(as_in_text, word)


def spelled_as_in_text(word: str, text: str) -> str:
    """Give the word with what the text spells another way spelled as the text has it.

    :param word: The word, in furigana syntax
    :param text: The text the word is searched for in
    :return: The word to search for instead, or the same string when nothing in it is spelled
        another way in the text
    """
    bare_text = re.sub(rf"{TAG_PART_RE}|{FURIGANA_PART_RE}", "", text)
    respelled = repeated_kanji_as_in_text(numbers_as_in_text(word, bare_text), bare_text)
    if respelled != word:
        logger.debug("spelled_as_in_text: '%s' -> '%s'", word, respelled)
    return respelled
