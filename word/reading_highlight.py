"""Find a word where the text spells it another way than the word is given, and reads the same.

`highlight_as_written` takes the word's kanji and kana for what the text has to show. A
sentence is free to write the same word differently, and the word field of a note often does:

    見付[みつ]かる    in  見[み]つかりません        a kanji of the word is kana in the text
    罰[ばつ]          in  バツが三つ                all of it is
    お 詫[わ]び       in  御[お] 詫[わ]び           kana of the word is kanji in the text
    有様[ありさま]    in  有[あ]り 様[さま]         okurigana is in the bracket on one side
    CD                in  ＣＤ                      the width differs

`highlight_by_reading` finds those places. `word_highlight` asks it only where the word as
written was found nowhere, so it can add a highlight and never moves one.

Reading both sides
------------------
The word and the text are each read as a row of atoms, the pieces furigana syntax cannot cut:
a kanji run with the reading in its bracket, or a single character that reads as itself. A
reading is folded so that hiragana and katakana, full and half width and upper and lower case
are the same; tags and whitespace are not read at all. Neither are splitter dots, except the
text's for a kana word that is written without one (`highlight_by_reading` says why).

A place is a run of the text's atoms that reads exactly what the word reads. It starts and
ends where an atom does, since half a bracket cannot be highlighted.

The two spellings of a place have to be compatible. They are compared in cells: the place is
cut wherever an atom ends on both sides at the same point of the reading, which is the finest
cut that needs no bracket's reading split (住[すま]居[い] against 住[す]まい is the cells すま and
い: the text's 住[す] ends where the word's 住[すま] does not). In a cell, either both sides are
written alike, or one side has no kanji, or both have kanji and one side's are the other's
with some left out (見付 and 見つ). Different kanji with the same reading are a homophone and
never the word (紬 is not 紡ぎ).

How much makes a place the word
-------------------------------
A reading is weak evidence by itself, the weaker the shorter, so what else the two spellings
share decides how much more is asked:

1. A kanji is written on both sides: the place is the word.
2. Nothing differs but width, kana type or spacing: the place is the word, as any occurrence
   of a kana word is to the as-written search.
3. The text writes kanji where the word has only kana, and no kanji is shared: at least one
   character of the word has to be written out in the text too. A kana word is not found
   where the text has nothing but a reading for it (いえ is not 家[いえ]); nothing but the
   reading would say which of the kanji read that way the word is.
4. The text writes kana where the word has kanji, and no kanji is shared, so the whole place
   is kana: MeCab has to read the place as words. Three kana or more have to be whole tokens.
   Two kana have to be one token that is its own headword, which leaves out a form of another
   word (あれ of ある) and two particles side by side (もの). One kana is never the word. Four
   kana or more may also be the head or the tail of one token, which is how MeCab has a
   compound it knows (ラーメン in カップラーメン); three are too few for that (いちば begins
   いちばん).
5. Each side has a kanji the other has in kana and none is shared: not taken. No such case
   was seen, so there is nothing to say what would make one the word.

Inflection
----------
A word that ends in a kana a dictionary form ends in is also looked for without that kana,
and the okurigana check (`get_conjugated_okuri_with_mecab`) says how far the inflected word
goes, as it does for a word found as written. The check has MeCab parse the stem with the
kana after it, and the stem has two spellings here, so it is asked with the text's and then
with the word's. Where a kanji is shared and the check finds no inflection the stem alone is
highlighted, again as for a word found as written. A kana word in a place the text writes
kanji in (3) is only taken with an inflection the check accepts.

A stem that the text has in kana (4) proves nothing: the い of 言う begins いる, and the check
would read the る as its ending. For such a word MeCab's headwords are asked instead, and
only when no place was found any other way:

- First the kana path's own search, `highlight_inflected_words_with_mecab` with the word's
  bare reading. It wants one token that has the whole word for its headword and is a verb or
  an adjective as the word is, and it knows the stem of a verb MeCab does not (テンパってた).
- Then `find_by_last_headword`. The word is cut into a front and a rest; the rest has to be
  the headword of a token the text writes in kana, and the front a place that ends where the
  token starts. That finds what has neither one token nor a stem's kana to go by: a phrase
  whose last word inflects (であった of で 有[あ]る), a last word whose stem changes
  (行ってきました of 行[い]って 来[く]る), and a word MeCab takes for an auxiliary (あり of
  有[あ]る). The token's own conjugation is followed by the conditions the kana path uses.

A headword is only asked of a token the text writes in kana. Where the text writes the kanji
it gives them a reading of its own, which is compared as any other place is; MeCab's
headword for 行った is 行く or 行う by what stands around it, whatever the bracket says.
"""

