import re

from ..all_types.main_types import OkuriResults
from ..kana.kana_highlight import WithTagsDef, kana_highlight
from ..mecab_controller.kana_conv import is_kana_str, to_hiragana, to_katakana
from ..okuri.get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab
from ..regex.kanji_furi import KANJI_RANGES
from ..utils.logger import package_logger as logger
from .highlight_inflected_words_with_mecab import (
    highlight_inflected_words_with_mecab,
)
from .reading_highlight import highlight_by_reading
from .reading_variants import (
    ReadingAgreement,
    WordKanjiReading,
    last_kanji_agreement,
    reading_agreement,
)
from .text_spelling import spelled_as_in_text, whole_number_pattern
from .use_tag_cleaning import (
    FURIGANA_PART_RE,
    SPLITTER_DOT_RE,
    TAG_AND_BARE_DOT_PART_RE,
    TAG_AND_DOT_PART_RE,
    TAG_PART_RE,
    use_tag_cleaning_with_b_insertion,
)
from .word_normalizer import normalize_word

KANJI_AND_MAYBE_FURIGANA_AND_OKURIGANA_RE = (
    rf"([\d々{KANJI_RANGES}ヶヵ]+)(?:\[([^\]]*?)\])?([ぁ-ん]*)$"
)
# The last kanji of a word that was split into one reading per kanji: (1) the kanji, which is
# anything a kanji run can hold, or a number with all its digits, which the splitting keeps
# under one reading, (2) the repeater sharing its bracket, if there is one, and (3) the
# reading. A bare repeater, which only a degenerate word has, is taken as (1).
LAST_KANJI_FURIGANA_RE = rf"(\d+|[々{KANJI_RANGES}ヶヵ])(々?)(?:\[([^\]]*?)\])?$"

CONSECUTIVE_FURI_WORD_RE = (
    rf"(?: ([\d々{KANJI_RANGES}ヶヵ]+)\[([^\]]*?)\])(?:"
    rf" ([\d々{KANJI_RANGES}ヶヵ]+)\[([^\]]*?)\])"
)
FURIGANA_TOKEN_RE = rf"([\d々{KANJI_RANGES}ヶヵ]+)\[([^\]]*?)\]"
KANJI_RUN_AND_MAYBE_FURIGANA_RE = rf"([\d々{KANJI_RANGES}ヶヵ]+)(\[[^\]]*\])?"
KANJI_RUN_CHAR_RE = rf"[\d々{KANJI_RANGES}ヶヵ]"
LATIN_CHAR_RE = "[A-Za-zＡ-Ｚａ-ｚ]"
# (1) A run of Latin letters of either width, and the reading the word may have on it
LATIN_RUN_AND_MAYBE_FURIGANA_RE = rf"({LATIN_CHAR_RE}+)(?:\[[^\]]*\])?"
# A katakana word a word ends in: (1) the last kanji with its reading, (2) the okurigana that
# kanji may have, (3) the katakana. The long vowel mark is katakana here though ァ-ン stops
# short of it: without it 神[かみ]ゲー has no such tail and is searched for bracket and all,
# which only a text cut into the same brackets has.
KATAKANA_SUFFIX_RE = rf"({KANJI_RUN_CHAR_RE}\[[^\]]*?\])([ぁ-ん]*)([ァ-ンー]+)$"


def kanji_run_with_maybe_furigana(escaped_kanji: str, run_may_continue: bool = True) -> str:
    """Create a pattern for a kanji run of the word that gives no reading for it.

    The text can carry furigana the word was written without (an Anki word field often has
    none where the sentence field does). The kanji then match a text run that has a bracket
    too, so the bracket stays inside the highlight instead of being cut off from the kanji it
    belongs to. The word can also be only part of that run, whose one reading cannot be split
    without the word's own reading, so the rest of the run is taken along with the bracket.
    A run the text wrote no reading on is matched as far as the word goes, as before.

    An inflecting word's okurigana follows its last kanji directly, so a run that goes on past
    that kanji is not the word (出来事 is not 出来る) and run_may_continue is False for it. Only
    this path needs the rule; a word that gives its own readings has them to disagree with the
    text's. The run may still begin before the word: a compound ending in the word's kanji is
    a genuine ambiguity (花見 / 見る).
    """
    run_tail = rf"{KANJI_RUN_CHAR_RE}*" if run_may_continue else ""
    bare_kanji = escaped_kanji if run_may_continue else rf"{escaped_kanji}(?!{KANJI_RUN_CHAR_RE})"
    return rf"(?:{KANJI_RUN_CHAR_RE}*{escaped_kanji}{run_tail}\[[^\]]*\]|{bare_kanji})"


def replace_hiragana_in_pattern(text: str) -> str:
    # Replace each hiragana character with a katanana or hiragana option
    def replace_hiragana(match: re.Match) -> str:
        char = match.group(0)
        katakana_char = to_katakana(char)
        return rf"(?:{char}|{katakana_char})"

    return re.sub(r"[ぁ-ん]", replace_hiragana, text)


