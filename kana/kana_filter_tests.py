import sys

from .kana_highlight import kana_filter


RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
RESET = "\033[0m"

failed_tests: list[str] = []


def test(test_name: str, text: str, expected: str):
    """Run a test for the kana_filter function."""
    result = kana_filter(text)
    try:
        assert result == expected
    except AssertionError:
        failed_tests.append(test_name)
        print(
            f"""{RED}{test_name}
{YELLOW}Expected: {expected!r}
{GREEN}Got:      {result!r}
{RESET}"""
        )


def main():
    # Basic furigana, the cases Anki's own {{kana:Field}} filter gives the same result for
    test(
        test_name="single word",
        text="漢字[かんじ]",
        expected="かんじ",
    )
    test(
        test_name="leading space before the word is dropped",
        text=" 漢字[かんじ]",
        expected="かんじ",
    )
    test(
        test_name="leading space in the middle of a sentence is dropped",
        text="これは 漢字[かんじ]です",
        expected="これはかんじです",
    )
    test(
        test_name="multiple words",
        text="日本語[にほんご]を 勉強[べんきょう]する",
        expected="にほんごをべんきょうする",
    )
    test(
        test_name="consecutive words separated by a space",
        text="日本[にほん] 語[ご]",
        expected="にほんご",
    )
    test(
        test_name="okurigana is kept",
        text="食[た]べる",
        expected="たべる",
    )
    test(
        test_name="okurigana is kept, with leading space",
        text="これを 食[た]べる",
        expected="これをたべる",
    )
    test(
        test_name="small ヶ, numbers and 々 count as kanji",
        text="一ヶ月[いっかげつ] ３月[さんがつ] 人々[ひとびと]",
        expected="いっかげつさんがつひとびと",
    )
    test(
        test_name="&nbsp; is treated as a space",
        text="漢字[かんじ]&nbsp;語[ご]",
        expected="かんじご",
    )

    # Where this differs from Anki: kanji are matched directly instead of with [^ >], so text
    # before the kanji isn't swallowed. Anki's version would give かんじです here.
    test(
        test_name="text directly before the kanji is kept",
        text="これは漢字[かんじ]です",
        expected="これはかんじです",
    )
    test(
        test_name="mixed okurigana furigana, okurigana in the middle",
        text="消え去[きえさ]る",
        expected="きえさる",
    )
    test(
        test_name="mixed okurigana furigana, okurigana in the middle and the end",
        text="隣り合わせ[となりあわせ]",
        expected="となりあわせ",
    )

    # [sound:...] tags are left alone
    test(
        test_name="sound tag alone",
        text="[sound:x.mp3]",
        expected="[sound:x.mp3]",
    )
    test(
        test_name="sound tag directly after furigana",
        text="音[おと][sound:x.mp3]",
        expected="おと[sound:x.mp3]",
    )
    test(
        test_name="sound tag after a space",
        text="漢字[かんじ] [sound:x.mp3]",
        expected="かんじ [sound:x.mp3]",
    )
    test(
        test_name="sound tag directly after kanji, with kanji and numbers in the file name",
        text="漢字[sound:漢字1.mp3]",
        expected="漢字[sound:漢字1.mp3]",
    )

    # Text without furigana is unchanged
    test(
        test_name="empty text",
        text="",
        expected="",
    )
    test(
        test_name="kana only",
        text="ひらがなだけ",
        expected="ひらがなだけ",
    )
    test(
        test_name="kanji without furigana are kept",
        text="漢字だけ",
        expected="漢字だけ",
    )
    test(
        test_name="numbers without furigana are kept",
        text="3つ",
        expected="3つ",
    )

    # HTML is preserved
    test(
        test_name="furigana inside a tag",
        text="<b>漢字[かんじ]</b>",
        expected="<b>かんじ</b>",
    )
    test(
        test_name="furigana with leading space inside a tag",
        text='<span class="x"> 漢字[かんじ]</span>です',
        expected='<span class="x">かんじ</span>です',
    )
    test(
        test_name="furigana with reading tags, as kana_highlight outputs it",
        text="<b><on> 会[かい]</on></b><on> 話[わ]</on>をする",
        expected="<b><on>かい</on></b><on>わ</on>をする",
    )
    test(
        test_name="line break between words",
        text="漢字[かんじ]と<br>音読[おんよ]み",
        expected="かんじと<br>おんよみ",
    )
    test(
        test_name="numbers in tag attributes are kept",
        text='<img src="paste-123.jpg">漢字[かんじ]',
        expected='<img src="paste-123.jpg">かんじ',
    )

    if failed_tests:
        print(f"{RED}{len(failed_tests)} tests failed{RESET}")
        sys.exit(1)
    print(f"\n{GREEN}All tests passed{RESET}")


if __name__ == "__main__":
    main()
