"""
The word `word_highlight` is asked for, brought into the furigana syntax its searches read.

The searches take the word to be a dictionary form in ordinary furigana syntax and nothing
else: a reading in brackets after each kanji run, the kana outside the brackets. A word that
comes from a note's field is not always that, and a search that is handed something else finds
nothing. `normalize_word` rewrites the shapes that can be told apart from an ordinary word with
confidence and gives every other word back as the very string it was given, which is what
happens to nearly all of them.

Noise
-----
What is not the word is taken off it: the whitespace after it (a non-breaking space and its
entity included), html tags, and a bracket with no reading in it. The space in front of a word
is furigana syntax, marking where its kanji start, and stays.

Brackets that are not cut where the kanji runs are
--------------------------------------------------
A bracket is the reading of the kanji run it follows. A note's field also holds

- one bracket after a whole expression, kana and all: 言う迄も無く[いうまでもなく], 神ゲー[かみげー]
- a bracket that reads the kana before its kanji too: スペイン 語[すぺいんご], に 対[にたい]して
- a bracket that reads kanji written before its own run without a reading: 聞き 耳[ききみみ]
- brackets cut at the wrong occurrence of a kana: 長[ながいあ]い 間[だ] for 長[なが]い 間[あいだ]

In each of them the brackets and the kana outside them still spell the word's reading in
order; only the cuts are not where the kanji runs are. So the word is cut again (`recut`). Its
runs of kana and kanji are laid against a reading of the whole word: a kana run has to stand in
the reading as it is written, hiragana and katakana alike, and each kanji run takes the kana
between two such anchors.

What the reading of the whole word is depends on what each bracket was meant to cover, which
the word does not say. For every bracket there are two answers: the kana written since the
bracket before it read themselves, as in ordinary syntax, or the bracket spells them as well.
`whole_readings` gives the reading for each combination of answers that can be meant, and
`spellings` every way such a reading spells the runs.

Which cut is taken
------------------
The same kana can occur twice in a reading, and a reading can open with the very kana that
stand before its kanji (か 家族[かぞく], where か is a particle), so that a word can be spelled
is not yet a reason to cut it that way. The kanji's own listed readings decide, by the measure
`okuri/okurigana_mix_cleaning_replacer.py` uses for the same question in texts: how many kanji a
cut leaves that no listed reading accounts for.

- A word in which every kanji run has a bracket of its own that reads it with listed readings
  is ordinary and comes back as it was given, whatever else would spell it.
- Otherwise the cut that leaves the fewest kanji unread is taken, when no other cut leaves as
  few and, for a word whose brackets all follow a kanji run, when it leaves fewer than the word
  as written does (where a kanji run without a bracket is unread).
- When the readings do not decide, the word comes back as it was given. So does a word whose
  brackets do not spell its kana at all: that is a note with a wrong reading, which is not
  this module's to repair.

Two things are never cut, because nothing in the word says where: the readings of two kanji
runs with only a bracket between them, and a kanji run after the last bracket, which no bracket
can be shown to read. A word may deliberately have furigana on some of its kanji only.

A splitter dot (阪神・淡路大震災) separates two runs like a space does and is written back where
it was. Anything else that is neither kana nor kanji, Latin letters above all, leaves the word
as it was given: no kana of the reading can be matched to it.

A text written the same way
---------------------------
The sentences come from the same notes as the words, and a sentence can have the word with the
very bracket the word field has (電子メール[でんしめーる] in the text itself). The searches read
such a text no better than such a word, and only the word as it was given matches it. So a
word that the text holds character for character is not cut again; noise comes off it all the
same.
"""

from __future__ import annotations

import re
from itertools import product
from math import prod
from typing import NamedTuple

from ..mecab_controller.kana_conv import to_hiragana
from ..okuri.okurigana_mix_cleaning_replacer import unread_kanji_count
from ..regex.kanji_furi import KANA_CHARS, KANJI_CHAR_RE
from ..utils.logger import package_logger as logger
from .use_tag_cleaning import TAG_PART_RE