def word_part_pattern(word_part: str) -> str:
    """Create a pattern for what the word has outside its kanji runs and their readings.

    Kana match in either script, and a number left here by the splitting only a whole number.

    Latin letters can carry a reading the way kanji do, ＡＢＣ[えいびーしー] and
    ｎｍ[なのめーとる], in the word or in the text. They match with a reading after them and
    without one, whether the word gives them one or not, and the two readings are not held
    against each other: the letters are the word, and how a reading spells them out is not
    settled (えい and えー).

    A reading in the text is the reading of the whole run of letters before it, and with the
    readings out of the comparison nothing else says so. So the word's letters take a bracket
    along only as all of its run, and inside a run that has one they are not found at all:
    ｍ[めーとる] is not the ｍ of ｃｍ[せんち], nor Ｋ the end of ＮＨＫ[えぬえいちけい] with
    the highlight closing between the letters and their reading. In letters the text gives
    no reading the word is found as far as it goes, as it always was.
    """

    def letters_pattern(letters: str) -> str:
        whole_run_with_reading = rf"(?<!{LATIN_CHAR_RE}){letters}\[[^\]]*\]"
        not_in_a_run_with_reading = rf"{letters}(?!{LATIN_CHAR_RE}*\[)"
        return rf"(?:{whole_run_with_reading}|{not_in_a_run_with_reading})"

    # Split with a capturing group: the letters are the odd parts, and their reading goes
    return "".join(
        letters_pattern(re.escape(part))
        if index % 2
        else replace_hiragana_in_pattern(whole_number_pattern(part))
        for index, part in enumerate(re.split(LATIN_RUN_AND_MAYBE_FURIGANA_RE, word_part))
    )


def make_word_pattern(word: str, followed_by_okurigana: bool = False) -> str:
    """Create a regex pattern matching the word, with or without the text's furigana.

    A kanji run the word already gives a reading for is matched as written; one it does not
    also matches the reading the text has for it, together with the space furigana syntax
    puts before the kanji and the rest of the text's kanji run that reading covers. Where the
    word has okurigana after its last kanji, the text's run has to end at that kanji.

    Digits are part of a kanji run, and a number among them is the text's whole number or
    nothing: ２ does not match in １２, whatever else the run it stands in may take along.
    """
    # Remove first space
    word = re.sub(r"^ ", "", word)
    pattern_parts: list[str] = [r"\s?"]
    cursor = 0
    kanji_matches = list(re.finditer(KANJI_RUN_AND_MAYBE_FURIGANA_RE, word))
    for index, match in enumerate(kanji_matches):
        literal_prefix = word[cursor : match.start()]
        if literal_prefix:
            pattern_parts.append(word_part_pattern(literal_prefix))
            pattern_parts.append(r"\s?")
        kanji, kanji_furigana = match.group(1), match.group(2)
        if kanji_furigana:
            pattern_parts.append(whole_number_pattern(kanji))
            pattern_parts.append(replace_hiragana_in_pattern(re.escape(kanji_furigana)))
        else:
            run_ends_word = followed_by_okurigana and index == len(kanji_matches) - 1
            pattern_parts.append(
                kanji_run_with_maybe_furigana(
                    whole_number_pattern(kanji), run_may_continue=not run_ends_word
                )
            )
        cursor = match.end()
    literal_suffix = word[cursor:]
    if literal_suffix:
        pattern_parts.append(word_part_pattern(literal_suffix))
    return "".join(pattern_parts)


def make_furigana_agnostic_pattern(word: str) -> tuple[str, list[WordKanjiReading]]:
    """Create a regex pattern that captures furigana sections for variant checking.

    The generated pattern keeps kanji and separators strict, but allows the furigana
    inside brackets to vary. Captured furigana values can then be validated via
    reading_agreement (rendaku/small-tsu/vowel-change, etc.), which is given each kanji as
    the word reads it; those come back in the order of the pattern's furi_ groups.

    A text written without furigana has neither the brackets nor the space before a kanji, so
    both are optional; a bracket that is there still has to agree with the word's reading.

    A number of the word, which the splitting leaves as one token under one reading, matches
    the same number of the text in digits of either width and no part of a longer one.
    """
    word = re.sub(r"^ ", "", word)
    expected_readings: list[WordKanjiReading] = []
    pattern_parts: list[str] = [r"\s?"]
    cursor = 0
    for idx, match in enumerate(re.finditer(FURIGANA_TOKEN_RE, word)):
        literal_prefix = word[cursor : match.start()]
        if literal_prefix:
            without_space = literal_prefix.rstrip(" ")
            if without_space:
                pattern_parts.append(word_part_pattern(without_space))
            if without_space != literal_prefix:
                pattern_parts.append(r"\s?")
        kanji = match.group(1)
        expected_readings.append(
            WordKanjiReading(
                kanji=kanji,
                reading=to_hiragana(match.group(2)),
                begins_word=not word[: match.start()].strip(),
            )
        )
        pattern_parts.append(rf"{whole_number_pattern(kanji)}(?:\[(?P<furi_{idx}>[^\]]+)\])?")
        cursor = match.end()
    literal_suffix = word[cursor:]
    if literal_suffix:
        pattern_parts.append(word_part_pattern(literal_suffix))
    return "".join(pattern_parts), expected_readings


def furigana_captures_match_readings(
    match: re.Match,
    expected_readings: list[WordKanjiReading],
) -> bool:
    """Validate captured furigana readings against expected readings with variants.

    A kanji the text gave no reading for has nothing to disagree with the word about.
    """
    for idx, expected in enumerate(expected_readings):
        captured = match.group(f"furi_{idx}")
        if captured is None:
            continue
        if reading_agreement(expected, to_hiragana(captured)) == "none":
            return False
    return True


