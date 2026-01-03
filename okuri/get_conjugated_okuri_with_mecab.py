import sys

try:
    from mecab_common import (
        OkuriPrefix,
        get_all_conjugation_conditions,
        get_word_type_from_mecab_token,
        mecab,
    )
except ImportError:
    from .mecab_common import (
        OkuriPrefix,
        get_all_conjugation_conditions,
        get_word_type_from_mecab_token,
        mecab,
    )
try:
    from all_types.main_types import (
        OkuriResults,
    )
except ImportError:
    from ..all_types.main_types import (
        OkuriResults,
    )
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger

try:
    from mecab_controller.basic_types import (
        MecabParsedToken,
    )
except ImportError:
    from ..mecab_controller.basic_types import (
        MecabParsedToken,
    )


def get_conjugated_okuri_with_mecab(
    word: str,
    reading: str,
    maybe_okuri: str,
    okuri_prefix: OkuriPrefix = "word",
    logger: Logger = Logger("error"),
) -> tuple[OkuriResults, bool]:
    """
    Determines the portion of text that is the conjugated okurigana for a kanji reading.
    :param word: The kanji or word
    :param maybe_okuri: The okurigana to check
    :param reading: The reading of the kanji or word occurring before the okurigana
    :param logger: Logger instance for debugging
    :return: A tuple of the okurigana that is part of the conjugation for threading
            and the rest of the okurigana, along with a boolean indicating if it is a suru verb
    """
    logger.debug(
        f"get_conjugated_okuri - maybe_okuri: {maybe_okuri}, word: {word}, reading:"
        f" {reading}, okuri_prefix: {okuri_prefix}"
    )
    if not maybe_okuri:
        logger.debug("get_conjugated_okuri - No okurigana provided, no processing needed.")
        return OkuriResults("", "", "no_okuri", None), False
    parse_text_prefix = None
    if okuri_prefix == "word":
        if word:
            # Exception for 為 as its headword doesn't get detected correctly so process it using
            # the kanji reading
            if (word == "為" and reading == "し") or word == "抉":
                parse_text_prefix = reading
                okuri_prefix = "reading"
            else:
                parse_text_prefix = word
        elif reading:
            parse_text_prefix = reading
            okuri_prefix = "reading"
    elif okuri_prefix == "reading":
        if reading:
            parse_text_prefix = reading
        elif word:
            parse_text_prefix = word
            okuri_prefix = "word"
    if not parse_text_prefix:
        logger.error(
            f"get_conjugated_okuri - cannot set parse_text_prefix, okuri_prefix: '{okuri_prefix}',"
            f" word: '{word}', reading: '{reading}'"
        )
        return OkuriResults("", maybe_okuri, "no_okuri", None), False
    text_to_parse = f"{parse_text_prefix}{maybe_okuri}"

    okuri_type = "detected_okuri"
    is_suru_verb = False

    # exceptions that parsing gets wrong
    if word == "久" and reading == "ひさ" and maybe_okuri.startswith("しぶり"):
        return OkuriResults("し", maybe_okuri[1:], okuri_type, "adj-i"), is_suru_verb
    if word == "仄々" and reading == "ほのぼの":
        if maybe_okuri.startswith("した"):
            rest_kana = maybe_okuri[2:]
            return OkuriResults("した", rest_kana, okuri_type, None), is_suru_verb
        if maybe_okuri.startswith("しい"):
            rest_kana = maybe_okuri[2:]
            return OkuriResults("しい", rest_kana, okuri_type, "adj-i"), is_suru_verb
        if maybe_okuri.startswith("し"):
            rest_kana = maybe_okuri[1:]
            return OkuriResults("し", rest_kana, okuri_type, "adj-i"), is_suru_verb

    tokens: list[MecabParsedToken] = list(mecab.translate(text_to_parse))
    logger.debug(
        f"Parsed text: {text_to_parse} ->\n"
        + "\n".join([f"{token.word}, PartOfSpeech: {token.part_of_speech}" for token in tokens]),
    )
    if not tokens:
        logger.debug(
            f"get_conjugated_okuri - No tokens found for text: {text_to_parse}, returning no okuri."
        )
        return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
    first_token = tokens[0]
    if not first_token.part_of_speech:
        logger.error(f"get_conjugated_okuri - No PartOfSpeech found for {text_to_parse}")
        return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb

    word_type = get_word_type_from_mecab_token(first_token)
    logger.debug(
        f"First token: {first_token.word},  PartOfSpeech: {first_token.part_of_speech},"
        f" first_token word_type: {word_type}"
    )
    if not word_type:
        # If the first token is not one of the processable types, try again with kanji_reading
        # as the prefix
        if okuri_prefix == "word":
            logger.debug(
                f"First token not valid: {first_token.word}, PartOfSpeech:"
                f" {first_token.part_of_speech}, Retrying with reading as"
                " prefix."
            )
            if reading:
                return get_conjugated_okuri_with_mecab(
                    word,
                    reading,
                    maybe_okuri,
                    okuri_prefix="reading",
                    logger=logger,
                )
            else:
                logger.debug("No reading available to retry with, returning no okuri.")
                return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
        elif okuri_prefix == "reading":
            logger.debug(
                f"First token is not a verb or adjective: {first_token.word}, PartOfSpeech:"
                f" {first_token.part_of_speech}, Returning empty okuri."
            )
            return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
        else:
            logger.error(f"Unknown okuri_prefix: {okuri_prefix}. Expected 'word' or 'reading'.")
            return OkuriResults("", maybe_okuri, "no_okuri", None), is_suru_verb
    # The first token will actually include the conjugation stem, so we need to extract it
    conjugated_okuri = first_token.word[len(parse_text_prefix) :]
    # Exception for nouns like 恥ずかしげな where the げ should be considered not a conjugation
    # as it is in fact 恥ずかし気な
    if word_type == "noun" and first_token.word.endswith("げ"):
        conjugated_okuri = first_token.word[len(parse_text_prefix) : -1]
        okuri_type = "full_okuri"
        logger.debug(
            f"Detected okuri for noun: {conjugated_okuri}, rest:"
            f" {maybe_okuri[len(conjugated_okuri):]}"
        )
        return (
            OkuriResults(conjugated_okuri, maybe_okuri[len(conjugated_okuri) :], okuri_type, None),
            is_suru_verb,
        )
    rest_kana = maybe_okuri[len(conjugated_okuri) :]
    logger.debug(
        f"Initial conjugated okuri: {conjugated_okuri}, rest_kana: {rest_kana}, first token:"
        f" {first_token.word}, PartOfSpeech: {first_token.part_of_speech}"
    )
    rest_tokens = tokens[1:]
    for token in rest_tokens:
        add_to_conjugated_okuri, was_suru_verb = get_all_conjugation_conditions(
            token,
            rest_tokens,
            word_type,
            logger,
        )
        if add_to_conjugated_okuri:
            conjugated_okuri += token.word
            # Remove the text from the rest of the okurigana
            rest_kana = rest_kana[len(token.word) :]
            logger.debug(
                f"Added to okuri: {token.word}, headword: {token.headword}, new okuri:"
                f" {conjugated_okuri}, rest_kana: {rest_kana}"
            )
            if was_suru_verb:
                is_suru_verb = True
        else:
            # If we hit a non-auxiliary token, stop processing
            logger.debug(
                f"Stopping at non-auxiliary token: {token.word}, PartOfSpeech:"
                f" {token.part_of_speech},"
            )
            break
    return OkuriResults(conjugated_okuri, rest_kana, "detected_okuri", None), is_suru_verb