# A non-breaking space, as the character or as the entity an html field stores it as
NON_BREAKING_SPACE_REC = re.compile(r"&nbsp;|\u00a0")
# A bracket that holds no reading: nothing at all, or only whitespace
EMPTY_BRACKET_REC = re.compile(r"\[\s*\]")

# The parts a word is made of, each match being one of them
WORD_PART_REC = re.compile(
    rf"""
(?P<reading>\[[^\[\]]*\])       # a bracket and what it holds
|(?P<kanji>{KANJI_CHAR_RE}+)    # a kanji run
|(?P<kana>[{KANA_CHARS}]+)      # a kana run
|(?P<gap>[\s・]+)                # what separates two runs without being read: spaces, dots
|(?P<other>.)                   # anything else: Latin letters, punctuation, a stray bracket
""",
    re.VERBOSE,
)
KANA_ONLY_REC = re.compile(rf"[{KANA_CHARS}]+")

# No reading of a kanji opens with one of these, so no cut is made in front of them: a small
# kana and the long vowel mark belong to the kana before them, and ん and っ end a mora.
CANNOT_OPEN_A_READING = frozenset("ぁぃぅぇぉゃゅょゎっんー")

# Past these a word is not an expression with a bracket in the wrong place any more, and is
# left alone rather than searched: its runs (a whole paragraph can be handed in as the word),
# the readings its brackets leave open, and the ways those spell the runs.
MAX_RUNS = 64
MAX_WHOLE_READINGS = 64
MAX_SPELLINGS = 32


class Run(NamedTuple):
    """
    A kana or kanji run of the word.

    :param text: The run as written
    :param is_kanji: Whether it is kanji, which a bracket has to read, or kana, which read
        themselves
    :param bracket: How many brackets stand before the run, which is the index of the first
        bracket after it; the number of brackets for a run after the last one
    :param after_dot: Whether a splitter dot stands between the run and the one before it
    """

    text: str
    is_kanji: bool
    bracket: int
    after_dot: bool


def without_noise(word: str) -> str:
    """Take off the word what a note's field can hold besides it.

    A word that would have nothing left is given back whole: the searches are never handed an
    empty word, and one made only of noise is no word to look for either way.
    """
    cleaned = re.sub(TAG_PART_RE, "", word)
    cleaned = NON_BREAKING_SPACE_REC.sub(" ", cleaned)
    cleaned = EMPTY_BRACKET_REC.sub("", cleaned)
    cleaned = cleaned.rstrip()
    return cleaned if cleaned.strip() else word


def split_word(word: str) -> tuple[list[Run], list[str]] | None:
    """Split the word into its runs and its brackets' readings, both in the order written.

    None for a word that cannot be laid against a reading: one with a character that is neither
    kana nor kanji, or with something other than kana in a bracket.
    """
    runs: list[Run] = []
    readings: list[str] = []
    after_dot = False
    for part in WORD_PART_REC.finditer(word):
        kind, text = part.lastgroup, part.group()
        if kind == "other":
            return None
        if kind == "gap":
            after_dot = after_dot or "・" in text
        elif kind == "reading":
            if not KANA_ONLY_REC.fullmatch(text[1:-1]):
                return None
            readings.append(text[1:-1])
        else:
            runs.append(Run(text, kind == "kanji", len(readings), after_dot))
            after_dot = False
    return runs, readings


def written_cut(runs: list[Run], readings: list[str]) -> tuple[str, ...] | None:
    """Give the reading each kanji run has as the word is written, "" for a run without one.

    None when a bracket does not follow a kanji run, which no ordinary word has.
    """
    last_run_before = {run.bracket: index for index, run in enumerate(runs)}
    for bracket in range(len(readings)):
        if bracket not in last_run_before or not runs[last_run_before[bracket]].is_kanji:
            return None
    return tuple(
        readings[run.bracket]
        if run.bracket < len(readings) and last_run_before[run.bracket] == index
        else ""
        for index, run in enumerate(runs)
        if run.is_kanji
    )


