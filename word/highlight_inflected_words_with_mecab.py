"""Find a kana word in a text in the forms it inflects to, with MeCab's reading of the text.

`word_highlight` comes here with a word written in kana only, after looking for it as it is
spelled and not finding it. MeCab is given the text without its tags, spaces and furigana
brackets, and an occurrence is looked for at each token it cuts the text into. Hiragana and
katakana are the same kana throughout: グレちゃった is ぐれる.

Where an occurrence starts
--------------------------

1. A token whose headword is the word (はしっ of はしって is はしる). The token has to
   inflect the way the word does: a verb for a word ending in an う-row kana and an adjective
   for one ending in い, or what MeCab calls an auxiliary (助動詞), which is its name for the
   job a word does and not for how it inflects. ある is an auxiliary to it after で and じゃ.

   A word can be several tokens: a phrase (ピントがずれる, である), or a verb MeCab does not
   know and cuts in pieces (ぼっ/た/くら/れ/た). Then a token's headword is the end of the word,
   and the text before that token, from the start of a token on, is the rest of it: ずれ in
   ピントがずれています, あっ in であった, くら in ぼったくられた. A word MeCab knows as one
   word is not put together like that. は and いない spell a form of はいる and are not one.
2. A token whose headword is the word's stem, with a conjugation of the word after it. This is
   how MeCab cuts a verb it does not know when it cuts it at the stem: バズ/っ/た. The stem has
   to be two kana or more. One kana and a conjugation is に before ない and て before いる.

What a conjugation of the word is comes from the okurigana progression of its inflection
class, which the word's last kana gives: the godan row, the adjective for い, and for る the
godan row plus the ichidan forms when the stem ends in an い- or え-row kana, as an ichidan
stem does. する's forms are left out: they are conjugations of する, which rule 1 finds as
the last word of a phrase (びっくりした), and with them ミスした would be a form of ミスる.

Where an occurrence ends
------------------------

After a token found by rule 1, with each following token that conjugates it, as
`get_all_conjugation_conditions` judges for the word's type: ている, the passive and the
causative, ない, た and the like are the word, a particle or the copula is not.

After a stem found by rule 2 MeCab's tokens are not the word's (バズった gives っ the headword
く), so the conjugation is read off the text against the progression and the highlight ends
where the longest one does, inside a token if need be (バズって of バズってる). Only when that
is the end of a token are the tokens after it asked as above.

The text that comes back
------------------------

The highlight is cut out of the text by position. MeCab does not hand back every character it
was given (～ comes back as ~), so nothing of the output is made from its tokens: without the
`<b>` tags the output is the input.
"""

from collections.abc import Iterator
from typing import NamedTuple

from ..all_types.main_types import PartOfSpeech
from ..mecab_controller.basic_types import MecabParsedToken
from ..mecab_controller.basic_types import PartOfSpeech as MecabPartOfSpeech
from ..mecab_controller.kana_conv import to_hiragana
from ..okuri.get_conjugatable_okurigana_stem import CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH
from ..okuri.mecab_common import (
    MecabWordType,
    get_all_conjugation_conditions,
    get_word_type_from_mecab_token,
    mecab,
)
from ..okuri.okurigana_dict import (
    E_I_ENDING_KANA,
    GODAN_FORM_VERB_STARTINGS,
    POSSIBLE_OKURIGANA_PROGRESSION_DICT,
)
from ..utils.logger import package_logger as logger
from .use_tag_cleaning import (
    TAG_SPACE_AND_FURIGANA_PART_RE,
    use_tag_cleaning_with_b_insertion,
)

# The shortest stem a form is recognised by. One kana and a conjugation spells too many other
# words (あれ, おれ, かれ, みたい) and too many particles followed by one (に/ない, か/って).
MIN_STEM_LENGTH = 2

# The inflection classes whose forms belong to する and not to a word that merely ends in る
SURU_PARTS_OF_SPEECH: tuple[PartOfSpeech, ...] = ("vs", "vs-i", "vs-s")


