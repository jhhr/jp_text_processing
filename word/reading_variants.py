"""Whether the reading a text gives a kanji is the reading a word gives it.

The furigana paths of `word_highlight` find the word's kanji in the text and then have to say,
kanji by kanji, whether a reading that is written differently is still the word's. That
decision is made here, and the paths only ask for it.

Four things make two spellings one reading:

1. A sound change the reading goes through where the text has it. This is `check_reading_match`
   of the kana pipeline, asked the way that pipeline asks it: the word's reading is the bare
   one and the text's the changed one (腰[こし] in 及び腰[ごし], 学[がく] in 学校[がっこう]).
   Nothing here changes what it accepts.

2. The same sound spelled the other way: ず and づ, じ and ぢ (動機付[どうきず]け and
   動機付[どうきづ]け).

3. Rendaku the other way round. Rendaku voices the first kana of an element that is not the
   first of its compound, so a word can hold the voiced form itself, 初見殺[しょけんごろ]し,
   where the text says the same compound without it, 初見殺[しょけんころ]し. Ignoring voicing
   is not the rule, though, since voicing also tells words apart. It is taken as rendaku
   undone only when both of these hold:

   - Something of the word stands before the kanji. A word that begins voiced is not a rendaku
     form of anything: 顔[がお] is the suffix and 顔[かお] the noun, and 降伏[ごうぶく] is
     another word than 降伏[こうふく].
   - The kanji does not list the voiced reading for itself. One it lists is a reading in its
     own right: 中 is チュウ and ジュウ, and 心中[しんじゅう] is not 心中[しんちゅう]; 見 is
     ケン and ゲン, and 一見[いちげん] is not 一見[いっけん]. 殺 has no ごろ and 深 no ぶか, so
     those can only be ころ and ふか voiced.

4. A stem said two ways. A few verbs and adjectives have a stem that begins with い or え in
   the newer pronunciation and with ゆ, よ or う in the older: 良い is いい and よい, 行く is
   いく and ゆく, 言う is いう and ゆう, 得る is える and うる, 歪む is いがむ and ゆがむ. No
   sound change makes one of the other wherever it stands, so the kanji's listed readings
   decide: both have to be kunyomi of that kanji with the same okurigana, alike but for that
   first kana. Two stems that merely take the same okurigana are two words, 捌[は]ける and
   捌[さば]ける, and so are 居[い]る and 居[お]る, which inflect differently.

The word's last kanji, the one its okurigana follows, has two more ways to agree, both to do
with the reading meeting the okurigana there:

5. The stem itself inflects. Two verbs do that: する is し, さ or せ in its other forms and
   くる is き or こ, so 為[す]る is found in 為[し]た and 来[く]る in 来[こ]ない. They are told by
   their kanji, the way okuri/ tells 為る; 摩[す]る and 繰[く]る are ordinary verbs.

6. The bracket ends at another kana. The text's can hold the start of the word's okurigana,
   溜[たま]っている for 溜[た]まる and 流行[はやり] for 流行[はや]り, the noun form of the
   okurigana included: 引[びき] in 字引 is ひき, voiced, for 引[ひ]く. Or the word's holds what
   the text writes after the kanji, 錆[さび]る against 錆[さ]びて. Kana that are not the
   okurigana's make another word: 突[つつ]いて is つつく, not 突[つ]く.

Everything else is another reading: 出[だ]す for 出[で]る, 潜[くぐ]って for 潜[もぐ]る, the
紡[ぼう] of 紡錘 for 紡[つむ]ぎ. What a path does with a place the text reads otherwise is that
path's own rule; this module only says that it does.

What is deliberately not here: voicing anywhere but in a reading's first kana (端[はし] and
端[はじ]), and the ち of an onyomi against じ (朝 チョウ and ジョウ in 晨朝), which is how 心中
differs too.
"""

from functools import lru_cache
from typing import Literal, NamedTuple

