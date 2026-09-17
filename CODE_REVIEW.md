# Code review: jp_text_processing

Reviewed at commit `1536ad7` (main, 2026-09-17). This is a fresh review of the whole tree after
the 23 commits that followed the previous review at `782a5bc`; it replaces that report. Scope:
every tracked file, the bundled `mecab_controller` submodule read for context only. Nothing in
this report changes code. Every finding was checked by reading the code and, where it says so, by
running it; the fixes marked *verified* were applied on a scratch copy and the full pytest suite
run against them, then reverted.

## Summary

The codebase is in much better shape than at the last review. The hand-rolled test harnesses are
gone and every suite runs under pytest with a non-zero exit on failure; logging goes through the
standard `logging` module and nothing threads a logger through call signatures; mypy is clean with
the repo's own config; about 600 lines of dead code and the dual import scheme are gone; and all
five of the previous high-severity bugs are fixed.

What is left is concentrated in three places:

- **Two ways to corrupt or crash on ordinary input.** The okurigana-mix cleaning regex reads
  through the closing `]` into the next word, so a sentence with two words sharing the same
  okurigana (`見え[みえ]ない … 消え[きえ]た`) comes out of both `kana_filter` and
  `kana_highlight` with the second word garbled. `word_highlight` raises on any one-kana word it
  cannot find verbatim.
- **Two alignment gaps.** A kanji written twice in a row is assumed to repeat its reading, so
  `毎月月末[まいつきげつまつ]` tags げつ as kunyomi; and a word at the start of a line is not
  recognised as a word start, so it skips two cleaning passes.
- **Performance.** The alignment search is still exhaustive: 1.0 s at 11 kanji, 3.2 s with
  okurigana after it, and a word that opens with kana is aligned three times.