class InflectingWord(NamedTuple):
    """
    The kana word to find, as the rules need it. Everything is in hiragana.

    :param dictionary_form: the word, a godan verb's noun form turned back into the verb
    :param stem: the dictionary form without its last kana, which is the part that inflects
    :param conjugations: the inflection classes whose okurigana progression the word can
        follow after its stem; empty for a word that does not inflect
    :param word_type: what a MeCab token of the word is, None for a word that does not inflect
    """

    dictionary_form: str
    stem: str
    conjugations: list[PartOfSpeech]
    word_type: MecabWordType | None


class ParsedText(NamedTuple):
    """
    MeCab's reading of a text, with where each token stands in it.

    :param tokens: the tokens, in the order of the text
    :param spans: for each token, where it starts and ends in the text
    :param folded: the text in hiragana, to compare kana with whatever the script
    """

    tokens: list[MecabParsedToken]
    spans: list[tuple[int, int]]
    folded: str


class Occurrence(NamedTuple):
    """
    An occurrence of the word, as far as the rule that found it can tell.

    :param end: where in the text the part the rule is sure of ends
    :param continues_as: the type of word whose conjugating tokens can still follow that part,
        None when nothing can
    :param rule: the rule's name, for the log
    """

    end: int
    continues_as: MecabWordType | None
    rule: str


def walk_okurigana_progression(
    part_of_speech: PartOfSpeech, okurigana: str
) -> Iterator[tuple[int, dict]]:
    """Walk a part of speech's okurigana progression over the text, one character at a time.

    Yields how much of the text the progression has read and the node that reading reached,
    stopping where the progression cannot continue.
    """
    progression = POSSIBLE_OKURIGANA_PROGRESSION_DICT.get(part_of_speech)
    for char_index, char in enumerate(okurigana):
        progression = progression.get(char) if progression else None
        if not progression:
            return
        yield char_index + 1, progression


def conjugation_length(parts_of_speech: list[PartOfSpeech], text: str) -> int:
    """
    Length of the longest conjugation the text starts with, 0 when it starts with none.

    The longest one is the one the word actually got: った of ったら is not where the form ends.
    """
    longest = 0
    for part_of_speech in parts_of_speech:
        for okuri_len, node in walk_okurigana_progression(part_of_speech, text):
            if node.get("is_last"):
                longest = max(longest, okuri_len)
            if not node.get("る", {}).get("is_last"):
                continue
            # The causative, the passive and the potential turn the word into an ichidan verb
            # of its own (バズる -> バズらせる) and the dict lists only a few of that verb's own
            # forms, らせた not among them. Where the okurigana so far plus る is one of them,
            # the rest of the text goes on as the ichidan okurigana it is.
            for extra_len, extra_node in walk_okurigana_progression("v1", text[okuri_len:]):
                if extra_node.get("is_last"):
                    longest = max(longest, okuri_len + extra_len)
    return longest


def inflecting_word(base_form_word: str) -> InflectingWord:
    """Work out from a kana word's last kana how it inflects."""
    word = to_hiragana(base_form_word)
    stem, ending = word[:-1], word[-1]
    conjugations: list[PartOfSpeech] = []
    if ending in CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH:
        conjugations = CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH[ending]
    elif ending in GODAN_FORM_VERB_STARTINGS:
        # A godan verb in its noun form (バズり) is found as the verb it is the form of, whose
        # dictionary form is what MeCab has for a headword
        ending = GODAN_FORM_VERB_STARTINGS[ending]
        conjugations = CONJUGATABLE_LAST_OKURI_PART_OF_SPEECH.get(ending, [])
        word = stem + ending
    word_type: MecabWordType | None = None
    if any(part_of_speech.startswith("v") for part_of_speech in conjugations):
        word_type = "verb"
    elif "adj-i" in conjugations:
        word_type = "i_adjective"
    # A word in る is a godan verb or an ichidan one, and nothing in its kana says which,
    # except that an ichidan stem ends in an い- or え-row kana
    conjugations = [
        part_of_speech
        for part_of_speech in conjugations
        if part_of_speech not in SURU_PARTS_OF_SPEECH
        and (part_of_speech != "v1" or stem[-1:] in E_I_ENDING_KANA)
    ]
    return InflectingWord(word, stem, conjugations, word_type)


