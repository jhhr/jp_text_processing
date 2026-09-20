"""Cases for `kana_filter`, run with pytest from `anki_shared/`:

    python -m pytest jp_text_processing/kana/kana_filter_tests.py
"""

import pytest

from .kana_highlight import kana_filter

CASES = [
    # Basic furigana, the cases Anki's own {{kana:Field}} filter gives the same result for
    pytest.param("漢字[かんじ]", "かんじ", id="single word"),
    pytest.param(" 漢字[かんじ]", "かんじ", id="leading space before the word is dropped"),
    pytest.param(
        "これは 漢字[かんじ]です",
        "これはかんじです",
        id="leading space in the middle of a sentence is dropped",
    ),
    pytest.param(
        "日本語[にほんご]を 勉強[べんきょう]する",
        "にほんごをべんきょうする",
        id="multiple words",
    ),
    pytest.param("日本[にほん] 語[ご]", "にほんご", id="consecutive words separated by a space"),
    pytest.param("食[た]べる", "たべる", id="okurigana is kept"),
    pytest.param("これを 食[た]べる", "これをたべる", id="okurigana is kept, with leading space"),
    pytest.param(
        "一ヶ月[いっかげつ] ３月[さんがつ] 人々[ひとびと]",
        "いっかげつさんがつひとびと",
        id="small ヶ, numbers and 々 count as kanji",
    ),
    pytest.param(
        "〆切[しめきり] 四〇三[よんまるさん] 𠮟[しか]る",
        "しめきりよんまるさんしかる",
        id="〆, 〇 and a supplementary plane kanji count as kanji",
    ),
    pytest.param("漢字[かんじ]&nbsp;語[ご]", "かんじご", id="&nbsp; is treated as a space"),
    # Where this differs from Anki: kanji are matched directly instead of with [^ >], so text
    # before the kanji isn't swallowed. Anki's version would give かんじです here.
    pytest.param(
        "これは漢字[かんじ]です", "これはかんじです", id="text directly before the kanji is kept"
    ),
    pytest.param(
        "消え去[きえさ]る",
        "きえさる",
        id="mixed okurigana furigana, okurigana in the middle",
    ),
    pytest.param(
        "隣り合わせ[となりあわせ]",
        "となりあわせ",
        id="mixed okurigana furigana, okurigana in the middle and the end",
    ),
    # [sound:...] tags are left alone
    pytest.param("[sound:x.mp3]", "[sound:x.mp3]", id="sound tag alone"),
    pytest.param(
        "音[おと][sound:x.mp3]", "おと[sound:x.mp3]", id="sound tag directly after furigana"
    ),
    pytest.param(
        "漢字[かんじ] [sound:x.mp3]", "かんじ [sound:x.mp3]", id="sound tag after a space"
    ),
    pytest.param(
        "漢字[sound:漢字1.mp3]",
        "漢字[sound:漢字1.mp3]",
        id="sound tag directly after kanji, with kanji and numbers in the file name",
    ),
    # Text without furigana is unchanged
    pytest.param("", "", id="empty text"),
    pytest.param("ひらがなだけ", "ひらがなだけ", id="kana only"),
    pytest.param("漢字だけ", "漢字だけ", id="kanji without furigana are kept"),
    pytest.param("3つ", "3つ", id="numbers without furigana are kept"),
    # HTML is preserved
    pytest.param("<b>漢字[かんじ]</b>", "<b>かんじ</b>", id="furigana inside a tag"),
    pytest.param(
        '<span class="x"> 漢字[かんじ]</span>です',
        '<span class="x">かんじ</span>です',
        id="furigana with leading space inside a tag",
    ),
    pytest.param(
        "<b><on> 会[かい]</on></b><on> 話[わ]</on>をする",
        "<b><on>かい</on></b><on>わ</on>をする",
        id="furigana with reading tags, as kana_highlight outputs it",
    ),
    pytest.param(
        "漢字[かんじ]と<br>音読[おんよ]み",
        "かんじと<br>おんよみ",
        id="line break between words",
    ),
    pytest.param(
        '<img src="paste-123.jpg">漢字[かんじ]',
        '<img src="paste-123.jpg">かんじ',
        id="numbers in tag attributes are kept",
    ),
    # Several words in one text. A mixed-okurigana reading used to run on past its own closing
    # bracket to the last word in the text whose okurigana sat in front of one, which left the
    # first word overfed and the second rewritten into a bracket the filter no longer reads.
    pytest.param(
        "彼は 見え[みえ]ない 所[ところ]で 消え[きえ]た",
        "彼はみえないところできえた",
        id="two words whose okurigana is the same kana",
    ),
    pytest.param(
        "これは 上げ[あげ]て 下げ[さげ]る",
        "これはあげてさげる",
        id="two words whose okurigana and reading share a kana",
    ),
    pytest.param(
        "食べ[たべ]たい 食べ[たべ]る", "たべたいたべる", id="the same word twice in one text"
    ),
    # A \n marks where a word begins just as a space does: fields written in the HTML editor
    # break their lines with <br>, but fields pasted or imported as plain text carry \n.
    pytest.param("行[い]く\n食べ[たべ]る", "いく\nたべる", id="a word opening a line is a word start"),
    # Whole sentences: what the filter gets from a card, with the words kept apart by a space,
    # a <br> or a newline, one of them opening the text and one following a tag.
    pytest.param(
        "勿体無い[もったいない] 行き来[いきき]",
        "もったいないいきき",
        id="the greedy reading and the second reading in one text",
    ),
    pytest.param(
        "見え[みえ]た<br>消え[きえ]た",
        "みえた<br>きえた",
        id="words sharing okurigana across a line break",
    ),
    pytest.param(
        "<b>上げ[あげ]</b>て 下げ[さげ]る",
        "<b>あげ</b>てさげる",
        id="a word right after a tag, with another after it",
    ),
    pytest.param(
        "すり下ろす[すりおろす]\nかも知れない[かもしれない]",
        "すりおろす\nかもしれない",
        id="two words opening with kana, the second opening a line",
    ),
    pytest.param(
        "朝[あさ] 起き[おき]て<br>夜[よる] 寝る[ねる]",
        "あさおきて<br>よるねる",
        id="a sentence of words with and without okurigana",
    ),
]


@pytest.mark.parametrize("text, expected", CASES)
def test_kana_filter(text: str, expected: str):
    assert kana_filter(text) == expected


if __name__ == "__main__":
    # Habit, and the `-m` form the other suites still use, keeps working.
    raise SystemExit(pytest.main([__file__]))
