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

What is deliberately not here: voicing anywhere but in a reading's first kana (端[はし] and
端[はじ]), and the ち of an onyomi against じ (朝 チョウ and ジョウ in 晨朝), which is how 心中
differs too.
"""

from functools import lru_cache
from typing import Literal, NamedTuple

from ..kana.reading_matcher import check_reading_match
from ..kanji.all_kanji_data import all_kanji_data
from ..mecab_controller.kana_conv import to_hiragana

# How a text's reading of a kanji is the word's reading of it: not at all, the same kana (or
# the same sound, 2 above), a sound change on the text's side (1), the word's rendaku undone
# (3), or the other pronunciation of the stem (4)
ReadingAgreement = Literal["none", "same", "sound_change", "rendaku_undone", "other_stem"]

# ぢ and づ written as the じ and ず they sound like
YOTSUGANA_AS_SPOKEN = str.maketrans("ぢづ", "じず")

# The two kana a stem said two ways can begin with (4 above), each pair written newer, older
STEM_KANA_PAIRS = frozenset(frozenset(pair) for pair in ("いゆ", "いよ", "えう", "えよ"))


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