import re
import unicodedata
from collections.abc import Sequence
from typing import NamedTuple

from ..mecab_controller.basic_types import MecabParsedToken
from ..mecab_controller.kana_conv import is_kana_str, to_hiragana
from ..okuri.get_conjugatable_okurigana_stem import CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH
from ..okuri.get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab
from ..okuri.mecab_common import MecabWordType, get_all_conjugation_conditions, mecab
from ..regex.kanji_furi import KANA_CHAR_RE, KANJI_CHAR_RE
from ..utils.logger import package_logger as logger
from .highlight_inflected_words_with_mecab import highlight_inflected_words_with_mecab
from .use_tag_cleaning import (
    TAG_AND_BARE_DOT_PART_RE,
    TAG_PART_RE,
    use_tag_cleaning_with_b_insertion,
)

ATOM_REC = re.compile(
    rf"""
    # A kanji run with its reading, and the space furigana syntax puts before the run. The
    # reading has to have something in it: an empty bracket says nothing about the kanji.
    (?P<furigana>\ ?(?P<kanji>{KANJI_CHAR_RE}+)\[(?P<reading>[^\]]+)\])
    # Any other bracket: [sound:...], or one that follows no kanji. It is not text.
    |(?P<bracket>\[[^\]]*\])
    # Whitespace, which is not read
    |(?P<space>&nbsp;|\s)
    # Anything else is one character that reads as itself
    |(?P<char>.)
    """,
    re.VERBOSE | re.DOTALL,
)
KANJI_CHAR_REC = re.compile(KANJI_CHAR_RE)
KANA_CHAR_REC = re.compile(KANA_CHAR_RE)
# What is not read in the word. In the text the tag storage takes the same parts out.
UNREAD_IN_WORD_REC = re.compile(TAG_AND_BARE_DOT_PART_RE)
# U+FF5E, spelled by its number because the wave dash U+301C looks the same in most fonts
FULLWIDTH_TILDE = chr(0xFF5E)

# The fewest kana a place the text writes in kana alone can have and be a kanji word, by what
# MeCab makes of it. See rule 4 in the module docstring; the numbers are from a collection's
# sentences, where every wrong place found without them had two kana or one.
MIN_KANA_AS_ONE_HEADWORD = 2
MIN_KANA_AS_WHOLE_TOKENS = 3
MIN_KANA_AS_PART_OF_A_TOKEN = 4


class Atom(NamedTuple):
    """
    A piece of furigana text that cannot be cut: a kanji run with its reading, or one character.

    :param written: What the text writes: the kanji run without its bracket, or the character
    :param reading: What that reads, folded (see `fold`); a character reads as itself
    :param start: Where the piece starts in the text, the space before a kanji run included
    :param end: Where it ends, the bracket included
    """

    written: str
    reading: str
    start: int
    end: int


class SpellingEvidence(NamedTuple):
    """
    What two compatible spellings of one reading have in common.

    :param shared_kanji: How many kanji both sides write
    :param shared_kana: How many other characters both sides write, kana mostly
    :param word_kanji_as_kana: Whether the text has only kana somewhere the word has kanji
    :param text_kanji_as_kana: Whether the word has only kana somewhere the text has kanji
    """

    shared_kanji: int
    shared_kana: int
    word_kanji_as_kana: bool
    text_kanji_as_kana: bool


