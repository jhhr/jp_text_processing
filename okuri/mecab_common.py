from typing import Literal

from ..mecab_controller.basic_types import (
    Inflection,
    MecabParsedToken,
    PartOfSpeech,
)
from ..mecab_controller.mecab_controller import MecabController

MecabWordType = Literal[
    "i_adjective",
    "na_adjective",
    "verb",
    "adverb",
    "noun",
]
OkuriPrefix = Literal["word", "reading"]

# Mecab tags na-adjective stems as plain 名詞 (静か, 賑やか) and does not expose the
# 形容動詞語幹 sub-class, so a noun ending in か is the only handle there is. The indefinite
# pronouns built from an interrogative plus か are nouns ending in か too and take no な, so
# they are excluded by their stem. Most of them (誰か, 何か, どこか) mecab already splits off
# the か from, leaving the noun alone; 幾つか and いつか it does not.
INTERROGATIVE_STEMS = (
    "誰",
    "だれ",
    "何",
    "なに",
    "なん",
    "何処",
    "どこ",
    "何時",
    "いつ",
    "幾つ",
    "いくつ",
    "幾ら",
    "いくら",
    "何方",
    "どちら",
    "どっち",
    "何れ",
    "どれ",
    "どなた",
    "如何",
    "どう",
)

# Create a single MecabController instance that will be used by all functions in this module
mecab = MecabController()


def get_word_type_from_mecab_token(token: MecabParsedToken) -> MecabWordType | None:
    """Get the MecabWordType from a MecabParsedToken."""

    if token.part_of_speech == PartOfSpeech.i_adjective or (
        # i-adjective inflected to く gets categorized as an adverb
        token.part_of_speech == PartOfSpeech.adverb and token.word.endswith("く")
    ):
        return "i_adjective"
    if (
        token.part_of_speech == PartOfSpeech.noun
        and token.word.endswith("か")
        and token.word[:-1] not in INTERROGATIVE_STEMS
    ):
        return "na_adjective"
    if token.part_of_speech == PartOfSpeech.verb:
        return "verb"
    if token.part_of_speech == PartOfSpeech.adverb:
        return "adverb"
    # Need to check nouns for words like 止め or 恥ずかしげな
    if token.part_of_speech == PartOfSpeech.noun:
        return "noun"
    return None


def verb_conjugation_conditions(
    token: MecabParsedToken, all_tokens: list[MecabParsedToken]
) -> bool:
    """Check if the token meets verb conjugation conditions."""
    token_index = all_tokens.index(token)
    prev_prev_token = all_tokens[token_index - 2] if token_index > 1 else None
    prev_token = all_tokens[token_index - 1] if token_index > 0 else None
    next_token = all_tokens[token_index + 1] if token_index < len(all_tokens) - 1 else None
    return bool(
        # handle ている / でいる
        (
            token.part_of_speech == PartOfSpeech.particle
            and (token.word == "て" or token.word == "で")
            and (
                token.word == "て"
                or (token.word == "で" and next_token and next_token.headword == "いる")
            )
        )
        or (
            token.part_of_speech == PartOfSpeech.verb
            and token.headword == "いる"
            and prev_token
            and prev_token.word in ["て", "で"]
            # don't add iru if preceded by ない
            and (not prev_prev_token or prev_prev_token.headword != "ない")
        )
        or (
            # -られ, -させ
            token.part_of_speech == PartOfSpeech.verb
            and token.headword in ["れる", "られる", "せる", "させる", "てる"]
        )
        or (
            # -ない, -なく
            token.part_of_speech == PartOfSpeech.bound_auxiliary
            and token.headword in ["ない", "ぬ"]
        )
        or (
            # だ but not だろう or だね
            token.part_of_speech == PartOfSpeech.bound_auxiliary
            # だろう has word="だろ" and headword="だ", so using word="だ" excludes it
            and (token.word == "だ" and token.headword == "だ")
            and (not next_token or next_token.headword != "ね")  # exclude だね
        )
        or (
            # -て, -で following ない
            token.part_of_speech == PartOfSpeech.particle
            and token.word in ["て", "で"]
            and prev_token
            and prev_token.headword == "ない"
        )
    )


def get_all_conjugation_conditions(
    token: MecabParsedToken,
    all_tokens: list[MecabParsedToken],
    word_type: MecabWordType | None,
) -> tuple[bool, bool]:
    """Check if the token meets any conjugation conditions."""
    add_to_conjugated_okuri = False
    is_suru_verb = False
    if token.word in ["だろう", "でしょう", "なら", "から"]:
        add_to_conjugated_okuri = False
    elif word_type == "verb":
        if (
            token.part_of_speech == PartOfSpeech.bound_auxiliary
            and token.inflection_type is not None
            and token.headword not in ["だ", "です"]
        ) or verb_conjugation_conditions(token, all_tokens):
            add_to_conjugated_okuri = True
            if token.headword == "する":
                is_suru_verb = True
    elif word_type == "i_adjective":
        if (
            (
                # -ない, -なかっ(た)
                token.part_of_speech == PartOfSpeech.bound_auxiliary
                and (
                    token.inflection_type
                    in [
                        Inflection.continuative_ta,
                        Inflection.continuative_te,
                        Inflection.hypothetical,
                    ]
                    or token.word in ["た", "ない"]
                )
            )
            or (token.part_of_speech == PartOfSpeech.particle and token.word in ["て", "ば"])
            or token.word == "さ"
            or (token.part_of_speech == PartOfSpeech.bound_auxiliary and token.headword == "う")
        ):
            add_to_conjugated_okuri = True
    elif word_type == "na_adjective":
        if token.word == "な":
            add_to_conjugated_okuri = True
    elif word_type == "adverb" or word_type == "noun":
        # handle suru verbs; copula だ/です is never okurigana for nouns/adverbs
        if (
            (token.part_of_speech == PartOfSpeech.verb and token.headword == "する")
            or (
                token.part_of_speech == PartOfSpeech.bound_auxiliary
                and token.headword not in ["だ", "です"]
            )
            or (
                token.headword not in ["だ", "です"]
                and verb_conjugation_conditions(token, all_tokens)
            )
            or (token.part_of_speech == PartOfSpeech.particle and token.word == "って")
        ):
            add_to_conjugated_okuri = True
        if token.headword == "する":
            is_suru_verb = True
    return add_to_conjugated_okuri, is_suru_verb
