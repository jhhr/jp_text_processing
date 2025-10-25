# Main functions

## kana_highlight.py

Given some furigana text, find all kanji and highlight the the kanji **and its reading** within the text. Effectively, this splits readings within furigana between individual kanji to enable finding only the portion of the kanji that should be highlighted.

- Can return the text with all readings split in this way or keep the non-highlighted portions as-is.
- The kanji to highlight can be omitted to only use the reading splitting option.
- Optionally, each reading can be wrapped with html tags to signify the type of reading: `<on>`, `<kun>` or `<juk>`

## word_highlight.py

Given a word or phrase in furigana format, non-inflected, find occurrences of the phrase in the text, with inflection taken into account. Uses Mecab to check inflections - `mecab-controller` from AJATT-tools is included as a submodule for this.