def parse_text(text: str) -> ParsedText | None:
    """
    Have MeCab read the text and place its tokens in it.

    MeCab hands the tokens back in order and all but verbatim: the one thing it is known to
    rewrite is ～, to ~, one character for one. So a token stands for as many characters of the
    text as it has. None when the tokens do not add up to the text, which is MeCab (or the
    corrections made to its output) having dropped or made up a character: there is then no
    telling where a token stands.
    """
    tokens = list(mecab.translate(text))
    spans: list[tuple[int, int]] = []
    cursor = 0
    for token in tokens:
        spans.append((cursor, cursor + len(token.word)))
        cursor += len(token.word)
    if cursor != len(text):
        logger.debug("MeCab's tokens are %s characters, the text is %s", cursor, len(text))
        return None
    return ParsedText(tokens, spans, to_hiragana(text))


def inflects_as(token: MecabParsedToken, word: InflectingWord) -> bool:
    """
    Whether a token with the word for a headword can be the word.

    MeCab's 助動詞 says what a word does in the sentence, not how it inflects: ある after で is
    one and conjugates as the verb ある all the same.
    """
    return (
        get_word_type_from_mecab_token(token) == word.word_type
        or token.part_of_speech == MecabPartOfSpeech.bound_auxiliary
    )


def is_one_word_to_mecab(word: InflectingWord) -> bool:
    """Whether MeCab, given the word alone, reads it as a single word that inflects."""
    tokens = mecab.translate(word.dictionary_form)
    return (
        len(tokens) == 1
        and to_hiragana(tokens[0].headword) == word.dictionary_form
        and inflects_as(tokens[0], word)
    )


def headword_occurrence(parsed: ParsedText, word: InflectingWord, index: int) -> Occurrence | None:
    """
    Rule 1: the word begins at this token when a token here has it for a headword.

    For a word of one token that is this token. A word of several has its last word for the
    headword of a later token, and before that token the text spells the rest of the word
    from this token on. Only that last token is asked for its headword: the ones before it do
    not inflect, and MeCab cuts them differently from text to text (な/の/で or なの/で).

    A word MeCab knows as one word is not looked for in several tokens. Its forms are its own
    and not those of a shorter word it ends in: はいる is は and いる to the eye, and はいない is
    no form of it.
    """
    start = parsed.spans[index][0]
    for head_index in range(index, len(parsed.tokens)):
        written_before = parsed.folded[start : parsed.spans[head_index][0]]
        if len(written_before) >= len(word.dictionary_form) or not word.dictionary_form.startswith(
            written_before
        ):
            return None
        head = parsed.tokens[head_index]
        if written_before + to_hiragana(head.headword) != word.dictionary_form or not inflects_as(
            head, word
        ):
            continue
        if written_before and is_one_word_to_mecab(word):
            return None
        return Occurrence(parsed.spans[head_index][1], word.word_type, "headword")
    return None


def stem_token_occurrence(
    parsed: ParsedText, word: InflectingWord, index: int
) -> Occurrence | None:
    """
    Rule 2: the word begins at this token when its headword is the word's stem and a
    conjugation of the word follows.

    MeCab does not know every verb; for an unknown one it splits the word into a noun-ish stem
    plus the conjugation, so the stem token's headword is the word's stem. The stem alone is
    no evidence though - はし is the noun 橋 as much as it is the stem of はしる - so the text
    after the token has to go on as one of the conjugations possible for this word.
    """
    token = parsed.tokens[index]
    if len(word.stem) < MIN_STEM_LENGTH or to_hiragana(token.headword) != word.stem:
        return None
    token_end = parsed.spans[index][1]
    okurigana_len = conjugation_length(word.conjugations, parsed.folded[token_end:])
    if not okurigana_len and index + 1 < len(parsed.tokens):
        # MeCab can also read the conjugation as a verb of its own (バズ/られ/た, where られ is
        # the verb られる), leaving the progression nothing to walk. An auxiliary verb that
        # counts as this word's conjugated okurigana is the same evidence that the stem is the
        # word's - and only a verb is: バズらしい is the noun plus らしい.
        next_token = parsed.tokens[index + 1]
        if (
            get_word_type_from_mecab_token(next_token) == "verb"
            and get_all_conjugation_conditions(next_token, parsed.tokens, word.word_type)[0]
        ):
            okurigana_len = len(next_token.word)
    if not okurigana_len:
        return None
    return Occurrence(token_end + okurigana_len, word.word_type, "stem token")