# Tests
def test(kanji, kanji_reading, maybe_okuri, expected, okuri_prefix="word", debug: bool = False):
    result, is_suru_verb = get_conjugated_okuri_with_mecab(
        kanji,
        kanji_reading,
        maybe_okuri,
        okuri_prefix,
        logger=Logger("debug" if debug else "error"),
    )
    try:
        assert result.okurigana == expected[0]
        assert result.rest_kana == expected[1]
        assert is_suru_verb == expected[2]
    except AssertionError:
        # Re-run with logging enabled
        get_conjugated_okuri_with_mecab(kanji, kanji_reading, maybe_okuri, logger=Logger("debug"))
        print(f"""\033[91mget_conjugated_okuri_with_mecab({maybe_okuri}, {kanji}, {kanji_reading})
\033[93mExpected: {expected}
\033[92mGot:      {(result.okurigana, result.rest_kana, is_suru_verb)}
\033[0m""")
        # Stop the testing here
        sys.exit(0)


def main():
    # Test cases
    test("逆上", "のぼ", "せたので", ("せた", "ので", False))
    test("悔", "くや", "しいくらい", ("しい", "くらい", False))
    test("安", "やす", "くなかった", ("くなかった", "", False))
    test("来", "く", "れたらいくよ", ("れたら", "いくよ", False))
    test("青", "あお", "かったらあかくぬって", ("かったら", "あかくぬって", False))
    test("大", "おお", "きくてやわらかい", ("きくて", "やわらかい", False))
    test("勉強", "べんきょう", "している", ("している", "", True))
    test("勉強", "べんきょう", "されている", ("されている", "", True))
    test("勉強", "べんきょう", "させられる", ("させられる", "", True))
    test("容易", "たやす", "くやったな", ("く", "やったな", False))
    test("清々", "すがすが", "しくない", ("しくない", "", False))
    # 恥ずかしげ gets categorized as a noun
    test("恥", "は", "ずかしげなかおで", ("ずかし", "げなかおで", False))
    test("察", "さっ", "していなかった", ("していなかった", "", False))
    test("為", "さ", "れるだろう", ("れる", "だろう", False))
    test("知", "し", "ってるでしょう", ("ってる", "でしょう", False))
    test("為", "し", "なかった", ("なかった", "", False))
    test("挫", "くじ", "けられないで", ("けられない", "で", False))
    test("挫", "くじ", "けさせてやる", ("けさせて", "やる", False))
    test("何気", "なにげ", "にと", ("に", "と", False))
    test("為", "す", "るしかない", ("る", "しかない", False))
    test("静", "しず", "かにいった", ("かに", "いった", False))
    test("静", "しず", "かでよい", ("か", "でよい", False))
    test("静", "しず", "かなあおさ", ("かな", "あおさ", False))
    test("高", "たか", "ければたかくなる", ("ければ", "たかくなる", False))
    test("行", "い", "ったらしい", ("ったらしい", "", False))
    test("行", "い", "ったらいくかも", ("ったら", "いくかも", False))
    test("清々", "すっきり", "した", ("した", "", True))
    test("熱々", "あつあつ", "だね", ("", "だね", False))
    test("瑞々", "みずみず", "しさがいい", ("しさ", "がいい", False))
    test("止", "ど", "め", ("め", "", False))
    test("読", "よ", "みかた", ("み", "かた", False))
    test("悪", "あ", "しがわからない", ("し", "がわからない", False))
    test("死", "し", "んでいない", ("んでいない", "", False))
    test("聞", "き", "いていたかい", ("いていた", "かい", False))
    test("目論", "もくろ", "む", ("む", "", False))
    # 久ぶりに doesn't get split into ひさし and ぶりに and is instead treated as a single noun
    test("久", "ひさ", "しぶりに", ("し", "ぶりに", False))
    test("久", "ひさ", "しいきもち", ("しい", "きもち", False))
    test("仄々", "ほのぼの", "したようす", ("した", "ようす", False))
    # 欲する is detected as a noun, when ほっする is commonly considered a kunyomi for it
    # This would need to be handled by giving only the する part to the function
    # test("欲", "ほっ", "ればやる", ("れば", "やる", False))
    test("欲", "ほ", "しいなら", ("しい", "なら", False))
    test("放", "ほ", "ったらかす", ("ったら", "かす", False))
    test("放", "ほう", "ったらかす", ("ったら", "かす", False))
    test("放", "ほう", "っておく", ("って", "おく", False))
    test("高", "たか", "めるから", ("める", "から", False))
    test("厚", "あつ", "かましくてやかましい", ("かましくて", "やかましい", False))
    test("抉", "えぐ", "られたように", ("られた", "ように", False))
    # Works when using okuri_prefix="kanji_reading" instead of "kanji"
    test("抉", "えぐ", "かったよな", ("かった", "よな", False))
    # えぐくて is too niche for mecab...
    # test("抉", "えぐ", "くてやわらかい", ("くて", "やわらかい", False))
    test("", "として", "いるのは", ("", "いるのは", False))
    test("送", "おく", "ってた", ("ってた", "", False))
    test("聴牌", "テンパ", "ります", ("ります", "", False))
    test("聴牌", "テンパ", "ってた", ("ってた", "", False))
    print("\033[92mTests passed\033[0m")


if __name__ == "__main__":
    main()