class Place(NamedTuple):
    """
    A run of the text's atoms that reads as the word or its stem, spelled compatibly.

    :param first: Index of the place's first atom
    :param last: Index of the atom after its last one
    :param evidence: What the place's spelling shares with the word's
    :param by_stem: Whether it reads as the word without its last kana, an inflection to follow
    """

    first: int
    last: int
    evidence: SpellingEvidence
    by_stem: bool


def fold(text: str) -> str:
    """Make hiragana and katakana, full and half width, upper and lower case the same."""
    return to_hiragana(unicodedata.normalize("NFKC", text)).lower()


def kanji_in(written: str) -> str:
    """
    The kanji of a spelling, in order, and what furigana syntax counts as kanji with them.

    Digits are among those and come in two widths, so the width is folded here as well.
    """
    return "".join(KANJI_CHAR_REC.findall(unicodedata.normalize("NFKC", written)))


def read_atoms(text: str) -> list[Atom]:
    """Cut tag-free furigana text into its atoms. Whitespace is no atom and no part of one,
    except the space before a kanji run, which belongs to the run's span."""
    atoms: list[Atom] = []
    for match in ATOM_REC.finditer(text):
        if match.group("space"):
            continue
        if match.group("furigana"):
            written, reading = match.group("kanji"), fold(match.group("reading"))
        else:
            # A bracket reads as itself too, which no word does, so it is never part of a
            # place. It stays an atom so that nothing is found across it.
            written = match.group(0)
            reading = fold(written)
        atoms.append(Atom(written, reading, match.start(), match.end()))
    return atoms


def is_subsequence(part: str, whole: str) -> bool:
    """Whether the characters of `part` are in `whole` in the same order."""
    rest = iter(whole)
    return all(char in rest for char in part)


def compare_spellings(
    word_atoms: Sequence[Atom], text_atoms: Sequence[Atom]
) -> SpellingEvidence | None:
    """
    Say whether two runs of atoms can be two spellings of one word, and what they share.

    The runs are walked together and cut into cells where an atom ends on both sides at the
    same point of the reading; see the module docstring for what a cell may hold. Returns
    None where the runs do not read the same or a cell has other kanji on each side.
    """
    shared_kanji = shared_kana = 0
    word_kanji_as_kana = text_kanji_as_kana = False
    word_index = text_index = 0
    word_cell: list[Atom] = []
    text_cell: list[Atom] = []
    word_read = text_read = 0
    while word_index < len(word_atoms) or text_index < len(text_atoms):
        # Whichever side has read less takes its next atom, until both have read as much
        if word_read <= text_read and word_index < len(word_atoms):
            word_cell.append(word_atoms[word_index])
            word_read += len(word_atoms[word_index].reading)
            word_index += 1
        elif text_index < len(text_atoms):
            text_cell.append(text_atoms[text_index])
            text_read += len(text_atoms[text_index].reading)
            text_index += 1
        else:
            return None
        if word_read != text_read:
            continue
        if "".join(atom.reading for atom in word_cell) != "".join(
            atom.reading for atom in text_cell
        ):
            return None
        word_written = "".join(atom.written for atom in word_cell)
        text_written = "".join(atom.written for atom in text_cell)
        word_kanji, text_kanji = kanji_in(word_written), kanji_in(text_written)
        if fold(word_written) == fold(text_written):
            shared_kanji += len(word_kanji)
            shared_kana += len(word_written) - len(word_kanji)
        elif word_kanji and text_kanji:
            if not (
                is_subsequence(word_kanji, text_kanji) or is_subsequence(text_kanji, word_kanji)
            ):
                return None
            shared_kanji += min(len(word_kanji), len(text_kanji))
        elif word_kanji:
            word_kanji_as_kana = True
        else:
            # Two spellings that read the same and are not written alike differ by a kanji,
            # so this is the text's
            text_kanji_as_kana = True
        word_cell, text_cell = [], []
    if word_cell or text_cell:
        return None
    return SpellingEvidence(shared_kanji, shared_kana, word_kanji_as_kana, text_kanji_as_kana)