def preserve_small_counter_kana(text: str) -> str:
    # Keep Japanese counter kana in katakana form after to_hiragana conversion.
    return text.replace("ゕ", "ヵ").replace("ゖ", "ヶ")


def split_furi_text_into_individual_kanji_furigana(furi_text: str) -> str:
    """Splits a furigana text into individual kanji-furigana parts with kana_highlight.

    Args:
        furi_text (str): The furigana text to split.

    Returns:
        str: The split furigana text.
    """
    furi_text = kana_highlight(
        text=furi_text,
        kanji_to_highlight="",
        return_type="furigana",
        with_tags_def=WithTagsDef(
            with_tags=True,
            merge_consecutive=False,
            onyomi_to_katakana=False,
            include_suru_okuri=False,
        ),
    )
    # Replace tags so that we now have all kanji furigana split except for repeaters
    furi_text = re.sub(r"</?(?:on|kun|juk|mix|oku)>", "", furi_text)
    return furi_text


def kanji_run_continuations(text: str) -> list[bool]:
    """Tell for each kanji of the text whether the run it stands in goes on after it.

    Splitting the text gives every kanji a bracket of its own, so the runs the text was
    written with are only visible in the text itself. The kanji keep their order through the
    splitting, so the answer is looked up by counting them.
    """
    bare_text = re.sub(rf"{TAG_AND_BARE_DOT_PART_RE}|{FURIGANA_PART_RE}", "", text)
    return [
        bool(re.match(KANJI_RUN_CHAR_RE, bare_text[index + 1 : index + 2]))
        for index, char in enumerate(bare_text)
        if re.match(KANJI_RUN_CHAR_RE, char)
    ]


def kanji_index_at(text: str, position: int) -> int:
    """Count the kanji before the position, the tags, dots and readings not counted."""
    before = re.sub(rf"{TAG_AND_BARE_DOT_PART_RE}|{FURIGANA_PART_RE}", "", text[:position])
    return len(re.findall(KANJI_RUN_CHAR_RE, before))


def merge_consecutive_furigana(split_furi_text: str, text: str) -> str:
    """Merges consecutive kanji-furigana parts back into a single furigana text.

    Only what the splitting took apart is put back: two furigana words the text was written
    with a space between are not one run and stay apart, so a part of the text the highlight
    did not touch comes back as it was written.

    Args:
        split_furi_text (str): The split furigana text.
        text (str): The text as it was written, whose kanji runs say what may merge.
    Returns:
        str: The merged furigana text.
    """
    run_continues_after_kanji = kanji_run_continuations(text)
    pattern = re.compile(CONSECUTIVE_FURI_WORD_RE)
    search_start = 0
    while match := pattern.search(split_furi_text, search_start):
        first_kanji = match.group(1)
        first_furi = match.group(2)
        second_kanji = match.group(3)
        second_furi = match.group(4)
        last_kanji_index = kanji_index_at(split_furi_text, match.start(1) + len(first_kanji) - 1)
        if run_continues_after_kanji[last_kanji_index : last_kanji_index + 1] != [True]:
            # The text has these two as words of its own; the second one can still have a
            # part of its own run after it
            logger.debug(
                "Not merging '%s' and '%s': the text has them apart", first_kanji, second_kanji
            )
            search_start = match.start(3) - 1
            continue
        merged_kanji = first_kanji + second_kanji
        merged_furi = first_furi + second_furi
        merged_text = f" {merged_kanji}[{merged_furi}]"
        split_furi_text = (
            split_furi_text[: match.start(0)] + merged_text + split_furi_text[match.end(0) :]
        )
        # The merged part can have another part of the same run after it
        search_start = match.start(0)
    return split_furi_text


def adnominal_na_okuri(word_okurigana: str, maybe_okuri: str) -> str:
    """Give the okurigana an i-adjective's な form has in the text, if the text has that form.

    大きい's adnominal form is 大きな and its stem 大き is the word as much as 大きく is, so the
    stem is taken; the な is not, except when the word to match was written with it (大きいな).
    Returns "" when the text does not have the word's な form.
    """
    word_ends_in_na = word_okurigana.endswith("な")
    dictionary_okuri = word_okurigana[:-1] if word_ends_in_na else word_okurigana
    stem = dictionary_okuri[:-1]
    # Only an i-adjective with a stem of its own has a な form; 良[い]い's な is the particle
    if not stem or not dictionary_okuri.endswith("い"):
        return ""
    if not maybe_okuri.startswith(f"{stem}な"):
        return ""
    return f"{stem}な" if word_ends_in_na else stem