Tooling on the current tree (run from the package's parent directory):

| Check | Result |
| --- | --- |
| `python -m pytest jp_text_processing` | 2601 passed, 240 skipped, 1 xfailed, 7 s |
| `mypy --config-file jp_text_processing/pyproject.toml -p jp_text_processing` | clean, 64 files |
| `pyflakes` (outside `mecab_controller/`) | clean |
| `ruff check` with pyupgrade/isort/simplify/bugbear rules | 90 findings, 80 auto-fixable, 1 real (`B018`, see L7) |

The 240 skips are modes a `kana_highlight` case gives no expectation for, by design. The one
xfail is the colloquial 無[ねえ] word-highlight case, marked strict.

---

## High severity

### H1. The okurigana-mix cleaning regex reads past the closing bracket and corrupts the next word

`okuri/okurigana_mix_cleaning_replacer.py:133` and `:136`: the reading groups are `(?P<furi1>.+)`
and `(?P<furi2>.+)`. `.` matches `]`, and `furi1` is deliberately greedy (the comment below the
pattern explains why: `hira1` has to be the *last* occurrence of that kana in the reading). Greedy
`.+` therefore also matches across `]` and the words after it, and stops at the last place in the
whole text where `hira1` is followed by `]`. Two words in one sentence whose okurigana ends in the
same kana are enough:

```
kana_filter("彼は 見え[みえ]ない 所[ところ]で 消え[きえ]た")
  -> "彼はみえないところで 消え[き]えた"       (bracket and kanji left in the kana output)
kana_highlight("", "これは 上げ[あげ]て 下げ[さげ]る", "furigana")
  -> "これは<kun> 上[あげ]</kun>て 下げ[さ]げる"  (上げ mis-split, 下げ left unprocessed)
kana_filter("食べ[たべ]たい 食べ[たべ]る")
  -> "たべたい 食べ[た]べる"
```

The first word gets the whole span up to the other word's bracket as its reading, and the second
word is rewritten into a form nothing downstream recognises. `kana_filter` is the add-on's
replacement for Anki's kana filter, so this reaches every card that has two such words on a line.
Only words with okurigana before the bracket trigger it, but those are the common verb and
adjective forms.

**Fix (verified, 2601 pass):** bound both groups to the bracket, `(?P<furi1>[^\]]+)` and
`(?P<furi2>[^\]]+)`. Greediness within the bracket is unchanged, so 勿体無い[もったいない] and
行き来[いきき] still split as the comment describes. Add the three inputs above as cases in
`okurigana_mix_cleaning_tests.py` and `kana_filter_tests.py`; nothing in either suite currently has
two mixed-okurigana words in one text.

### H2. `word_highlight` raises on a one-kana word that is not in the text verbatim

`word/highlight_inflected_words_with_mecab.py:59-63`: `word_stem = base_form_word[:-1]` is empty
for a one-character word, and `is_katakana_str("")` in the submodule raises `ValueError: string
can't be empty`. The path is reached whenever the kana-only branch of `word_highlight` fails its
plain regex search, which is any one-kana word not present in the text:

```
word_highlight("これは犬です", "ね")   -> ValueError
word_highlight("食べた", "る")         -> ValueError
word_highlight("ねこ", "ね")           -> "<b>ね</b>こ"   (found verbatim, never reaches mecab)
```

A one-kana word is an unusual thing to highlight, but the entry point is called from card
rendering and an exception there aborts the whole card. Found by fuzzing 3750 random calls; it was
the only exception.

**Fix (verified):** after computing `word_stem`, `if not word_stem: return text`. A one-kana word
has no stem to inflect and the verbatim search has already failed, so there is nothing more to
find.

### H3. A kanji written twice in a row is given the first kanji's match without checking the second

`kana/mora_alignment.py:140` treats `next_kanji == kanji` the same as `々`, and at `:290-292` the
second occurrence gets a copy of the first one's `ReadingMatchInfo` with only `matched_mora`
replaced. The second reading is never matched against the kanji's own readings. That is correct
for 々 (it has no readings of its own) and for a genuine doubled word, but a doubled kanji is just
as often two words meeting, and then the readings differ:

```
毎月月末[まいつきげつまつ] -> <on> 毎[マイ]</on><kun> 月月[つきげつ]</kun><on> 末[マツ]</on>
毎年年末[まいとしねんまつ] -> <on> 毎[マイ]</on><kun> 年年[としねん]</kun><on> 末[マツ]</on>
```

げつ and ねん are onyomi and come out tagged `<kun>`, merged into one chunk with the kunyomi
before them, and never converted to katakana. The existing 生物物理学 case passes only because
both 物 happen to read ぶつ. The unchecked copy can also accept a wrong split: whatever mora the
trial split hands the second kanji is taken as its reading, so the search can exit "complete" on a
split the second kanji would have rejected.

**Fix (verified, 2601 pass, both words above come out `<kun> 月[つき]</kun><on> 月[ゲツ]</on>`):**
when `next_kanji != "々"`, call `match_reading_to_mora` for the second occurrence on `second_mora`
(with `is_last_kanji=(i + 1) == kanji_count - 1` and the same okurigana context) and use that
match if there is one; fall back to the copy only when the second mora matches nothing, which
keeps the doubled-kunyomi words like 各々 that only list the doubled reading. The 々 rewrite rule
(`rendaku_matched` or written 々) can stay as it is.

---

## Medium severity

### M1. A word at the start of a line is not a word start

Both word-boundary lookbehinds are `(?<![^ >])` (`okurigana_mix_cleaning_replacer.py:22` and
`:123`): the character before the word must be a space, a `>`, or nothing. A newline is neither,
so the first word of every line after the first skips leading-kana cleaning and okurigana-mix
cleaning, although the comment on the pattern says a line start counts:

```
kana_filter("行[い]く\n食べ[たべ]る")     -> "いく\n食べ[たべ]る"   (bracket left in the output)
kana_highlight("", "行[い]く\nお前[おまえ]", "furigana")
                                          -> "…\nお<juk> 前[おまえ]</juk>"   (お not taken out)
```

The same inputs with `<br>` instead of `\n` are handled. Anki fields written in the HTML editor
use `<br>`, but fields pasted or imported as plain text carry `\n`.

**Fix (verified):** `(?<![^\s>])` in both patterns.

### M2. The alignment search is exhaustive

Unchanged from the previous review's M4, restated with current numbers because every prefixed
word now pays it three times (H2's fix runs two probe alignments before the real one):

| Input | Time | `check_reading_match` calls |
| --- | --- | --- |
| 東京特許許可局 (7 kanji) | 10 ms | |
| ご協力者募集中 (6 kanji, kana prefix) | 92 ms | three full alignments |
| 国際連合安全保障理事会 (11 kanji, 16 mora) | 1.0 s | 29 500, of which 188 distinct (kanji, chunk, context) |
| 国際連合安全保障理事会…する (okurigana after it) | 3.2 s | 304 700 |

Every (kanji, chunk) pair is re-scored once per split that contains it, about 150 times over for
the 11-kanji word. The best alignment of the rest of the word depends only on which kanji you are
at and where in the mora sequence you are, not on the path taken to get there, so the search is a
dynamic program over (kanji index, mora position): kanji × mora² reading checks instead of
C(mora−1, kanji−1) splits.

Two steps, in order. First an `lru_cache` on `match_reading_to_mora` keyed by kanji, chunk,
okurigana, `is_last_kanji` and the repeater chunk; that alone turns the 29 500 calls into 188 with
no change to the search. Then replace the split enumeration with the memoised recursion. What the
DP has to keep: the repeater lookahead (a kanji followed by 々 is one step that advances two
kanji), the last kanji's `maybe_okuri`, the yōon retry, and the tie-breaking order (today the
first complete alignment in enumeration order wins, and among partials fewest jukujikun then most
characters matched; a DP must define ties the same way or outputs shift). Check it is
output-identical on the full suite before switching. The two probe alignments in
`leading_kana_cleaning_replacer` become cheap with the same change; until then, skip the kept
probe when the stripped one leaves nothing unread and `SELF_READING_PREFIX_REC` matches the
prefix.

Not part of this: `get_conjugated_okuri_with_mecab` is called from `match_onyomi_to_mora` for
every onyomi match of every split (4022 times on the last input above), but the submodule's LRU
cache on `translate` makes that 31 ms of the 3.2 s. Not worth touching before the search is.

### M3. Kana-only word highlighting misses two verb shapes

Both in `highlight_inflected_words_with_mecab`, both known from the previous fix review and still
open:

- **Passive of a verb mecab does not know.** `word_highlight("バズられた", "バズる")` highlights
  nothing. mecab gives バズ/られ/た, `inflected_stem_okurigana_len` walks
  `POSSIBLE_OKURIGANA_PROGRESSION_DICT` for v5r/v1 over られた and finds no `is_last`, so the
  stem is rejected. バズった and バズらない work. Before a1648fd the whole word was bolded.
  Accepting the stem also when the token after it passes `get_all_conjugation_conditions` (られ
  has headword られる and is a verb) covers it and still rejects はしが.
- **Katakana-stem verbs mecab does know.** `word_highlight("サボった", "サボる")` highlights
  nothing. `:60-63` rebuilds `base_form_word` with a katakana ending when the stem is katakana,
  giving サボル, which never equals mecab's headword サボる. The conversion exists for noun-form
  input (バズり → バズる), so apply it only to the noun-form branch, or compare headwords in
  hiragana.

### M4. HTML around a highlighted word is nested or split by the mecab path

`highlight_inflected_words_with_mecab` restores tags by stored index after inserting `<b>`, and
two cases come out wrong:

```
word_highlight("<b>食べた</b>", "食べる")          -> "<b><b>食べた</b></b>"
word_highlight("<span>はしって</span>", "はしる")  -> "<b><span>は</span>しって</b>"
```

The first is what happens when the highlighter is run on its own output; `kana_highlight` strips
existing `<b>` for exactly this reason (`kana/kana_highlight.py:47`) and `word_highlight` does
not. The second is the stem-match path (`stem_okuri_remaining`) closing the highlight inside a
token, which the index bookkeeping in `use_tag_cleaning` does not model. Both are in the branch
`balance_b_tags` was added to protect. Strip `<b>`/`</b>` from the text on entry the way
`kana_highlight` does, and add the `<span>` case to `word_highlight_tests.py`; it is the shape
the add-on produces when a previous run wrapped the word.

---

## Low severity

### L1. `EXISTING_BOLD_TAGS_REC` misses a `<b>` with attributes

`kana/kana_highlight.py:47`, `</?b>`: `<b class="x">漢字[かんじ]</b>` keeps its opening tag and
loses the closing one, leaving `<b class="x"><b>…</b>…` unbalanced. `</?b(?:\s[^>]*)?>` covers it.
Carried over from the previous fix review.

### L2. Number conversion

- `kanji/number_to_kanji.py:164`: the rule that a 千 heading a myriad group keeps its 一 only
  applies when nothing follows the 千: 10000000 → 一千万 but 12000000 → 千二百万 and 1203兆 →
  千二百三兆. Both spellings are acceptable Japanese, but a furigana of いっせんにひゃくまん aligns
  only against one of them. `(?!千[一二三四五六七八九十百]*[万億兆京])` makes it consistent. The
  tests at `number_to_kanji_tests.py:90-103` pin the bare case only.
- `:141-142`: `clean_num_str = num_str.strip()` is overwritten on the next line by a comprehension
  over the unstripped `num_str`, so `" 12 "` is returned as-is. Either strip in the comprehension
  or delete the line.

### L3. `verb_conjugation_conditions` finds a token's neighbours by value

`okuri/mecab_common.py:48`, `all_tokens.index(token)`. `MecabParsedToken` is a frozen dataclass
with value equality, so a token that appears twice in the text resolves to the first occurrence
and `prev_token`/`next_token` are the wrong neighbours. Only the で rule (`next_token.headword ==
"いる"`) reads a neighbour whose identity matters; a probe with two で in one text
(`急いで 読んでいる`) still came out right because いる is checked by its own previous token. Latent;
pass the index from the caller's loop instead.

### L4. Exception handling inside `process_jukujikun_positions` has two rough edges

`kana/jukujikun_processor.py:198-243`:

- The loop mutates the caller's alignment (`jukujikun_positions.append`, `kanji_matches[0] =`),
  which the docstring does not say and `kana_highlight` does not expect (it reads
  `alignment["jukujikun_positions"]` again afterwards).
- `:230-243` gives an unmatched kanji in front of an exception a synthetic *onyomi* match for the
  prefix kana, but leaves its index in `jukujikun_positions`, so the redistribution still assigns
  it a `<juk>` entry. The entry wins for the tag and the synthetic match wins for
  `highlight_match_type`, so a caller asking what kind of reading was highlighted is told onyomi
  for something rendered as jukujikun. No exception word in the table triggers it today (every
  prefix probed, 生真面目, 不真面目, 白薔薇, 大風邪, matched a real reading); either drop the block
  or remove the index from `jukujikun_positions` when it fires.

### L5. Degenerate furigana produces empty tags and empty brackets

Too few mora for the kanji is handled without crashing, but the output has holes:

```
kana_highlight("国", "国際連合[こ]", "furigana")   -> <b><juk> 国[こ]</juk></b><juk> 際連合[]</juk>
kana_highlight("国", "国際連合[こ]", "kana_only")  -> <b><juk>こ</juk></b><juk></juk>
kana_highlight("漢", "漢字[]", "kana_only")        -> ""            (the word disappears)
```

`construct_wrapped_furi_word` already merges an entry with empty furigana into the one before it
(`:145-152`) but only inside one segment; the highlight boundary splits these into separate
segments. The last case is the empty-furigana branch of `furigana_replacer` returning the (empty)
furigana in kana-only mode; returning the kanji would at least keep the text.

### L6. Every run of two spaces anywhere in the text is collapsed

`kana/kana_highlight.py`, end of `kana_highlight`: `re.sub(r" {2}", " ", processed_text)` runs on
the whole output, including spaces the caller had in plain text, and only collapses pairs (three
spaces become two). Carried over. Limit it to the space the reconstruction adds, i.e. replace
` ` + ` <tag>` at the seams rather than any double space.

### L7. Small defects

- `okuri/check_okurigana_for_inflection.py:33`: a bare `maybe_okuri` expression statement, the one
  real ruff finding (`B018`).
- `kana/kana_highlight.py:517`: the docstring of `kana_highlight` sits after the `if with_tags_def
  is None` block, so it is a string expression, not the function's docstring (`help()` and IDEs
  show nothing).