def whole_readings(runs: list[Run], readings: list[str]) -> list[tuple[str, dict[int, int]]] | None:
    """Give each reading of the whole word that its brackets can be meant to spell.

    Between two brackets stand the runs the later one may read. Either it reads the last of
    them alone and the kana before that read themselves, or it spells all of them. The first
    cannot be meant when a kanji run stands further back, which would be left with no reading
    while the word is laid against one; the second is the same reading when there are no kana.

    With each reading come the places in it that are not open to another cut, as the index of a
    kanji run and where its reading has to end: with nothing but a bracket between two kanji
    runs, only that bracket says where one reading stops and the next begins.

    None when the brackets leave more readings open than a misplaced bracket accounts for.
    """
    runs_before: list[list[int]] = [[] for _ in readings]
    kana_after_last = ""
    for index, run in enumerate(runs):
        if run.bracket < len(readings):
            runs_before[run.bracket].append(index)
        else:
            kana_after_last += run.text
    kana_before = [
        "".join(runs[i].text for i in before if not runs[i].is_kanji) for before in runs_before
    ]
    answers: list[list[bool]] = []
    for before, kana in zip(runs_before, kana_before):
        only_its_own_run = not any(runs[i].is_kanji for i in before[:-1])
        # Whether the bracket spells the kana as well: no, yes, or either
        answer = [False] if only_its_own_run else []
        if kana or not only_its_own_run:
            answer.append(True)
        answers.append(answer)
    if prod(len(answer) for answer in answers) > MAX_WHOLE_READINGS:
        return None
    whole_readings_and_fixed_ends = []
    for combination in product(*answers):
        whole = ""
        fixed_ends: dict[int, int] = {}
        for before, kana, reading, spells_the_kana in zip(
            runs_before, kana_before, readings, combination
        ):
            whole += reading if spells_the_kana else kana + reading
            # The run the bracket follows and the run after the bracket
            around_the_bracket = runs[before[-1] : before[-1] + 2] if before else []
            if [run.is_kanji for run in around_the_bracket] == [True, True]:
                fixed_ends[before[-1]] = len(whole)
        whole_readings_and_fixed_ends.append((whole + kana_after_last, fixed_ends))
    return whole_readings_and_fixed_ends


def spellings(
    runs: list[Run], reading: str, fixed_ends: dict[int, int]
) -> list[tuple[str, ...]] | None:
    """Find every way the reading spells the runs in order, as the reading of each kanji run.

    A kana run has to stand in the reading as it is written, hiragana and katakana being the
    same kana; a kanji run takes one kana or more, up to where `fixed_ends` holds it. The
    reading has to be used up, which is what keeps a kana that occurs in it twice from being
    taken for the word's at its first occurrence (勿体無い[もったいない] ends in its い).

    None when there are more ways than a misplaced bracket accounts for.
    """
    plain = to_hiragana(reading)
    found: list[tuple[str, ...]] = []
    # Where the rest of the runs cannot spell the rest of the reading, so that a kana occurring
    # many times does not have the same tail tried from every one of them
    dead_ends: set[tuple[int, int]] = set()

    def spell(index: int, start: int, cut: tuple[str, ...]) -> bool:
        """Spell the reading from `start` on with the runs from `index` on, after `cut`."""
        if (index, start) in dead_ends or len(found) > MAX_SPELLINGS:
            return False
        if index == len(runs):
            if start == len(reading):
                found.append(cut)
            return start == len(reading)
        run = runs[index]
        spelled = False
        if not run.is_kanji:
            kana = to_hiragana(run.text)
            spelled = plain.startswith(kana, start) and spell(index + 1, start + len(kana), cut)
        elif start < len(reading) and plain[start] not in CANNOT_OPEN_A_READING:
            ends = (
                [fixed_ends[index]] if index in fixed_ends else range(start + 1, len(reading) + 1)
            )
            for end in ends:
                if end > start and spell(index + 1, end, (*cut, reading[start:end])):
                    spelled = True
        if not spelled:
            dead_ends.add((index, start))
        return spelled

    spell(0, 0, ())
    return None if len(found) > MAX_SPELLINGS else found


