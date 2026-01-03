from typing import Literal

try:
    from mecab_controller.basic_types import (
        Inflection,
        MecabParsedToken,
        PartOfSpeech,
    )
except ImportError:
    from ..mecab_controller.basic_types import (
        Inflection,
        MecabParsedToken,
        PartOfSpeech,
    )
try:
    from mecab_controller.mecab_controller import MecabController
except ImportError:
    from ..mecab_controller.mecab_controller import MecabController
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger

MecabWordType = Literal[
    "i_adjective",
    "na_adjective",
    "verb",
    "adverb",
    "noun",
]
OkuriPrefix = Literal["word", "reading"]

# Create a single MecabController instance that will be used by all functions in this module
mecab = MecabController()


def get_word_type_from_mecab_token(token: MecabParsedToken) -> MecabWordType | None:
    """Get the MecabWordType from a MecabParsedToken."""

    if token.part_of_speech == PartOfSpeech.i_adjective or (
        # i-adjective inflected to く gets categorized as an adverb
        token.part_of_speech == PartOfSpeech.adverb
        and token.word.endswith("く")
    ):
        return "i_adjective"
    if token.part_of_speech == PartOfSpeech.noun and (token.word.endswith("か")):
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
    return (
        # handle ている / でいる
        (
            token.part_of_speech == PartOfSpeech.particle
            and (token.word == "て" or token.word == "で")
            and (
                token.word == "て"
                or (token.word == "で" and next_token and next_token.headword == "いる")
            )
        )
        or ((
            token.part_of_speech == PartOfSpeech.verb
            and token.headword == "いる"
            and prev_token
            and prev_token.word in ["て", "で"]
            # don't add iru if preceded by ない
            and (not prev_prev_token or prev_prev_token.headword != "ない")
        ))
        or (
            # -られ, -させ
            token.part_of_speech == PartOfSpeech.verb
            and token.headword in ["れる", "られる", "せる", "させる", "てる"]
        )
        or (
            # -ない, -なく
            token.part_of_speech == PartOfSpeech.bound_auxiliary
            and token.headword == "ない"
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
    word_type: MecabWordType,
    logger: Logger = Logger("error"),
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
        # handle suru verbs
        if (
            (token.part_of_speech == PartOfSpeech.verb and token.headword == "する")
            or (token.part_of_speech == PartOfSpeech.bound_auxiliary and token.headword != "だ")
            or verb_conjugation_conditions(token, all_tokens)
            or (token.part_of_speech == PartOfSpeech.particle and token.word == "って")
        ):
            add_to_conjugated_okuri = True
        if token.headword == "する":
            is_suru_verb = True
    return add_to_conjugated_okuri, is_suru_verb