def find_places(
    needle_atoms: Sequence[Atom], text_atoms: Sequence[Atom], by_stem: bool
) -> list[Place]:
    """Find every run of the text's atoms that reads as the needle and is spelled compatibly."""
    needle = "".join(atom.reading for atom in needle_atoms)
    if not needle:
        return []
    text_reading = "".join(atom.reading for atom in text_atoms)
    # Where in the reading each atom starts; a place can only start and end at one of these
    atom_at: dict[int, int] = {}
    read = 0
    for index, atom in enumerate(text_atoms):
        atom_at[read] = index
        read += len(atom.reading)
    atom_at[read] = len(text_atoms)
    places: list[Place] = []
    begin = text_reading.find(needle)
    while begin != -1:
        end = begin + len(needle)
        if begin in atom_at and end in atom_at:
            first, last = atom_at[begin], atom_at[end]
            evidence = compare_spellings(needle_atoms, text_atoms[first:last])
            if evidence:
                places.append(Place(first, last, evidence, by_stem))
        begin = text_reading.find(needle, begin + 1)
    return places


def is_bracket(atom: Atom) -> bool:
    """Whether the atom is a bracket that is no reading, such as a sound tag."""
    return len(atom.written) > 1 and atom.written.startswith("[")


class WrittenTokens(NamedTuple):
    """
    MeCab's reading of the text as it is written, the brackets and spaces left out.

    :param atom_offsets: Where each atom starts in the written text, and after the last of
        them where that text ends
    :param spans: `(start, end, token)` for each token, in the same offsets
    """

    atom_offsets: list[int]
    spans: list[tuple[int, int, MecabParsedToken]]


def mecab_tokens(text_atoms: Sequence[Atom]) -> WrittenTokens | None:
    """
    Have MeCab read the text as it is written and say where each of its tokens is.

    Returns None when the tokens do not spell the text, which is MeCab having dropped or
    rewritten something; there is then nothing to hold a place against.
    """
    written = ""
    atom_offsets: list[int] = []
    for atom in text_atoms:
        atom_offsets.append(len(written))
        if is_bracket(atom):
            # MeCab's own cleaning drops [sound:...], so the bracket is given as a space
            # instead, which separates words and comes back in no token
            written += " "
        else:
            # The same cleaning turns the full-width tilde into a plain one; doing it first
            # keeps the tokens comparable with what they were made from
            written += atom.written.replace(FULLWIDTH_TILDE, "~")
    atom_offsets.append(len(written))
    spans: list[tuple[int, int, MecabParsedToken]] = []
    at = 0
    for token in mecab.translate(written):
        while written.startswith(" ", at):
            at += 1
        if not token.word or not written.startswith(token.word, at):
            logger.debug("MeCab's token '%s' is not what the text has at %s", token.word, at)
            return None
        spans.append((at, at + len(token.word), token))
        at += len(token.word)
    return WrittenTokens(atom_offsets, spans)


def kana_place_is_words(place: Place, reading_length: int, tokens: WrittenTokens) -> bool:
    """Decide whether MeCab reads a place the text writes in kana as words: rule 4 of the
    module docstring."""
    start, end = tokens.atom_offsets[place.first], tokens.atom_offsets[place.last]
    covering = [span for span in tokens.spans if span[0] < end and span[1] > start]
    if not covering:
        return False
    starts_a_token = covering[0][0] == start
    ends_a_token = covering[-1][1] == end
    if starts_a_token and ends_a_token:
        if reading_length >= MIN_KANA_AS_WHOLE_TOKENS:
            return True
        token = covering[0][2]
        return (
            reading_length >= MIN_KANA_AS_ONE_HEADWORD
            and len(covering) == 1
            and fold(token.headword) == fold(token.word)
        )
    return (
        reading_length >= MIN_KANA_AS_PART_OF_A_TOKEN
        and len(covering) == 1
        and (starts_a_token or ends_a_token)
    )


