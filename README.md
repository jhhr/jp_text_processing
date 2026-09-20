# jp_text_processing

Japanese furigana, reading and word-highlighting processing, shared by the author's Anki add-ons.
The add-ons vendor this directory as a package and import it as
`<addon>.shared.jp_text_processing`; it is not pip-installable. Python 3.10 or newer.

Text is in Anki's furigana syntax: a reading follows its kanji in square brackets, and a space
before the word marks where its kanji start, except at the start of the string
(`この 家[いえ]は`, `家[いえ]で 居[い]る`).

## kana_highlight

```python
from jp_text_processing import kana_highlight
from jp_text_processing.all_types.main_types import WithTagsDef
```

`kana_highlight` highlights one kanji, together with its reading, inside furigana text. The
reading of every word is split between the word's individual kanji, so the highlight lands on
the kanji's own share of the reading and not on the whole word's. Every occurrence of the kanji
is highlighted, each with whatever it is read as in that word:

```python
>>> text = "大人[おとな]は 毎日[まいにち] 日本語[にほんご]を 勉強[べんきょう]する。"
>>> plain = WithTagsDef(with_tags=False, merge_consecutive=False, onyomi_to_katakana=False, include_suru_okuri=False)
>>> kana_highlight("日", text, "furigana", plain)
' 大人[おとな]は 毎[まい]<b> 日[にち]</b><b> 日[に]</b> 本語[ほんご]を 勉強[べんきょう]する。'
```

The same text and kanji in every return type and option. `return_type` is `furigana` (kanji with
the reading after it, as above), `furikanji` (the reading with the kanji after it) or `kana_only`
(the reading alone). The options are the fields of `WithTagsDef`.

```python
>>> kana_highlight("日", text, "furikanji", plain)
' おとな[大人]は まい[毎]<b> にち[日]</b><b> に[日]</b> ほんご[本語]を べんきょう[勉強]する。'
>>> kana_highlight("日", text, "kana_only", plain)
'おとなは まい<b>にち</b> <b>に</b>ほんごを べんきょうする。'

# with_tags: each reading is wrapped in a tag naming its type, <on>, <kun> or <juk>, with
# <oku> around okurigana
>>> kana_highlight("日", text, "furigana", WithTagsDef(True, False, False, False))
'<juk> 大[おと]</juk><juk> 人[な]</juk>は<on> 毎[まい]</on><b><on> 日[にち]</on></b><b><on> 日[に]</on></b><on> 本[ほん]</on><on> 語[ご]</on>を<on> 勉[べん]</on><on> 強[きょう]</on><oku>する</oku>。'

# merge_consecutive: neighbouring readings of the same type share one tag
>>> kana_highlight("日", text, "furigana", WithTagsDef(True, True, False, False))
'<juk> 大人[おとな]</juk>は<on> 毎[まい]</on><b><on> 日[にち]</on></b><b><on> 日[に]</on></b><on> 本語[ほんご]</on>を<on> 勉強[べんきょう]</on><oku>する</oku>。'

# onyomi_to_katakana: onyomi readings are written in katakana
>>> kana_highlight("日", text, "furigana", WithTagsDef(True, True, True, False))
'<juk> 大人[おとな]</juk>は<on> 毎[マイ]</on><b><on> 日[ニチ]</on></b><b><on> 日[ニ]</on></b><on> 本語[ホンゴ]</on>を<on> 勉強[ベンキョウ]</on><oku>する</oku>。'

# include_suru_okuri: the する of a highlighted suru verb goes inside the highlight
>>> kana_highlight("強", text, "furigana", WithTagsDef(True, True, False, False))
'<juk> 大人[おとな]</juk>は<on> 毎日[まいにち]</on><on> 日本語[にほんご]</on>を<on> 勉[べん]</on><b><on> 強[きょう]</on></b><oku>する</oku>。'
>>> kana_highlight("強", text, "furigana", WithTagsDef(True, True, False, True))
'<juk> 大人[おとな]</juk>は<on> 毎日[まいにち]</on><on> 日本語[にほんご]</on>を<on> 勉[べん]</on><b><on> 強[きょう]</on><oku>する</oku></b>。'
```

With no `WithTagsDef` given, tags are on, merged, and onyomi in katakana. `kanji_to_highlight`
may be `None` to only split and tag the readings, or several kanji to highlight a run of them.

Readings come from a bundled table of about 11 000 kanji, with rendaku, gemination and vowel
changes accounted for; okurigana is checked against a conjugation dictionary and MeCab. A
reading the table cannot explain is jukujikun, and a small exception table covers words that
need a fixed split. Digits are read as the kanji they stand for (`24[にじゅうよん]`), `々`
repeats the kanji before it, and `[sound:...]` tags and HTML are left as they are.

`kana_filter(text)`, in the same module, is the plain kana filter: it drops the kanji and keeps
the readings, after the same cleaning passes `kana_highlight` runs.

```python
>>> from jp_text_processing.kana.kana_highlight import kana_filter
>>> kana_filter("これは 漢字[かんじ]です")
'これはかんじです'
```

## word_highlight

```python
from jp_text_processing import word_highlight
```

`word_highlight` finds a word or phrase, given in dictionary form, in the text and wraps each
occurrence in `<b>`, inflected forms included. Verbs are followed through their auxiliaries
(いる, させる, せる) and negations; i-adjectives up to and including the い form, with the な form
only when the word asks for it. Inflection is checked with MeCab.

The same word against the same sentence written with furigana, with kanji alone, and in kana:

```python
>>> word_highlight("私は 毎日[まいにち] 朝[あさ]ご 飯[はん]を 食[た]べている。", "食[た]べる")
'私は 毎日[まいにち] 朝[あさ]ご 飯[はん]を<b> 食[た]べている</b>。'
>>> word_highlight("私は毎日朝ご飯を食べている。", "食[た]べる")
'私は毎日朝ご飯を<b>食べている</b>。'

# A kana text is matched by a kana word; a reading in a bracket is not the word
>>> word_highlight("わたしはまいにちあさごはんをたべている。", "たべる")
'わたしはまいにちあさごはんを<b>たべている</b>。'
```

The word may be written without furigana too. Then the text's reading cannot be split, so a word
that covers only part of a kanji run highlights the whole run:

```python
>>> word_highlight("私は 日本語[にほんご]を", "語")
'私は<b> 日本語[にほんご]</b>を'
>>> word_highlight("私は 日本語[にほんご]を", "語[ご]")
'私は 日本[にほん]<b> 語[ご]</b>を'
```

MeCab comes from `mecab_controller`, a submodule vendored from AJATT-tools' fork, which bundles
a MeCab binary for each platform, so nothing has to be installed.

## Development

Run everything from the directory that contains `jp_text_processing`, with
`PYTHONIOENCODING=utf-8` set so that Japanese prints:

```
python -m pytest jp_text_processing -q
python -m mypy --config-file jp_text_processing/pyproject.toml -p jp_text_processing
ruff check jp_text_processing
ruff format --check jp_text_processing
```

The suites live next to the code as `*_tests.py` files; `kana/kana_highlight_tests.py` is the main
one. `AGENTS.md` describes the layout, the test conventions and the rules a change is expected
to follow.

## License

GNU GPL v3, see `LICENSE`. `mecab_controller` carries its own license files.