def word_highlight(text: str, word: str) -> str:
    """
    Takes a japanese word or phrase in dictionary form and finds any inflected occurrences of
    it in the given text. The word and text is expected to be in furigana syntax; with brackets
    containing the reading of the kanji words. A word written without furigana still matches a
    text that has it, but then the text's reading cannot be split, so a word that covers only
    part of a kanji run highlights the whole run and its reading:

    word_highlight("私は 日本語[にほんご]を", "語") --> "私は<b> 日本語[にほんご]</b>を"
    word_highlight("私は 日本語[にほんご]を", "語[ご]") --> "私は 日本[にほん]<b> 語[ご]</b>を"

    Furigana syntax in text includes a space before the word begins, e.g "この 家[いえ]は" with the
    exception that the beginning of the string can omit the space, e.g "家[いえ]で 居[い]る".

    The word is then expected to be in the same syntax, e.g "家[いえ]". but the matched occurrence
    in the should include the space before the word. For example:

    word_highlight("この 家[いえ]は", "家[いえ]") --> "この<b> 家[いえ]</b>は"
    word_highlight("家[いえ]で 居[い]る", "家[いえ]") --> "<b>家[いえ]</b>で 居[い]る"

    Inflected forms are found for verbs up and including auxiliary verbs like いる, させる, せる
    negation forms like ない, させない, せない, な but not すぎる, すぎない.
    For example:
    word_highlight("私は 食[た]べている", "食[た]べる") --> "私は<b> 食[た]べている</b>"
    word_highlight("食[た]べさせるな!", "食[た]べる") --> "<b>食[た]べさせる</b>な!"

    For adjectives, the inflected forms are found up to and including the い form, but not
    the な form except when な is included in the word to match.
    For example:
    word_highlight("これ、 大[おお]きすぎない？", "大[おお]きい") --> "これ、 <b> 大[おお]き</b>すぎない？"
    word_highlight("大[おお]きな 家[いえ]", "大[おお]きい") --> "<b>大[おお]き</b>な 家[いえ]"
    word_highlight("大[おお]きな 家[いえ]", "大[おお]きいな") --> "<b>大[おお]きな</b> 家[いえ]"
    word_highlight("安[やす]くて 良[い]いな～", "安[やす]い") --> "<b>安[やす]くて</b> 良[い]いな～"
    word_highlight("高[たか]いでも 良[よ]かろう", "良[い]い") --> "高[たか]いでも<b> 良[よ]かろう</b>"

    A text the word does not occur in comes back exactly as it was given.

    Args:
        text (str): The input text where the word needs to be highlighted.
        word (str): The word to highlight.

    Returns:
        str: The text with <b> tags around each occurrence of the word.
    """
    logger.debug("word_highlight: text='%s', word='%s'", text, word)
    if not text or not word or not word.strip():
        return text

    word = normalize_word(word, text)
    result = highlight_as_written(text, word)
    if bold_count(result) > bold_count(text):
        return result
    # Looking for the word can regroup the text's furigana on the way, which is the price of
    # a highlight and nothing a text without one should pay. So it is the text as given that
    # is searched for another spelling of the word, and that comes back when there is none.
    return highlight_by_reading(text, word)


def bold_count(text: str) -> int:
    """Count the highlights in the text, to tell whether one was added to it."""
    return len(re.findall(r"<b>", text))


def highlight_as_written(text: str, word: str) -> str:
    """Highlight the word where the text writes it with the characters the word is given in.

    The word's kanji have to be the text's kanji and its kana the text's kana, hiragana and
    katakana taken as the same. Which of the two has furigana is free, and so is how the
    word is inflected; see word_highlight for what counts as an occurrence.

    A word that is not found so is looked for once more spelled as the text spells it, where
    the two spellings are the same word by rule: a number in digits or in kanji numerals, a
    kanji said twice written twice or with 々. text_spelling has the rules.

    Returns the text with the occurrences in <b> tags. Without one the text can still come
    back with its furigana grouped differently, which the caller has to tell apart.
    """
    result = highlight_spelling(text, word)
    if bold_count(result) > bold_count(text):
        return result
    respelled = spelled_as_in_text(word, text)
    if respelled == word:
        return result
    return highlight_spelling(text, respelled)