def from_last_kanji(atoms: Sequence[Atom]) -> Sequence[Atom]:
    """Give the atoms from the last one that has a kanji on, or all of them without one."""
    for index in range(len(atoms) - 1, -1, -1):
        if kanji_in(atoms[index].written):
            return atoms[index:]
    return atoms


def inflection_end(
    text_atoms: Sequence[Atom], place: Place, word_stem_atoms: Sequence[Atom]
) -> int | None:
    """
    Find where the inflection of a word found by its stem ends.

    Returns the index of the atom after the inflection, or None when the okurigana check
    finds none in the kana that follow the stem.
    """
    tail_atoms: list[Atom] = []
    for atom in text_atoms[place.last :]:
        if not KANA_CHAR_REC.fullmatch(atom.written):
            break
        tail_atoms.append(atom)
    if not tail_atoms:
        return None
    tail = to_hiragana("".join(atom.written for atom in tail_atoms))
    # The check parses the stem and the kana after it as a text of their own, and takes the
    # token the stem ends in for the inflecting word. A phrase in front of that word only
    # gives MeCab more to cut wrongly, and a token that starts before the stem's end is not
    # trusted unless it is a verb; so the stem is given from its last kanji on, which is what
    # the as-written search gives the check too (the word's last kanji).
    #
    # The stem has two spellings here, and MeCab may read the inflection in either: the text's
    # is tried first, then the word's. なかった after と言ったら is an auxiliary to MeCab, which
    # the check does not take for the word's own ending; 無かった, as と 言[い]ったら 無[な]い
    # spells it, is the adjective.
    tried: list[str] = []
    for stem_atoms in (text_atoms[place.first : place.last], word_stem_atoms):
        last_word = from_last_kanji(stem_atoms)
        written = "".join(atom.written for atom in last_word)
        if written in tried:
            continue
        tried.append(written)
        okuri_result, _ = get_conjugated_okuri_with_mecab(
            word=written,
            reading="".join(atom.reading for atom in last_word),
            maybe_okuri=tail,
            okuri_prefix="word",
        )
        logger.debug(
            "Inflection of '%s' in '%s': result '%s', okurigana '%s'",
            written,
            tail,
            okuri_result.result,
            okuri_result.okurigana,
        )
        if okuri_result.result != "no_okuri" and okuri_result.okurigana:
            # Every atom of the tail is one kana, so the okurigana's length counts atoms
            return place.last + len(okuri_result.okurigana)
    return None


def is_kana_place(place: Place) -> bool:
    """Whether the text writes the whole place in kana where the word has a kanji."""
    evidence = place.evidence
    return (
        not evidence.shared_kanji
        and evidence.word_kanji_as_kana
        and not evidence.text_kanji_as_kana
    )


def end_of_word_at(
    place: Place,
    text_atoms: Sequence[Atom],
    word_stem_atoms: Sequence[Atom],
    tokens: WrittenTokens | None,
) -> int | None:
    """
    Decide whether a place is the word, by the rules of the module docstring.

    Returns the index of the atom after the word, its inflection included, or None when the
    place is not taken for the word.
    """
    evidence = place.evidence
    if evidence.shared_kanji:
        # Rule 1. Without an inflection the check accepts, the stem is still the word
        if place.by_stem:
            return inflection_end(text_atoms, place, word_stem_atoms) or place.last
        return place.last
    if not evidence.word_kanji_as_kana and not evidence.text_kanji_as_kana:
        # Rule 2. A stem written alike is what the as-written search looked for already,
        # with the checks an inflected kana word needs
        return None if place.by_stem else place.last
    if evidence.word_kanji_as_kana and evidence.text_kanji_as_kana:
        # Rule 5
        return None
    if evidence.text_kanji_as_kana:
        # Rule 3
        if not evidence.shared_kana:
            return None
        if place.by_stem:
            return inflection_end(text_atoms, place, word_stem_atoms)
        return place.last
    # Rule 4. The kana of a stem say nothing; MeCab's headwords are asked for an inflected
    # word instead, see highlight_by_reading
    if place.by_stem or tokens is None:
        return None
    reading_length = sum(len(atom.reading) for atom in text_atoms[place.first : place.last])
    return place.last if kana_place_is_words(place, reading_length, tokens) else None