def conjugated_end(parsed: ParsedText, occurrence: Occurrence) -> tuple[int, int]:
    """
    Where the occurrence ends with what conjugates it, and the token to look on from.

    The tokens after the part the rule was sure of belong to the occurrence for as long as
    they conjugate it. A part that ends inside a token ends the occurrence there: it was read
    off the text because the tokens are not the word's, and what is left of that token is the
    tail of the word's own conjugation, which cannot begin the next occurrence.
    """
    end = occurrence.end
    index = next(
        (index for index, (start, _) in enumerate(parsed.spans) if start >= end),
        len(parsed.tokens),
    )
    if index and parsed.spans[index - 1][1] > end:
        return end, index
    while (
        index < len(parsed.tokens)
        and occurrence.continues_as
        and get_all_conjugation_conditions(
            parsed.tokens[index], parsed.tokens, occurrence.continues_as
        )[0]
    ):
        end = parsed.spans[index][1]
        index += 1
    # The token that ends the occurrence is looked at as the start of the next one: two can
    # sit next to each other (はしってはしって)
    return end, index


def find_inflected_word(text: str, base_form_word: str) -> list[tuple[int, int]]:
    """
    Find where a kana word occurs in a text, inflected forms included.

    :param text: the text as MeCab is to read it: no tags, no whitespace, no furigana brackets
    :param base_form_word: the word in its dictionary form, in kana
    :return: where each occurrence starts and ends in the text, in order; see the module
        docstring for what an occurrence is
    """
    # A one-kana word has no stem to inflect, and its headword is spelled as the word is, which
    # the caller has looked for already
    if not text or len(base_form_word) < 2:
        return []
    word = inflecting_word(base_form_word)
    parsed = parse_text(text)
    if parsed is None:
        return []
    logger.debug(
        "Looking for '%s' as a %s with stem '%s' and conjugations %s",
        word.dictionary_form,
        word.word_type,
        word.stem,
        word.conjugations,
    )
    found: list[tuple[int, int]] = []
    index = 0
    while index < len(parsed.tokens):
        occurrence = headword_occurrence(parsed, word, index) or stem_token_occurrence(
            parsed, word, index
        )
        if occurrence is None:
            index += 1
            continue
        start = parsed.spans[index][0]
        end, index = conjugated_end(parsed, occurrence)
        logger.debug(
            "Found '%s' by rule '%s', as far as '%s' with its conjugation",
            text[start : occurrence.end],
            occurrence.rule,
            text[start:end],
        )
        found.append((start, end))
    return found


def highlight_inflected_words_with_mecab(text: str, base_form_word: str) -> str:
    """
    Wrap each inflected occurrence of a kana word in the text in <b> tags.

    :param text: the text to look in, with its furigana and html
    :param base_form_word: the word in its dictionary form, in kana
    :return: the text with the occurrences highlighted; the text itself when there is none
    """
    if not text or not base_form_word:
        return text
    # Clean the html tags from the text temporarily, and the whitespace with them as mecab wipes
    # that out as well. The furigana brackets go with them: a reading is not the word occurring
    # in the text, so MeCab must not read one as a word of the sentence.
    html_and_space_free_text, increment_indexes_for_b, restore_tags_and_spaces, _ = (
        use_tag_cleaning_with_b_insertion(text, part_regex=TAG_SPACE_AND_FURIGANA_PART_RE)
    )
    occurrences = find_inflected_word(html_and_space_free_text, base_form_word)
    if not occurrences:
        return text
    result = html_and_space_free_text
    for count, (start, end) in enumerate(occurrences):
        # The positions are the text's, which has none of the b tags the earlier occurrences got
        start += count * len("<b></b>")
        end += count * len("<b></b>")
        increment_indexes_for_b(start, end)
        result = f"{result[:start]}<b>{result[start:end]}</b>{result[end:]}"
    logger.debug("Final highlighted result before restoring tags/spaces: '%s'", result)

    result = restore_tags_and_spaces(result)
    logger.debug("Restored html tags and spaces result: '%s'", result)

    return result