def highlight_spelling(text: str, word: str) -> str:
    """Highlight the word where the text has it in the one spelling the word is given in.

    This is the search highlight_as_written describes, and it returns what that one does.
    """
    # A splitter dot the word is written with (ヘレン・ケラー, 報・連・相) is no more a character
    # to match than one in the text is. The searches below store the text's dots away before
    # matching, so the word goes into them without its own; with them it could match nothing.
    word_has_splitter_dot = "・" in word
    if word_has_splitter_dot:
        word = re.sub(SPLITTER_DOT_RE, "", word)
        logger.debug("Word without its splitter dots: '%s'", word)
        if not word.strip():
            return text

    if is_kana_str(word):
        logger.debug("Word is kana only, use highlight_inflected_words_with_mecab")
        # This is either a simple case or a complex one needing inflection matching
        # First try a simple regex match
        pattern = make_word_pattern(word)
        logger.debug("Using pattern: %s", pattern)

        # Remove tags from the text temporarily, so that a word a tag splits is found here too
        # and not only on the mecab path below. Only the tags are stored: the pattern matches
        # the space before a word, and the furigana brackets have to stay for the readings in
        # them to be recognized as readings.
        # This is the one search where the text's dots stay as well, unless the word was
        # written with one itself. A kana word is short and turns up across a dot by accident
        # (トラ in テスト・ライブ), where the dot is what keeps two words apart; a word that has
        # its own dot says that it runs across one.
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text, part_regex=TAG_AND_BARE_DOT_PART_RE if word_has_splitter_dot else TAG_PART_RE
        )
        logger.debug("html_free_text for matching: '%s'", html_free_text)
        furigana_spans = [m.span() for m in re.finditer(FURIGANA_PART_RE, html_free_text)]

        # re.sub reports every match's position in its input, which has none of the b tags the
        # earlier matches got, so their length is added on to get the current position.
        b_tags_inserted = 0

        def replace_match(match: re.Match) -> str:
            nonlocal b_tags_inserted
            if any(start < match.start(0) < end for start, end in furigana_spans):
                # A reading inside [...] is not the word occurring in the text, so a kana word
                # must not match one
                return match.group(0)
            increment_tag_indexes(match.start(0) + b_tags_inserted, match.end(0) + b_tags_inserted)
            b_tags_inserted += len("<b></b>")
            return f"<b>{match.group(0)}</b>"

        result = re.sub(pattern, replace_match, html_free_text)

        if result != html_free_text:
            # If that worked, return the result
            logger.debug("Intermediate result with <b> tags: '%s'", result)
            return restore_tags(result)

        # Otherwise, use MeCab to find inflected forms
        return highlight_inflected_words_with_mecab(text, word)

    # Strip trailing katakana suffix after furigana (with optional hiragana okuri)
    # before to_hiragana so it is not mistaken for inflectable okurigana.
    # Only after a kanji's reading: the two paths that put the suffix back are the ones a
    # kanji with a reading leads to. Letters with a reading (Ｔ[てぃー]シャツ) take the path
    # that matches the word as it stands, which would look for the letters alone.
    katakana_suffix_after_furi_match = re.search(KATAKANA_SUFFIX_RE, word)
    katakana_fixed_suffix = (
        katakana_suffix_after_furi_match.group(3) if katakana_suffix_after_furi_match else ""
    )
    if katakana_fixed_suffix:
        word = word[: -len(katakana_fixed_suffix)]
        logger.debug(
            "Detected fixed katakana suffix: '%s', word without suffix: '%s'",
            katakana_fixed_suffix,
            word,
        )

    # Convert word to hiragana for matching with other methods while preserving
    # small counter kana (e.g. ヶ/ヵ), which are meaningful inside kanji words.
    word = preserve_small_counter_kana(to_hiragana(word))

    # We have some kanji in the word to match
    # First, remove kana from the end of the word, to see if there is any okurigana
    word_match = re.search(KANJI_AND_MAYBE_FURIGANA_AND_OKURIGANA_RE, word)
    logger.debug("word_match groups: %s", word_match.groups() if word_match else None)
    ending_okurigana = word_match.group(3) if word_match else ""
    word_without_furigana = word_match.group(1) if word_match else word[: -len(ending_okurigana)]
    furigana = word_match.group(2) if word_match else ""
    logger.debug(
        "Parsed word - word_without_furigana: '%s', furigana: '%s', ending_okurigana: '%s'",
        word_without_furigana,
        furigana,
        ending_okurigana,
    )

    if not ending_okurigana and not furigana:
        logger.debug("No ending kana and no furigana but have kanji -> simple regex match")
        # Most simple case, we can regex search for the word directly
        pattern = make_word_pattern(word)

        # Remove tags and splitter dots from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text, part_regex=TAG_AND_DOT_PART_RE
        )
        logger.debug("html_free_text for matching: '%s'", html_free_text)

        # re.sub reports every match's position in its input, which has none of the b tags the
        # earlier matches got, so their length is added on to get the current position.
        b_tags_inserted = 0

        def replace_match(match: re.Match) -> str:
            nonlocal b_tags_inserted
            increment_tag_indexes(match.start(0) + b_tags_inserted, match.end(0) + b_tags_inserted)
            b_tags_inserted += len("<b></b>")
            return f"<b>{match.group(0)}</b>"

        result = re.sub(pattern, replace_match, html_free_text)
        logger.debug("Intermediate result with <b> tags: '%s'", result)
        result = restore_tags(result)
        return result
    elif not ending_okurigana and furigana:
        logger.debug("No ending kana but has furigana -> split and regex match, then reconstruct")
        # Relatively simple case, we can regex search for the word
        # However, we need to make sure the word's furigana matches the text's furigana and
        # the text isn't including more or less kanji in the word

        # So, we need to split the word and text into individual kanji-furigana parts and
        # then match those parts, reconstructing the furigana back afterwards
        word_with_readings_split = split_furi_text_into_individual_kanji_furigana(word)
        logger.debug("word_with_readings_split: %s", word_with_readings_split)

        text_with_readings_split = split_furi_text_into_individual_kanji_furigana(text)
        logger.debug("text_with_readings_split: %s", text_with_readings_split)

        pattern, expected_readings = make_furigana_agnostic_pattern(word_with_readings_split)
        if katakana_fixed_suffix:
            # Append the fixed katakana suffix to the pattern, matching both katakana and hiragana.
            katakana_suffix_pattern = replace_hiragana_in_pattern(
                to_hiragana(katakana_fixed_suffix)
            )
            pattern += katakana_suffix_pattern
            logger.debug("Appended fixed katakana suffix pattern: '%s'", katakana_suffix_pattern)
        logger.debug("Using pattern: %s", pattern)

        # Remove tags and splitter dots from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text_with_readings_split, part_regex=TAG_AND_BARE_DOT_PART_RE
        )
        logger.debug("html_free_text for matching: '%s'", html_free_text)

        # As above: the positions re.sub reports know nothing of the b tags already inserted
        b_tags_inserted = 0

        def replace_match(match: re.Match) -> str:
            nonlocal b_tags_inserted
            has_sound_change = False
            for idx, expected in enumerate(expected_readings):
                captured = match.group(f"furi_{idx}")
                if captured is None:
                    # No furigana in the text for this kanji, so nothing to disagree about
                    continue
                agreement = reading_agreement(expected, to_hiragana(captured))
                if agreement == "none":
                    return match.group(0)
                if agreement == "sound_change":
                    has_sound_change = True

            match_text = match.group(0)
            split_start = match.start(0)
            split_end = match.end(0)
            leading_ws = ""
            # A reading the text changed (及び 腰[ごし] for 腰[こし]) leaves the space before the
            # word outside the highlight. Only that kind of difference does; the ones that are
            # the word's own doing keep the space inside, where every other path has it
            if has_sound_change and split_start > 0 and match_text[:1].isspace():
                leading_ws = match_text[0]
                match_text = match_text[1:]
                split_start += 1

            if not match_text:
                return match.group(0)

            increment_tag_indexes(split_start + b_tags_inserted, split_end + b_tags_inserted)
            b_tags_inserted += len("<b></b>")
            return f"{leading_ws}<b>{match_text}</b>"

        result = re.sub(pattern, replace_match, html_free_text)
        logger.debug("Intermediate result with <b> tags: '%s'", result)

        # Restore tags now, as the tag indexes are based on the split text
        result = restore_tags(result)
        logger.debug("Restored html tags result: '%s'", result)

        # Re-merge any consecutive furigana parts that were split earlier
        result = merge_consecutive_furigana(result, text)

        # Remove the space the furigana splitting puts at the beginning, unless the text was
        # written with one there
        if not text[:1].isspace():
            result = re.sub(r"^(<b>)? ", r"\1", result)
        return result

    # Getting more complicated, need to handle possible inflections
    word = word[: -len(ending_okurigana)]
    logger.debug(
        "Found ending kana, handling possible inflections: ending_okurigana='%s', word='%s',"
        " word_without_furigana='%s'",
        ending_okurigana,
        word,
        word_without_furigana,
    )

    if not furigana:
        logger.debug("No furigana but have kanji with okuri, use get_conjugated_okuri_with_mecab")
        pattern = make_word_pattern(word, followed_by_okurigana=True)
        # Add regex for possible okurigana after the word, we'll try to match inflections to those
        pattern += rf"((?:{ending_okurigana})|(?:[ぁ-んア-ン]*))"
        # Remove tags and splitter dots from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text, part_regex=TAG_AND_DOT_PART_RE
        )
        logger.debug("html_free_text for matching: '%s'", html_free_text)
        matches = list(re.finditer(pattern, html_free_text))
        result_indices: list[tuple[int, int]] = []
        for m in matches:
            maybe_okuri = m.group(1)
            logger.debug(
                "Found potential match at indices (%s, %s), maybe_okuri: '%s'",
                m.start(0),
                m.end(0),
                maybe_okuri,
            )
            if maybe_okuri == ending_okurigana:
                # Exact match, no need to check inflection
                logger.debug("Exact match found, no inflection check needed")
                result_indices.append((m.start(0), m.end(0)))
                continue
            na_okuri = adnominal_na_okuri(ending_okurigana, to_hiragana(maybe_okuri))
            if na_okuri:
                # MeCab reads the whole な form as one adnominal word, so the stem is checked
                # against the word's own okurigana instead
                logger.debug("Found the word's な form, okurigana: '%s'", na_okuri)
                result_indices.append((m.start(0), m.end(0) - len(maybe_okuri) + len(na_okuri)))
                continue
            # Check if the maybe_okuri contains a valid inflection for the ending_okurigana
            okuri_result, _ = get_conjugated_okuri_with_mecab(
                word=word_without_furigana,
                reading=furigana,
                maybe_okuri=to_hiragana(maybe_okuri),
                okuri_prefix="word",
            )
            logger.debug(
                "okuri_result: okurigana: '%s', rest_kana: '%s', result: '%s', part_of_speech:"
                " '%s'",
                okuri_result.okurigana,
                okuri_result.rest_kana,
                okuri_result.result,
                okuri_result.part_of_speech,
            )
            if okuri_result.result != "no_okuri":
                # We have a valid inflected form, extend end index to include the okurigana
                logger.debug("Found valid inflected form")
                result_indices.append(
                    (m.start(0), m.end(0) - len(maybe_okuri) + len(okuri_result.okurigana))
                )
            else:
                logger.debug("No valid inflected form found")
                result_indices.append((m.start(0), m.end(0) - len(maybe_okuri)))

        # Insert <b> tags into the text at the found indices
        result = html_free_text

        for idx in range(len(result_indices)):
            start, end = result_indices[idx]
            # Increment for tags inside (but not on exact same position) or after the opening tag
            increment_tag_indexes(start, end)
            result = result[:start] + "<b>" + result[start:end] + "</b>" + result[end:]
            logger.debug("Result after %s <b> insertions: '%s'", idx + 1, result)
            # Adjust subsequent indices due to added tag lengths
            for j in range(idx + 1, len(result_indices)):
                s, e = result_indices[j]
                result_indices[j] = (s + 7, e + 7)
        logger.debug("Intermediate result with <b> tags: '%s'", result)
        result = restore_tags(result)
        logger.debug("Restored html tags result: '%s'", result)
        return result
    else:
        logger.debug("Furigana present, using kana_highlight for inflection matching")
        # Furigana is present, so use kana_highlight to find the inflected forms for the last kanji
        # while matching the beginning part with direct regex search
        word_with_readings_split = split_furi_text_into_individual_kanji_furigana(word)
        logger.debug("word_with_readings_split: %s", word_with_readings_split)
        # Get the last kanji character and its furigana, while removing it from the split word
        last_kanji = ""
        repeater = ""
        last_kanji_furigana = ""

        def remove_from_split_word(match: re.Match) -> str:
            nonlocal last_kanji, repeater, last_kanji_furigana
            last_kanji = match.group(1) if match else ""
            repeater = match.group(2) if match else ""
            last_kanji_furigana = (match.group(3) if match else "") or ""
            logger.debug(
                "Found last kanji in split word: '%s', repeater: '%s', last_kanji_furigana: '%s'",
                last_kanji,
                repeater,
                last_kanji_furigana,
            )
            return ""

        word_with_readings_split = re.sub(
            LAST_KANJI_FURIGANA_RE, remove_from_split_word, word_with_readings_split
        )

        logger.debug(
            " last_kanji: '%s', last_kanji_furigana: '%s',  remaining word_with_readings_split:"
            " '%s'",
            last_kanji,
            last_kanji_furigana,
            word_with_readings_split,
        )
        if not last_kanji:
            # Everything below is about the word's last kanji: its reading is the one held
            # against the text's and its okurigana the one inflected. A word that could not
            # be split (a bracket that holds no kana comes back wrapped in <err>) has none,
            # and the pattern would have no furigana group to read, so it is not found
            logger.debug("The split word does not end in a kanji, nothing to match")
            return text
        last_word_kanji = WordKanjiReading(
            kanji=f"{last_kanji}{repeater}",
            reading=last_kanji_furigana,
            begins_word=not word_with_readings_split.strip(),
        )
        # Split the whole text similarly
        text_with_readings_split = split_furi_text_into_individual_kanji_furigana(text)
        logger.debug("text_with_readings_split: %s", text_with_readings_split)
        # Find all occurrences of the word_with_readings_split in the text_with_readings_split
        pattern, prefix_expected_readings = make_furigana_agnostic_pattern(word_with_readings_split)
        # Replace the furigana part for the last kanji in the regex pattern so that all
        # kana are allowed, this allows for matching inflected forms where the base reading
        # changes, like rendaku, small tsu, vowel changes etc.
        pattern += rf"{whole_number_pattern(last_kanji)}{repeater}(?:\[(?P<furigana>[^\]]+)\])?"
        pattern += rf"(?P<maybe_okuri>(?:{ending_okurigana})|(?:[ぁ-んア-ン]*))"
        logger.debug("Regex pattern for matching: '%s'", pattern)

        # Remove tags and splitter dots from text temporarily
        html_free_text, increment_tag_indexes, restore_tags, _ = use_tag_cleaning_with_b_insertion(
            text_with_readings_split, part_regex=TAG_AND_BARE_DOT_PART_RE
        )
        logger.debug("html_free_text for matching: '%s', pattern: '%s'", html_free_text, pattern)
        matches = list(re.finditer(pattern, html_free_text))
        logger.debug("Found %s matches", len(matches))
        # The places found are kept apart by how the text reads the word's last kanji there:
        # as the word does, or otherwise. Which of the two get the highlight is decided
        # below, once the whole text has been looked at.
        word_reading_indices: list[tuple[int, int]] = []
        other_reading_indices: list[tuple[int, int]] = []
        for m in matches:
            if not furigana_captures_match_readings(m, prefix_expected_readings):
                logger.debug("Skipping match; prefix furigana does not match expected readings")
                continue
            # For each match, check if the last kanji's furigana can be inflected to match
            # the ending_okurigana
            # Find the position of the last kanji in the matched text
            matched_text = html_free_text[m.start(0) : m.end(0)]
            # Where the text writes the last kanji without furigana, the word's own
            # reading for it is the one to inflect with
            furigana = m.group("furigana") or last_kanji_furigana
            maybe_okuri = m.group("maybe_okuri")
            agreement: ReadingAgreement = "same"
            if furigana:
                agreement = last_kanji_agreement(
                    last_word_kanji,
                    ending_okurigana,
                    to_hiragana(furigana),
                    to_hiragana(maybe_okuri),
                )
            found_indices = word_reading_indices if agreement != "none" else other_reading_indices
            if maybe_okuri == ending_okurigana:
                if agreement == "none":
                    # The dictionary form itself under another reading is another word
                    # (捌[さば]ける for 捌[は]ける), whatever else the text holds
                    logger.debug(
                        "Skipping exact okuri match; furigana '%s' does not match last kanji"
                        " reading '%s'",
                        furigana,
                        last_kanji_furigana,
                    )
                    continue
                # Exact match, no inflection needed
                logger.debug(
                    "Exact match found for matched text: '%s', maybe_okuri: '%s'",
                    matched_text,
                    maybe_okuri,
                )
                found_indices.append((m.start(0), m.end(0)))
                continue
            na_okuri = adnominal_na_okuri(ending_okurigana, to_hiragana(maybe_okuri))
            if na_okuri and agreement != "none":
                # MeCab reads the whole な form as one adnominal word, so the stem is checked
                # against the word's own okurigana instead
                logger.debug("Found the word's な form, okurigana: '%s'", na_okuri)
                found_indices.append((m.start(0), m.end(0) - len(maybe_okuri) + len(na_okuri)))
                continue
            logger.debug(
                "Matched text for kana_highlight inflection check: '%s', maybe_okuri: '%s', match:"
                " %s",
                matched_text,
                maybe_okuri,
                m,
            )

            # Check if after_last_kanji contains a valid inflection for the ending_okurigana
            logger.debug(
                "Checking inflected forms for last kanji with mecab, last_kanji: '%s',"
                " last_kanji_furigana: '%s'",
                last_kanji,
                last_kanji_furigana,
            )

            kanji_okuri_result = OkuriResults(
                result="no_okuri",
                okurigana="",
                rest_kana="",
            )
            # The word's own reading is the one MeCab knows the kanji by where the text only
            # changed its sound (付[づ]けた). Where the bracket holds other kana than the
            # word's, by its stem, by where it ends or because it is another reading, the
            # text's reading is what the kana after the kanji continue, and the check below
            # uses that one
            if furigana and agreement in ("same", "sound_change"):
                kanji_okuri_result, _ = get_conjugated_okuri_with_mecab(
                    word=last_kanji,
                    reading=last_kanji_furigana,
                    maybe_okuri=to_hiragana(maybe_okuri),
                    okuri_prefix="word",
                )
            if kanji_okuri_result.result != "no_okuri":
                okuri_result = kanji_okuri_result
                logger.debug(
                    "Valid inflected form found for last kanji, okurigana: '%s'",
                    okuri_result.okurigana,
                )
            else:
                logger.debug(
                    "No valid inflected form found for last kanji, trying full word with furigana"
                    " '%s' and furigana '%s'",
                    word_without_furigana,
                    furigana,
                )
                word_okuri_result, _ = get_conjugated_okuri_with_mecab(
                    word=word_without_furigana,
                    reading=furigana,
                    maybe_okuri=to_hiragana(maybe_okuri),
                    okuri_prefix="word",
                )
                okuri_result = word_okuri_result
            logger.debug(
                "Furigana split okuri_result: okurigana: '%s', rest_kana: '%s', result: '%s',"
                " part_of_speech: '%s'",
                okuri_result.okurigana,
                okuri_result.rest_kana,
                okuri_result.result,
                okuri_result.part_of_speech,
            )
            if okuri_result.result != "no_okuri":
                # We have a valid inflected form, extend end index to include the okurigana
                logger.debug(
                    "Found valid inflected form with kana_highlight, okurigana: '%s', maybe_okuri:"
                    " '%s'",
                    okuri_result.okurigana,
                    maybe_okuri,
                )
                found_indices.append(
                    (
                        m.start(0),
                        m.end(0) - len(maybe_okuri) + len(okuri_result.okurigana),
                    )
                )
            else:
                logger.debug("No valid inflected form found with kana_highlight")
                found_indices.append((m.start(0), m.end(0) - len(maybe_okuri)))

        # Insert <b> tags into the text at the found indices
        # Extend each end index to include the fixed katakana suffix when present in the text
        if katakana_fixed_suffix:
            katakana_suffix_re = replace_hiragana_in_pattern(to_hiragana(katakana_fixed_suffix))
            suffix_len = len(katakana_fixed_suffix)
            logger.debug(
                "Extending result_indices end by fixed katakana suffix '%s'", katakana_fixed_suffix
            )

            def with_suffix(indices: list[tuple[int, int]]) -> list[tuple[int, int]]:
                # Only keep matches where the suffix is present immediately after the okuri
                # end; filter out incidental matches that lack the suffix (e.g. 彫[ほ]る
                # without ナイフ).
                return [
                    (start, end + suffix_len)
                    for start, end in indices
                    if re.match(katakana_suffix_re, html_free_text[end:])
                ]

            word_reading_indices = with_suffix(word_reading_indices)
            other_reading_indices = with_suffix(other_reading_indices)
        # A text that has the word under its own reading has answered where the word is, and
        # the same kanji read another way elsewhere in it is another word: 出[だ]す beside
        # 出[で]てくる, the 紡[ぼう] of 紡錘 beside 紡[つむ]ぎ. A text that has the kanji only
        # under another reading is still best answered with that place. Often it is the word
        # after all and the word was given with the wrong one of the kanji's readings
        # (潜[もぐ]る for a text that has 潜[くぐ]って), which nothing here can tell from the
        # other case.
        result_indices = word_reading_indices or other_reading_indices
        if word_reading_indices and other_reading_indices:
            logger.debug(
                "Leaving out %s matches the text reads otherwise", len(other_reading_indices)
            )
        result = html_free_text
        for idx in range(len(result_indices)):
            start, end = result_indices[idx]
            increment_tag_indexes(start, end)
            result = result[:start] + "<b>" + result[start:end] + "</b>" + result[end:]
            # Adjust subsequent indices due to added tag lengths
            for j in range(idx + 1, len(result_indices)):
                s, e = result_indices[j]
                result_indices[j] = (s + 7, e + 7)
        logger.debug("Intermediate result with <b> tags: '%s'", result)
        # Restore tags now, as the tag indexes are based on the split text
        result = restore_tags(result)
        logger.debug("Restored html tags result: '%s'", result)
        # Re-merge any consecutive furigana parts that were split earlier
        result = merge_consecutive_furigana(result, text)
        # Remove the space the furigana splitting puts at the beginning, unless the text was
        # written with one there
        if not text[:1].isspace():
            result = re.sub(r"^(<b>)? ", r"\1", result)
        return result