def front_can_lead_to_headword(place: Place, tokens: WrittenTokens) -> bool:
    """
    Decide whether a place found for the front of the word can be the start of the word, the
    token after it having the rest of the word for headword.

    The headword is most of the evidence, so the front needs less than a word of its own
    would: a kanji shared, or a start where MeCab starts a token too (で of である, not the で
    that ends まで). What rules 3 and 5 refuse is refused here as well.
    """
    evidence = place.evidence
    if evidence.shared_kanji:
        return True
    if evidence.text_kanji_as_kana and (evidence.word_kanji_as_kana or not evidence.shared_kana):
        return False
    start = tokens.atom_offsets[place.first]
    return any(span[0] == start for span in tokens.spans)


def find_by_last_headword(
    word_atoms: Sequence[Atom],
    text_atoms: Sequence[Atom],
    tokens: WrittenTokens,
    word_type: MecabWordType,
) -> list[tuple[int, int]]:
    """
    Find the word where its last word is a kana token of the text that has it for headword.

    The word is cut in two at each of its atoms in turn, the longer rest first: the rest has
    to be the headword of a token the text writes in kana, and the front, if there is one, a
    place that ends where the token starts. The highlight goes on over the tokens that are
    the token's conjugation, by the conditions the kana path uses.

    Returns `(first atom, atom after the last)` for each place of the first cut that has any.
    """
    atom_at = {offset: index for index, offset in enumerate(tokens.atom_offsets)}
    all_tokens = [token for _start, _end, token in tokens.spans]
    for cut in range(len(word_atoms)):
        front_atoms, rest_atoms = word_atoms[:cut], word_atoms[cut:]
        rest_reading = "".join(atom.reading for atom in rest_atoms)
        if len(rest_reading) < 2:
            # One kana is the ending alone, and no word
            break
        front_places = find_places(front_atoms, text_atoms, by_stem=False)
        found: list[tuple[int, int]] = []
        for token_index, (start, end, token) in enumerate(tokens.spans):
            if fold(token.headword) != rest_reading or start not in atom_at or end not in atom_at:
                continue
            first = atom_at[start]
            if not all(
                KANA_CHAR_REC.fullmatch(atom.written) for atom in text_atoms[first : atom_at[end]]
            ):
                # A kana headword is that of a kana token as a rule. Should MeCab have one for
                # a token with kanji in it, the text has a reading for those kanji that the
                # headword says nothing about
                continue
            if front_atoms:
                fronts = [
                    place
                    for place in front_places
                    if place.last == first and front_can_lead_to_headword(place, tokens)
                ]
                if not fronts:
                    continue
                first = fronts[0].first
            # The tokens after it that are its conjugation, as far as they are whole atoms
            for next_start, next_end, next_token in tokens.spans[token_index + 1 :]:
                if (
                    next_start != end
                    or next_end not in atom_at
                    or not get_all_conjugation_conditions(next_token, all_tokens, word_type)[0]
                ):
                    break
                end = next_end
            found.append((first, atom_at[end]))
        if found:
            return found
    return []


def bare_reading(word: str) -> str:
    """
    Give the word as its kana alone, each kanji run replaced by its reading as written.

    The kana type is kept (テンパる of 聴牌[テンパ]る): the kana path spells the stem of a verb
    MeCab does not know the way it is given.
    """
    # group 1: the reading in the bracket of a kanji run
    reading = re.sub(rf"{KANJI_CHAR_RE}+\[([^\]]*)\]", r"\1", UNREAD_IN_WORD_REC.sub("", word))
    return re.sub(r"\s", "", reading)


