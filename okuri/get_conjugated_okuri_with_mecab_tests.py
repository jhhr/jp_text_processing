"""Cases for `get_conjugated_okuri_with_mecab`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/okuri/get_conjugated_okuri_with_mecab_tests.py

Pass `--log-cli-level=debug` to see what a case logged; pytest captures the package logger on
its own, so nothing here has to turn logging on.

A case's id is `kanji[reading]okurigana`, the three arguments it is called with; a case with no
kanji only has a reading to name it by. The expected value is
`(okurigana, rest_kana, is_suru_verb)` — the parts of the result the function's callers read.

A case that is known to fail gets `marks=pytest.mark.xfail(reason="...", strict=True)` in its
`pytest.param`: strict so an unexpected pass fails the run and the reason gets dropped. None of
the cases below need it today.
"""

import pytest

from .get_conjugated_okuri_with_mecab import get_conjugated_okuri_with_mecab

CASES = [
    pytest.param("逆上", "のぼ", "せたので", ("せた", "ので", False), id="逆上[のぼ]せたので"),
    pytest.param("悔", "くや", "しいくらい", ("しい", "くらい", False), id="悔[くや]しいくらい"),
    pytest.param("安", "やす", "くなかった", ("くなかった", "", False), id="安[やす]くなかった"),
    pytest.param(
        "来", "く", "れたらいくよ", ("れたら", "いくよ", False), id="来[く]れたらいくよ"
    ),
    pytest.param(
        "青",
        "あお",
        "かったらあかくぬって",
        ("かったら", "あかくぬって", False),
        id="青[あお]かったらあかくぬって",
    ),
    pytest.param(
        "大",
        "おお",
        "きくてやわらかい",
        ("きくて", "やわらかい", False),
        id="大[おお]きくてやわらかい",
    ),
    pytest.param("美味", "おい", "しい", ("しい", "", False), id="美味[おい]しい"),
    pytest.param(
        "美味", "おい", "しさがいい", ("しさ", "がいい", False), id="美味[おい]しさがいい"
    ),
    pytest.param("美味", "おい", "しくない", ("しくない", "", False), id="美味[おい]しくない"),
    pytest.param(
        "勉強",
        "べんきょう",
        "している",
        ("している", "", True),
        id="勉強[べんきょう]している",
    ),
    pytest.param(
        "勉強",
        "べんきょう",
        "されている",
        ("されている", "", True),
        id="勉強[べんきょう]されている",
    ),
    pytest.param(
        "勉強",
        "べんきょう",
        "させられる",
        ("させられる", "", True),
        id="勉強[べんきょう]させられる",
    ),
    pytest.param(
        "容易", "たやす", "くやったな", ("く", "やったな", False), id="容易[たやす]くやったな"
    ),
    pytest.param(
        "清々", "すがすが", "しくない", ("しくない", "", False), id="清々[すがすが]しくない"
    ),
    # 恥ずかしげ gets categorized as a noun
    pytest.param(
        "恥",
        "は",
        "ずかしげなかおで",
        ("ずかし", "げなかおで", False),
        id="恥[は]ずかしげなかおで",
    ),
    pytest.param(
        "察",
        "さっ",
        "していなかった",
        ("していなかった", "", False),
        id="察[さっ]していなかった",
    ),
    pytest.param("為", "さ", "れるだろう", ("れる", "だろう", False), id="為[さ]れるだろう"),
    pytest.param(
        "知", "し", "ってるでしょう", ("ってる", "でしょう", False), id="知[し]ってるでしょう"
    ),
    pytest.param("為", "し", "なかった", ("なかった", "", False), id="為[し]なかった"),
    pytest.param(
        "挫", "くじ", "けられないで", ("けられないで", "", False), id="挫[くじ]けられないで"
    ),
    pytest.param(
        "挫", "くじ", "けさせてやる", ("けさせて", "やる", False), id="挫[くじ]けさせてやる"
    ),
    pytest.param("何気", "なにげ", "にと", ("に", "と", False), id="何気[なにげ]にと"),
    pytest.param("為", "す", "るしかない", ("る", "しかない", False), id="為[す]るしかない"),
    pytest.param(
        "静", "しず", "かにいった", ("かに", "いった", False), id="静[しず]かにいった"
    ),
    pytest.param("静", "しず", "かでよい", ("か", "でよい", False), id="静[しず]かでよい"),
    pytest.param(
        "静", "しず", "かなあおさ", ("かな", "あおさ", False), id="静[しず]かなあおさ"
    ),
    pytest.param("賑", "にぎ", "やかな", ("やかな", "", False), id="賑[にぎ]やかな"),
    # 静か and 賑やか are na-adjective stems mecab tags as plain nouns, so their な is
    # okurigana. 幾つか, 誰か and 何か end in か as well but are an interrogative plus か and
    # take no な, so the な after them stays out of the okurigana.
    pytest.param("幾", "いく", "つかな", ("つか", "な", False), id="幾[いく]つかな"),
    pytest.param("誰", "だれ", "かな", ("", "かな", False), id="誰[だれ]かな"),
    pytest.param("何", "なに", "かな", ("", "かな", False), id="何[なに]かな"),
    pytest.param(
        "高",
        "たか",
        "ければたかくなる",
        ("ければ", "たかくなる", False),
        id="高[たか]ければたかくなる",
    ),
    pytest.param("行", "い", "ったらしい", ("ったらしい", "", False), id="行[い]ったらしい"),
    pytest.param(
        "行", "い", "ったらいくかも", ("ったら", "いくかも", False), id="行[い]ったらいくかも"
    ),
    pytest.param("清々", "すっきり", "した", ("した", "", True), id="清々[すっきり]した"),
    pytest.param("熱々", "あつあつ", "だね", ("", "だね", False), id="熱々[あつあつ]だね"),
    pytest.param(
        "好々爺", "こうこうや", "です", ("", "です", False), id="好々爺[こうこうや]です"
    ),
    pytest.param(
        "瑞々",
        "みずみず",
        "しさがいい",
        ("しさ", "がいい", False),
        id="瑞々[みずみず]しさがいい",
    ),
    pytest.param("止", "ど", "め", ("め", "", False), id="止[ど]め"),
    pytest.param("読", "よ", "みかた", ("み", "かた", False), id="読[よ]みかた"),
    pytest.param(
        "悪", "あ", "しがわからない", ("し", "がわからない", False), id="悪[あ]しがわからない"
    ),
    pytest.param("死", "し", "んでいない", ("んでいない", "", False), id="死[し]んでいない"),
    pytest.param(
        "聞", "き", "いていたかい", ("いていた", "かい", False), id="聞[き]いていたかい"
    ),
    pytest.param("目論", "もくろ", "む", ("む", "", False), id="目論[もくろ]む"),
    # 久ぶりに doesn't get split into ひさし and ぶりに and is instead treated as a single noun
    pytest.param("久", "ひさ", "しぶりに", ("し", "ぶりに", False), id="久[ひさ]しぶりに"),
    pytest.param(
        "久", "ひさ", "しいきもち", ("しい", "きもち", False), id="久[ひさ]しいきもち"
    ),
    pytest.param(
        "仄々", "ほのぼの", "したようす", ("した", "ようす", False), id="仄々[ほのぼの]したようす"
    ),
    # 欲する is detected as a noun, when ほっする is commonly considered a kunyomi for it
    # This would need to be handled by giving only the する part to the function
    # pytest.param("欲", "ほっ", "ればやる", ("れば", "やる", False), id="欲[ほっ]ればやる"),
    pytest.param("欲", "ほ", "しいなら", ("しい", "なら", False), id="欲[ほ]しいなら"),
    pytest.param("放", "ほ", "ったらかす", ("ったら", "かす", False), id="放[ほ]ったらかす"),
    pytest.param(
        "放", "ほう", "ったらかす", ("ったら", "かす", False), id="放[ほう]ったらかす"
    ),
    pytest.param("放", "ほう", "っておく", ("って", "おく", False), id="放[ほう]っておく"),
    pytest.param("高", "たか", "めるから", ("める", "から", False), id="高[たか]めるから"),
    pytest.param(
        "厚",
        "あつ",
        "かましくてやかましい",
        ("かましくて", "やかましい", False),
        id="厚[あつ]かましくてやかましい",
    ),
    pytest.param(
        "抉", "えぐ", "られたように", ("られた", "ように", False), id="抉[えぐ]られたように"
    ),
    # Works when using okuri_prefix="kanji_reading" instead of "kanji"
    pytest.param(
        "抉", "えぐ", "かったよな", ("かった", "よな", False), id="抉[えぐ]かったよな"
    ),
    # えぐくて is too niche for mecab...
    # pytest.param(
    #     "抉", "えぐ", "くてやわらかい", ("くて", "やわらかい", False), id="抉[えぐ]くてやわらかい"
    # ),
    pytest.param("", "として", "いるのは", ("", "いるのは", False), id="[として]いるのは"),
    pytest.param("送", "おく", "ってた", ("ってた", "", False), id="送[おく]ってた"),
    pytest.param("聴牌", "テンパ", "ります", ("ります", "", False), id="聴牌[テンパ]ります"),
    pytest.param("聴牌", "テンパ", "ってた", ("ってた", "", False), id="聴牌[テンパ]ってた"),
    pytest.param("", "はにか", "んだ", ("んだ", "", False), id="[はにか]んだ"),
    pytest.param("御座", "ござ", "います", ("います", "", False), id="御座[ござ]います"),
]


@pytest.mark.parametrize("word, reading, maybe_okuri, expected", CASES)
def test_get_conjugated_okuri_with_mecab(
    word: str,
    reading: str,
    maybe_okuri: str,
    expected: tuple[str, str, bool],
):
    result, is_suru_verb = get_conjugated_okuri_with_mecab(word, reading, maybe_okuri)
    assert (result.okurigana, result.rest_kana, is_suru_verb) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