def unread_kanji(runs: list[Run], cut: tuple[str, ...]) -> int:
    """Count the kanji the cut leaves without a reading of their own that is listed for them."""
    kanji_runs = [run.text for run in runs if run.is_kanji]
    return sum(
        unread_kanji_count(kanji, reading) if reading else len(kanji)
        for kanji, reading in zip(kanji_runs, cut)
    )


def write_cut(runs: list[Run], cut: tuple[str, ...], space_before: str) -> str:
    """Write the runs in ordinary furigana syntax, each kanji run with its reading of the cut."""
    readings = iter(cut)
    written = ""
    for run in runs:
        if run.after_dot:
            written += "・"
        if run.is_kanji:
            # The space says where the kanji that the bracket reads start
            written += f"{' ' if written else ''}{run.text}[{next(readings)}]"
        else:
            written += run.text
    return space_before + written


def recut(word: str) -> str:
    """Cut the word's reading where its kanji runs are, if it is not and it can be told where.

    The module docstring has the rules. The word comes back as it was given when it is ordinary
    already and whenever the cut cannot be decided.
    """
    if "[" not in word:
        return word
    split = split_word(word)
    if split is None:
        return word
    runs, readings = split
    if not readings or len(runs) > MAX_RUNS:
        return word
    if any(run.is_kanji and run.bracket == len(readings) for run in runs):
        # A kanji run after the last bracket has no reading and no bracket that could hold one
        return word
    possible_readings = whole_readings(runs, readings)
    if possible_readings is None:
        return word
    cuts: set[tuple[str, ...]] = set()
    for reading, fixed_ends in possible_readings:
        spelled = spellings(runs, reading, fixed_ends)
        if spelled is None or len(cuts) + len(spelled) > MAX_SPELLINGS:
            return word
        cuts.update(spelled)
    written = written_cut(runs, readings)
    if written is not None:
        cuts.discard(written)
    if not cuts:
        # Nearly every word ends here: spelled one way, the way it is written
        return word
    unread_as_written = None
    if written is not None:
        unread_as_written = unread_kanji(runs, written)
        if unread_as_written == 0:
            return word
    by_unread = sorted((unread_kanji(runs, cut), cut) for cut in cuts)
    fewest_unread, best_cut = by_unread[0]
    if len(by_unread) > 1 and by_unread[1][0] == fewest_unread:
        logger.debug("recut: '%s' can be cut in more than one way, %s", word, by_unread[:2])
        return word
    if unread_as_written is not None and fewest_unread >= unread_as_written:
        logger.debug("recut: no cut of '%s' is read better than the one written", word)
        return word
    return write_cut(runs, best_cut, word[: len(word) - len(word.lstrip())])


def normalize_word(word: str, text: str) -> str:
    """Give the word back in ordinary furigana syntax, or as it was given when it already is.

    Args:
        word (str): The word as `word_highlight` was given it, neither empty nor only spaces.
        text (str): The text the word is going to be searched for in.

    Returns:
        str: The word for the searches to take as written.
    """
    cleaned = without_noise(word)
    normalized = recut(cleaned)
    if normalized != cleaned and cleaned.strip() in text:
        # The sentence has the same bracket in the same wrong place, see the module docstring
        logger.debug("normalize_word: the text is written like '%s', not cut again", cleaned)
        normalized = cleaned
    if normalized != word:
        logger.debug("normalize_word: '%s' -> '%s'", word, normalized)
    return normalized