from ..kana.reading_matcher import check_reading_match
from ..kanji.all_kanji_data import all_kanji_data
from ..mecab_controller.kana_conv import to_hiragana
from ..okuri.okurigana_dict import get_verb_noun_form_okuri

# How a text's reading of a kanji is the word's reading of it: not at all, the same kana (or
# the same sound, 2 above), a sound change on the text's side (1), the word's rendaku undone
# (3), or the other pronunciation of the stem (4); and for the word's last kanji also the
# stem in another inflection (5), or the same kana with the bracket ending elsewhere (6)
ReadingAgreement = Literal[
    "none",
    "same",
    "sound_change",
    "rendaku_undone",
    "other_stem",
    "inflected_stem",
    "okurigana_moved",
]

# ぢ and づ written as the じ and ず they sound like
YOTSUGANA_AS_SPOKEN = str.maketrans("ぢづ", "じず")

# The two kana a stem said two ways can begin with (4 above), each pair written newer, older
STEM_KANA_PAIRS = frozenset(frozenset(pair) for pair in ("いゆ", "いよ", "えう", "えよ"))

# The verbs whose stem inflects (5 above), as kanji, stem and okurigana of the dictionary
# form, with the kana the stem is in the other forms
INFLECTED_STEMS = {
    ("為", "す", "る"): frozenset("しさせ"),
    ("来", "く", "る"): frozenset("きこ"),
}


class WordKanjiReading(NamedTuple):
    """
    A kanji of the word, as the word reads it.

    :param kanji: The kanji, or the run of them that shares one bracket (a repeater with its
        kanji, a jukujikun that could not be split)
    :param reading: The reading the word gives it, in hiragana
    :param begins_word: Whether nothing of the word, kanji or kana, stands before it
    """

    kanji: str
    reading: str
    begins_word: bool


def split_listed_readings(listed: str) -> list[str]:
    """Take a kanji's readings out of the 、-separated string the kanji data holds them in."""
    # A reading can carry a note in brackets after it, チュウ(呉)
    readings = [reading.split("(")[0].strip() for reading in listed.split("、")]
    return [reading for reading in readings if reading]


@lru_cache(maxsize=1024)
def readings_of_its_own(kanji: str) -> frozenset[str]:
    """
    Every reading the kanji data lists for the kanji, in hiragana: the onyomi, and each kunyomi
    both as its stem and with its okurigana. Empty for anything that is not one listed kanji.
    """
    data = all_kanji_data.get(kanji)
    if data is None:
        return frozenset()
    readings = {to_hiragana(onyomi) for onyomi in split_listed_readings(data.get("onyomi", ""))}
    for kunyomi in split_listed_readings(data.get("kunyomi", "")):
        readings.add(kunyomi.split(".")[0])
        readings.add(kunyomi.replace(".", ""))
    return frozenset(readings)


@lru_cache(maxsize=1024)
def okurigana_by_stem(kanji: str) -> dict[str, frozenset[str]]:
    """The okurigana each kunyomi stem of the kanji is listed with, for the stems that have any."""
    data = all_kanji_data.get(kanji)
    if data is None:
        return {}
    by_stem: dict[str, set[str]] = {}
    for kunyomi in split_listed_readings(data.get("kunyomi", "")):
        stem, dot, okurigana = kunyomi.partition(".")
        if dot:
            by_stem.setdefault(stem, set()).add(okurigana)
    return {stem: frozenset(okurigana) for stem, okurigana in by_stem.items()}


def is_rendaku_undone(word_kanji: WordKanjiReading, text_reading: str) -> bool:
    """Tell whether the word's reading is the text's with rendaku, by the rules at the top."""
    if word_kanji.begins_word:
        return False
    if word_kanji.reading in readings_of_its_own(word_kanji.kanji):
        return False
    # The same question the text's side is asked, the two readings changing places
    _, voiced_as = check_reading_match(reading=text_reading, mora_string=word_kanji.reading)
    return voiced_as == "rendaku"