- `kana/construct_wrapped_furi_word.py:226-229`: both arms of `if return_type == "kana_only"` build
  the same string.
- `word/word_highlight.py:666`: the final `return text` is unreachable; every branch above returns.
- `kana/kana_highlight.py`, `is_whole_word_case` → `whole_word_mora_split` is called with
  `full_word` while the alignment runs on `alignment_word` (digits converted). They agree today
  only because a one-character word converts to one kanji.
- 80 of the 90 ruff findings are import order and `Optional[X]` → `X | None`; all auto-fixable,
  none behavioural. Worth one `ruff --fix` commit, and a `[tool.ruff]` section in `pyproject.toml`
  so the rule set is the repo's rather than whatever the environment has.

### L8. Import-time side effects and shared state

Carried over: `okuri/mecab_common.py:20` starts a `MecabController` and `kanji/all_kanji_data.py:17`
loads the JSON when the modules are imported, so importing the package to use `number_to_kanji`
pays for both; and `MecabController._cache` (`mecab_controller/mecab_controller.py:59`) is a
class attribute, one cache for every instance. Neither matters inside Anki, both matter for tests
and any second embedding.

### L9. Heuristics carried over

- `okuri/mecab_common.py:32`: a noun ending in か is a na-adjective (静か yes, but also 誰か,
  何か, 幾つか).