def highlight_by_reading(text: str, word: str) -> str:
    """
    Highlight the word where the text reads as it does and spells it compatibly.

    See the module docstring for the rule. Returns the text with the places in <b> tags, or
    exactly as it was given when there is none.
    """
    if not text or not word:
        return text
    word_atoms = read_atoms(UNREAD_IN_WORD_REC.sub("", word))
    if not word_atoms or any(atom.written.startswith("[") for atom in word_atoms):
        # Nothing to read, or a bracket that is no reading: not a word that occurs in a text
        return text
    word_reading = "".join(atom.reading for atom in word_atoms)
    # The tags are stored away as on the furigana paths, and the splitter dots with them: a
    # word with kanji runs across a dot of the text there too, and a word written with a dot
    # says that it does. A kana word written without one keeps to the text as it stands, as
    # on the as-written search: kana words are short, and between two katakana words the dot
    # is what keeps one from running into the other (トラ is not in テスト・ライブ). There the
    # dots stay in the text and read as themselves, which nothing in a word does. The spaces
    # stay either way, because the one before a kanji run is highlighted with the run.
    runs_across_dots = "・" in word or any(kanji_in(atom.written) for atom in word_atoms)
    tag_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
        text, part_regex=TAG_AND_BARE_DOT_PART_RE if runs_across_dots else TAG_PART_RE
    )
    text_atoms = read_atoms(tag_free_text)

    last_atom = word_atoms[-1]
    # Only okurigana the word writes out is taken off: a noun's bracket can end in the same
    # kana (春[はる]) and has no stem
    inflects = (
        len(word_reading) > 1
        and not kanji_in(last_atom.written)
        and last_atom.reading in CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH
    )
    places = find_places(word_atoms, text_atoms, by_stem=False)
    if inflects:
        whole_word_starts = {place.first for place in places}
        places += [
            place
            for place in find_places(word_atoms[:-1], text_atoms, by_stem=True)
            # The stem of a place the whole word was found at is that place again
            if place.first not in whole_word_starts
        ]
        places.sort(key=lambda place: place.first)
    logger.debug(
        "highlight_by_reading: word reads '%s', inflects: %s, %s places to judge",
        word_reading,
        inflects,
        len(places),
    )

    # MeCab is only asked where a place needs its word for it (rule 4)
    needs_mecab = any(is_kana_place(place) and not place.by_stem for place in places)
    tokens = mecab_tokens(text_atoms) if needs_mecab else None
    highlights: list[tuple[int, int]] = []
    taken_until = 0
    for place in places:
        if place.first < taken_until:
            continue
        end = end_of_word_at(place, text_atoms, word_atoms[:-1], tokens)
        if end is None:
            continue
        logger.debug("Taking atoms %s to %s for the word: %s", place.first, end, place.evidence)
        highlights.append((text_atoms[place.first].start, text_atoms[end - 1].end))
        taken_until = end

    if not highlights and inflects and any(kanji_in(atom.written) for atom in word_atoms):
        kana_word = bare_reading(word)
        if kana_word and is_kana_str(kana_word):
            logger.debug("No place found, asking the kana path for '%s'", kana_word)
            by_kana_path = highlight_inflected_words_with_mecab(text, kana_word)
            if by_kana_path != text:
                return by_kana_path
        tokens = tokens or mecab_tokens(text_atoms)
        if tokens:
            word_type: MecabWordType = "i_adjective" if last_atom.reading == "い" else "verb"
            for first, end in find_by_last_headword(word_atoms, text_atoms, tokens, word_type):
                logger.debug("Taking atoms %s to %s for the word, by its last headword", first, end)
                highlights.append((text_atoms[first].start, text_atoms[end - 1].end))
    if not highlights:
        return text

    result = tag_free_text
    inserted = 0
    for start, end in highlights:
        # The indexes are those of the text as it is now, with the earlier <b> pairs in it
        increment_tag_indexes(start + inserted, end + inserted)
        result = (
            result[: start + inserted]
            + "<b>"
            + result[start + inserted : end + inserted]
            + "</b>"
            + result[end + inserted :]
        )
        inserted += len("<b></b>")
    return restore_tags(result)