def is_other_stem(kanji: str, reading: str, other_reading: str) -> bool:
    """Tell whether the two readings are one stem said two ways, by the rules at the top."""
    if reading[1:] != other_reading[1:]:
        return False
    if frozenset((reading[:1], other_reading[:1])) not in STEM_KANA_PAIRS:
        return False
    by_stem = okurigana_by_stem(kanji)
    return bool(by_stem.get(reading, frozenset()) & by_stem.get(other_reading, frozenset()))


def reading_agreement(
    word_kanji: WordKanjiReading, text_reading: str, okurigana: str = ""
) -> ReadingAgreement:
    """
    Say how the reading the text gives a kanji is the reading the word gives it.

    :param word_kanji: The kanji as the word reads it
    :param text_reading: The reading the text has on the same kanji, in hiragana
    :param okurigana: The kana after the kanji in the text, when it is the word's last kanji;
        one sound change depends on it (a reading loses its last う before っ)
    :return: How they agree, "none" when the text's is another reading or either is empty
    """
    if not word_kanji.reading or not text_reading:
        return "none"
    _, sound_change = check_reading_match(
        reading=word_kanji.reading, mora_string=text_reading, okurigana=okurigana
    )
    if sound_change == "plain":
        return "same"
    if sound_change != "none":
        return "sound_change"
    if word_kanji.reading.translate(YOTSUGANA_AS_SPOKEN) == text_reading.translate(
        YOTSUGANA_AS_SPOKEN
    ):
        return "same"
    if is_rendaku_undone(word_kanji, text_reading):
        return "rendaku_undone"
    if is_other_stem(word_kanji.kanji, word_kanji.reading, text_reading):
        return "other_stem"
    return "none"


def reads_into_okurigana(
    word_kanji: WordKanjiReading, word_okurigana: str, text_reading: str
) -> bool:
    """Tell whether the text's bracket holds the word's reading and the start of its okurigana."""
    in_bracket = [word_okurigana[:length] for length in range(1, len(word_okurigana) + 1)]
    noun_form = get_verb_noun_form_okuri(word_okurigana, word_kanji.kanji, word_kanji.reading)
    if noun_form:
        in_bracket.append(noun_form)
    # The sound changes work on what the bracket holds as a whole: the voicing of 引[びき] is
    # on the reading, and the small っ of 切[きっ] in 切符 on the okurigana
    return any(
        reading_agreement(word_kanji._replace(reading=word_kanji.reading + kana), text_reading)
        != "none"
        for kana in in_bracket
    )


def reads_into_text_kana(word_kanji: WordKanjiReading, text_reading: str, text_kana: str) -> bool:
    """Tell whether the word's bracket holds the text's reading and the kana the text has next."""
    reading = word_kanji.reading
    return any(
        text_kana.startswith(reading[cut:])
        and reading_agreement(word_kanji._replace(reading=reading[:cut]), text_reading) != "none"
        for cut in range(1, len(reading))
    )


def last_kanji_agreement(
    word_kanji: WordKanjiReading, word_okurigana: str, text_reading: str, text_kana: str
) -> ReadingAgreement:
    """
    Say how the reading the text gives the word's last kanji is the reading the word gives it.

    :param word_kanji: The word's last kanji as the word reads it
    :param word_okurigana: The kana the word has after it, in the dictionary form
    :param text_reading: The reading the text has on the same kanji, in hiragana
    :param text_kana: The kana after the kanji in the text, in hiragana
    :return: How they agree, "none" when the text's is another reading or either is empty
    """
    agreement = reading_agreement(word_kanji, text_reading, text_kana)
    if agreement != "none" or not word_kanji.reading or not text_reading:
        return agreement
    inflected = INFLECTED_STEMS.get((word_kanji.kanji, word_kanji.reading, word_okurigana))
    if inflected and text_reading in inflected:
        return "inflected_stem"
    if reads_into_okurigana(word_kanji, word_okurigana, text_reading):
        return "okurigana_moved"
    if reads_into_text_kana(word_kanji, text_reading, text_kana):
        return "okurigana_moved"
    return "none"