- `okuri/okurigana_dict.py:1513`: the empty-okurigana marker (for 恥ずかし気な) is added to every
  part of speech, so a verb stem with nothing after it scores `empty_okuri` too.
- `regex/kanji_furi.py:7`: `KANJI_CHAR_RE` stops at the BMP and Extension A; 〆, 〇 and Extension
  B+ kanji are not kanji to the furigana regexes and their brackets are left untouched.

---

## Design observations

### D1. Special cases live as code in four places

Kanji-specific behaviour is written into the functions that hit it: 久/仄々/為/抉 in
`get_conjugated_okuri_with_mecab.py:54,83-93`, 為 again in `reading_matcher.py:268` and
`jukujikun_processor.py:296`, 見/着/煮/似/干/居/射/鋳 and 行/呉/有/在 in
`okurigana_dict.get_part_of_speech`, and the whole-word/exception table in
`furigana_exceptions.py`. Each was added for one test case. One table keyed by kanji (or word +
reading) with the override as data, consulted from one place, would make the next case a row
rather than a branch, and would make it possible to see what is special-cased at all.

### D2. The word highlighter and the furigana highlighter disagree about HTML

`kana_highlight` strips `<b>` on entry and re-adds its own; `word_highlight` keeps the caller's
tags out of the way by index bookkeeping (`use_text_part_storage`, `use_tag_cleaning`,
`use_splitter_dot_cleaning`, ~450 lines) and then repairs crossings after the fact
(`balance_b_tags`, `apply_tag_fixes`). M4 and L1 are both consequences. The bookkeeping exists so
that `<b>` can be placed by character offset into text that still contains tags; an alternative
is to tokenise the text into (tag | text) runs once, run the matching over the concatenated text
runs with a run map, and insert `<b>` by run rather than by offset. That is a rewrite of the word
side only and would retire three helper modules.

### D3. `silenced()` is a global switch

`utils/logger.py`: the probe in `unread_kanji_count` disables the package logger for everyone,
including errors from unrelated threads and the whole `process_mora_split` under it. Fine inside
Anki's single thread; if the package is ever called from a worker, replace it with a logger
adapter or a filter that drops records from the probe's own frames.

### D4. No CI and no declared dev dependencies

`pyproject.toml` now documents how to run the suite and why from the parent directory, which is
the right place for it; but there is no `.github/workflows`, no `requirements-dev.txt` or
`[project.optional-dependencies]` naming pytest/mypy/ruff, and `README.md` does not mention tests
at all. With the suite at 7 s and exit codes correct, a workflow that runs pytest and mypy on push
is a small addition and would have caught H1 the day it was written, had the case existed.

### D5. Test suite shape

The conversion to pytest is thorough and the ids are readable. Two things would pay off:

- The suites that exercise the cleaning regexes have no multi-word inputs; H1 and M1 are both
  "two words in one text" bugs. A handful of sentence-level cases in `kana_filter_tests.py` would
  cover them.
- `kana_highlight_tests.py` runs nine modes per case but skips the ones a case does not specify,
  240 today. A skipped mode is still a mode the case runs through untested; filling in the
  expectations for the ones that matter (kana-only for every furigana case, at least) would turn
  those skips into coverage.

---

## Status of the previous review's findings

| Old | Status now |
| --- | --- |
| H1 reading order scrambled | Fixed (a7afa09, d9327db). |
| H2 leading kana stripped | Fixed (864e2fd). The extra probes' cost is in M2 here. |
| H3 `[sound:…]` destroyed | Fixed (83ce57e). |
| H4 一万/一億 | Fixed (ec910d3); the 千二百万 inconsistency is L2 here. |
| H5 kana-only highlight matched any stem | Fixed (a1648fd, 61cf286); the バズられた regression is M3 here. |
| M1 long vowel mark | Fixed (5ba21b1). |
| M2 neighbours by value | Still latent, L3 here. |
| M3 nested `<b>` | Fixed for `kana_highlight` (772aa85); attributes are L1, `word_highlight` is M4. |
| M4 exhaustive search | Open, M2 here. |
| M5 tests cannot fail CI | Fixed (2df474b and the pytest conversion). |
| M6 mypy 197 errors | Fixed (1a9f76e, 7787e4a): clean with the repo config. |
| M7 multi-character `kanji_to_highlight` | Fixed (3f3d381). |
| M8 dual imports, generic package names | Imports fixed (ea65189). Package names unchanged; harmless now that every import is relative. |
| L1 double spaces | Open, L6 here. |
| L2 mutation / unbound variable | Unbound variable fixed (1fa819a); mutation open, L4 here. |
| L3 dead code | Fixed (d3f4bd0). |
| L5 empty-okuri marker | Open, L9 here. |
| L6 kanji class gaps | Open, L9 here. |
| L7 import-time side effects | Open, L8 here. |
| L8 logging | Fixed (76f9d7b, 9f577bb, 52cbfea). |
| L9 na-adjective heuristic | Open, L9 here. |
| D1 packaging | Partly: `pyproject.toml` exists; CI and dev deps are D4 here. |
| D5 test suite shape | Fixed; follow-ups in D5 here. |

## Suggested order of work

1. **H1**, one line, verified; add the sentence cases with it.
2. **H2**, one guard, verified.
3. **M1**, two characters, verified; belongs in the same commit as H1 since it is the same pair of
   patterns.
4. **H3**, verified; the only one of the four that changes alignment output, so run the suite
   after it on its own.
5. **M3** and **M4** together, both in `highlight_inflected_words_with_mecab`.
6. **M2** in two steps as described, measuring after the cache before deciding on the DP.
7. `ruff --fix`, L7's four small edits, and a CI workflow (D4) so the next regression is caught.
