# Code review: jp_text_processing

Reviewed at commit `782a5bc` (main, 2026-09-17). Scope: every tracked file in the repository, the
bundled `mecab_controller` submodule read for context only. Nothing in this report changes code;
each finding was verified by reading the code and, where it says so, by running it.

## Summary

The library does a hard job well most of the time: 1874 kana_highlight test cases pass, the other
test scripts pass, and the alignment/okurigana pipeline handles a large number of awkward Japanese
cases. The problems are concentrated in a few places:

- **Five high-severity correctness bugs** that produce wrong furigana or wrong highlights on
  plausible input: reading order gets scrambled around a partially matched word, a particle in
  front of a word is stripped out of the kanji reading, `[sound:...]` tags are destroyed,
  `一万`/`一億` lose their `一`, and kana-only word highlighting matches unrelated words.
- **The test scripts cannot fail CI.** Most of them call `sys.exit(0)` on failure and the main
  suite never sets a non-zero exit code, so a red run looks green to any automation.
- **Structural debt**: a dual import scheme repeated in every file, generic top-level package
  names, stale type definitions, ~600 lines of dead code, and an exhaustive alignment search that
  reaches one second per word at 11 kanji.

Tooling results on the current tree:

| Check | Result |
| --- | --- |
| `kana/kana_highlight_tests.py` | 1874 cases pass, 1.2 s |
| `kana/kana_filter_tests.py`, `check_word_reading_type_tests.py`, `okuri/okurigana_mix_cleaning_tests.py`, `word/word_highlight_tests.py` | pass |
| Inline `main()` tests in 7 library modules | pass |
| `ruff check --select E,F,B,W` | 44 findings (32 are `B008` mutable-default `Logger(...)`) |
| `pyflakes` | 7 findings (unused imports, unused `nonlocal`) |
| `mypy --ignore-missing-imports` | 197 errors in 36 files |

There is no `pyproject.toml`, `requirements.txt`, CI config, or lint config in the repo, so the
tool runs above used default settings.

---

## Fix review (main at 61cf286, 2026-09-17)

Nine commits on main address H1–H5, M1, M3 and M7. Each was checked against its original
failing input, against the pre-fix code (c5f1edb) on the same inputs, and by the four touched
test suites, which all pass (`kana_highlight_tests` now 2168 cases).

| Finding | Commit | Verdict | Notes |
|---|---|---|---|
| H1 | a7afa09 | Fixed | Per-run redistribution. `kana_only` output round-trips the furigana in order on every crafted input (`山川保田[ぱぴぷほぺぽ]`, two runs, runs at both ends). |
| H2 | 864e2fd | Fixed, with a cost | `か家族[かぞく]`, `も紅葉[もみじ]` correct; every お/ご/katakana/multi-kana prefix probed is unchanged from before. Each prefixed word now runs two extra alignments, and the spelling that is wrong always fails, so it takes the exhaustive path (M4): the 6-kanji `ご協力者募集中` went from 22 ms to 107 ms. Cheap short-circuit: when the stripped probe leaves 0 unread and `SELF_READING_PREFIX_REC` matches the prefix, skip the kept probe. |
| H3 | 83ce57e | Fixed | Whole match returned for every return type. |
| H4 | ec910d3 | Fixed, rule applied inconsistently | 一万, 一億, 一千万 correct. Brute force against a reference over 50 000 numbers found one systematic deviation: a 千 that heads a myriad group keeps its 一 only when nothing follows it before the unit. 1000万 → 一千万 but 1200万 → 千二百万 and 1203兆 → 千二百三兆. The commit message says a 千 topping a 万-group keeps it; the lookahead `(?!千[万億兆京])` only covers the bare case. If 一千二百万 is intended, use `(?!千[一二三四五六七八九十百]*[万億兆京])`. Either convention is acceptable Japanese, but a furigana like いっせんにひゃくまん will only align under one of them. |
| H5 | a1648fd, 61cf286 | Fixed, one regression | はし/あめ no longer highlight, はしらないで still does, バズった and バズってる are bolded whole. **Regression:** `バズられた` (passive of an unknown verb) was fully highlighted before and is not highlighted at all now. mecab gives バズ/られ/た and `POSSIBLE_OKURIGANA_PROGRESSION_DICT` has no `is_last` on ら→れ→た for v5r or v1, so the stem is rejected. Accept the stem also when the next token passes `get_all_conjugation_conditions` (られ has headword られる and is a verb); that keeps はしが rejected. Limitation, not a regression: `バズっている` stops at って because mecab tokenizes って as one particle and the ている rule in `verb_conjugation_conditions` wants the previous token to be exactly て/で, while 食べている is bolded whole. |
| M1 | 5ba21b1 | Fixed | Every one of the 82 `LONG_VOWEL_MAP` entries now matches its gojūon row (checked programmatically). とーきょー, せんせー, けーざい, ぎゅーにゅー, おーきい all match. |
| M3 | 772aa85 | Fixed, two caveats | Design choice to be aware of: every `<b>` in the text is stripped, including the caller's emphasis on unrelated words (`<b>今日</b>は 食[た]べる` → `今日は …`). Bug: `</?b>` misses tags with attributes, so `<b class='x'>食[た]</b>べる` keeps the opening tag and loses the closing one, leaving unbalanced HTML. `</?b(?:\s[^>]*)?>` would cover it. |
| M7 | 3f3d381 | Fixed | 漢字, 生物 in 生物学, 物理 in 生物物理学 highlight correctly in all return types; `人々` as `kanji_to_highlight` now highlights (it did not before). Single-kanji and repeater words are identical to before on every probe. |

M2 stays latent (see below); M4, M5, M6, M8 and the Low/Design items are untouched.

Noticed while verifying, pre-existing and not caused by these commits:

- `highlight_inflected_words_with_mecab` loses or misplaces HTML tags that wrap the highlighted
  word: `あ<span>食べた</span>` → `あ<b>食べた</b>` (span gone), `<span>はしって</span>` →
  `<b><span>は</span>しって</b>`. A space inside the word breaks the same bookkeeping:
  `食べ た` → `<b >食べた</b>`.
- Katakana-stem verbs that mecab knows never highlight: `サボった`/サボる, `ミスった`/ミスる.
  `base_form_word` is rebuilt with a katakana ending (サボル), which never equals mecab's headword
  サボる, and the hiragana retry (さぼる) does not either. ググる only works because mecab does
  not know it and the stem path takes over.

## High severity

### H1. Reading order is scrambled when a matched kanji sits between unmatched kanji

`kana/jukujikun_processor.py:209-261` (`process_jukujikun_positions`, fallback redistribution).

When an alignment is partial, the code concatenates the mora of every unmatched position into one
string, re-splits it, and deals it out evenly across the jukujikun positions. It ignores where the
matched kanji sits, so mora that belong after the matched kanji can be dealt to positions before it.

Verified:

```
kana_highlight("", "山川保田[ぱぴぷほぺぽ]", "kana_only", WithTagsDef(False, False, False, False))
-> 'ぱぴぷぺほぽ'      # input reading was ぱぴぷほぺぽ: ほ and ぺ have swapped
kana_highlight("", "国際連合安全保障理[ぱぴぷぺぽぱぴぷぺぽぱぴぷぺ]", "kana_only", ...)
-> 'ぱぴぷぺぽぱぴぷぺぱぴぽぷぺ'   # 保 kept its ぽ, two later mora moved in front of it
```

Any word where reading matching succeeds for a middle kanji but fails on both sides (unknown
reading, misspelt furigana, kanji missing from `all_kanji_data.json`) silently reorders the
learner's reading. `kana_only` output, which is what a card shows, is affected directly.

Fix: redistribute per contiguous run of jukujikun positions. For each run, take only the mora that
`alignment["mora_split"]` assigned to that run's slots (they are already in order and already
bounded by the neighbouring matched kanji), and deal those out. Never pool mora across a matched
position.

### H2. Leading-kana cleaning strips particles out of the kanji reading

`okuri/okurigana_mix_cleaning_replacer.py:506-537` (`LEADING_KANA_CLEANING_REC`,
`leading_kana_cleaning_replacer`), applied in `kana/kana_highlight.py:1123`.

The pass exists for お前[おまえ] and スペイン語[すぺいんご]. Its only guard is "the reading starts
with the same kana", which any particle or leading kana that happens to share the kanji's first
mora also satisfies.

Verified:

```
kana_highlight("", "か家族[かぞく]と", "furigana")   -> 'か<juk> 家族[ぞく]</juk>と'
kana_highlight("", "が学校[がっこう]に", "furigana") -> 'が<juk> 学校[っこう]</juk>に'
```

The word loses its first mora, fails to align, and is tagged jukujikun. Triggers on any text
where a kana precedes a kanji word without a space at the start of a field, a line, or after a
tag, which is exactly where the lookbehind `(?<![^ >])` allows the match.

Fix: do not strip on a string-prefix test alone. Either restrict `pre` to the prefixes that
genuinely carry their own reading (お/ご/御 honorifics, katakana runs, or an explicit list), or
try the alignment both with and without the prefix removed and keep the one that aligns
completely. The second option is safest because it uses the kanji data as the oracle.

### H3. `[sound:...]` after a kanji is destroyed or read as furigana

`kana/kana_highlight.py:893-946`.

The `startswith("sound:")` guard at line 942 sits after the non-kana cleaning at line 893, which
turns `sound:test.mp3` into an empty string. The invalid-furigana branch then runs instead and the
guard is unreachable. If the filename contains kana, the kana are used as the reading.

Verified:

```
kana_highlight("", "漢字[sound:test.mp3]", "kana_only")   -> '<err>sound:test.mp3</err>'
kana_highlight("", "漢字[sound:test.mp3]", "furigana")    -> '<err> 漢字[sound:test.mp3]</err>'
kana_highlight("", "漢字[sound:かんじ.mp3]", "furigana")  -> '<on> 漢字[カンジ]</on>'
```

`kana_filter` (line 177) does this correctly by checking the raw group first.

Fix: test `match.group(2).startswith("sound:")` on the raw bracket content before any cleaning and
return `match.group(0)` unchanged. Add a test case for each return type.

### H4. Numbers drop the `一` in 一万, 一億, 一兆, 一京

`kanji/number_to_kanji.py:160-164`, with the wrong behaviour asserted by its own tests at
lines 233-242.

The post-processing strips `一` before every unit. That is right for 十/百/千 but wrong for 万 and
above, which always keep `一` (一万円, 一億人). Verified:

```
number_to_kanji("10000")     -> '万'      (expected 一万)
number_to_kanji("10001")     -> '万一'    (expected 一万一)
number_to_kanji("100000000") -> '億'      (expected 一億)
kana_highlight("円", "10000円[いちまんえん]", "furigana")
-> '<kun> 10000[いちまん]</kun><b><on> 円[エン]</on></b>'   # alignment fails, digits tagged <kun>
```

Fix: only strip `一` before 十, 百, 千 (and not before a 千 that itself precedes 万, so 一千万 is
kept). Update the tests at lines 233-242 to the correct readings.

### H5. Kana-only word highlighting matches any token whose headword equals the stem

`word/highlight_inflected_words_with_mecab.py:154-156`:

```python
elif (token.headword == base_form_word and get_word_type_from_mecab_token(token) == word_type
) or token.headword == word_stem:
```

The second clause ignores part of speech. For a verb like はしる the stem is はし, so the noun
はし (橋/箸) is highlighted. Verified:

```
word_highlight("はしをわたる", "はしる", Logger("error")) -> '<b>はし</b>をわたる'
word_highlight("あめがふる",  "あめる", Logger("error")) -> '<b>あめ</b>がふる'
```

Fix: apply the stem clause only when the token is a verb or i-adjective (or when
`get_word_type_from_mecab_token(token) == word_type`), or drop it and rely on headword matching
plus the hiragana/katakana retry.

---

## Medium severity

### M1. Long vowel mark ー is only understood as う

`kana/reading_matcher.py:90` normalises `ー` to `う` and nothing else. Readings written with ー
after an え/い/あ/お vowel do not match. Verified:

```
kana_highlight("生", "先生[せんせー]", "furigana") -> '<on> 先[セン]</on><b><juk> 生[せー]</juk></b>'
kana_highlight("京", "東京[とーきょー]", "furigana") -> correct, because both are う-row
```

`regex/mora.py:194` already has `LONG_VOWEL_MAP` (preceding kana → vowel). Fix: build the
normalised candidate with that map (せー → せえ, and also try せい for the え row, since えい is
usually written ー) instead of a blanket replace.

### M2. `verb_conjugation_conditions` looks up neighbours by value, not position (latent)

`okuri/mecab_common.py:62` uses `all_tokens.index(token)`. `MecabParsedToken` is a frozen
dataclass with value equality, so a repeated token resolves to its first occurrence: on
食べていて見ていて every later て resolves to index 1 and every later い to index 2.

Downgraded after testing. The callers (`get_conjugated_okuri_with_mecab.py:183`,
`highlight_inflected_words_with_mecab.py:132`) stop at the first token that is not accepted, so a
later duplicate is only examined when every earlier token was accepted, and the neighbour-dependent
conditions then give the same answer for the first occurrence as for the real one. An identity-based
lookup was compared against the current code on 24 inputs built to have repeated て/で/いる/ない
tokens in one parse; no output differed. Treat it as a correctness hazard for future conditions,
not a current bug. Fix is still one line: pass the index in from the callers' loops.

### M3. Existing `<b>` tags in the input produce nested `<b>`

`kana/kana_highlight.py:873` says the text is "cleaned from any previous `<b>` tags"; no cleaning
happens. Verified:

```
kana_highlight("字", "<b>漢字[かんじ]</b>", "furigana")
-> '<b><on> 漢[カン]</on><b><on> 字[ジ]</on></b></b>'
```

Re-running the highlighter over its own output (a common Anki workflow) compounds this.

Fix: strip `<b>`/`</b>` before processing, or state in the docstring that the caller must.

### M4. Alignment search is exhaustive and gets slow past ten kanji

`kana/mora_alignment.py:107` enumerates every ordered split via `get_ordered_sublists`
(C(mora-1, kanji-1) splits) and scores each from scratch. Measured with mecab warm:

| Input | Splits tried | Time |
| --- | --- | --- |
| 東京特許許可局 (7 kanji) | – | 12 ms |
| 国際連合安全保障理事会 (11 kanji, 16 mora) | 2588 | 1.06 s |
| same word, reading that matches nothing | – | 1.36 s |

The profile shows 295k `check_reading_match` calls for that one word, and 25k
`match_kunyomi_to_mora` calls each of which re-parses the reading string and rebuilds candidate
lists. On top of that every `logger.debug(f"... {alignment}")` formats a full dict repr even when
debug is off (`utils/logger.py` takes the finished string).

Fix, in order of payoff:
1. Memoise `match_reading_to_mora(kanji, mora_sequence, okuri)` for the duration of one
   `find_first_complete_alignment` call; the same (kanji, substring) pair is scored hundreds of
   times across splits.
2. Replace the enumerate-all-splits loop with a left-to-right DP over mora positions (for each
   kanji, for each end position, best alignment so far). This is polynomial and gives the same
   "first complete / best partial" answer.
3. Make debug logging lazy (`logger.debug(lambda: ...)` or check `logger.level` first) in the hot
   loops of `mora_alignment.py` and `reading_matcher.py`.

### M5. The test scripts cannot fail a CI run

- `kana/kana_highlight_tests.py:main` prints "N test cases failed" and returns; the process exits 0.
- `sys.exit(0)` on assertion failure: `kana/construct_wrapped_furi_word.py:484`,
  `okuri/get_conjugated_okuri_with_mecab.py:420`, `okuri/starts_with_okurigana_conjugation.py:305`,
  `kanji/number_to_kanji.py:261`, `word/word_up_to_okuri.py:299`, `word/word_highlight_tests.py:40`,
  and `exit(0)` in `kana/check_word_reading_type_tests.py:36`.
- Only `kana_filter_tests.py`, `okurigana_mix_cleaning_tests.py`, `use_tag_cleaning.py`, and
  `use_text_part_storage.py` exit 1 on failure.
- `ignore_fail=True` is used on three cases (two in `kana_highlight_tests.py`, one in
  `word_highlight_tests.py`) to silence known failures without recording them as expected failures.
- `kana/kana_highlight_tests.py:160-193` (`ruff B023`): the `rerun` closures capture `rerun_args`
  and `diff` late, so the "debug log for first failed test" printed at the end re-runs the *last*
  case of that test, not the one that failed.

Fix: convert the scripts to `unittest` or `pytest` (each `test(...)` call becomes a parametrised
case), exit non-zero on failure, mark the three ignored cases `xfail` with a reason, and add a
one-line CI workflow that runs them. The mecab binary is bundled, so CI needs no system packages.

### M6. Type definitions are out of sync with the code (mypy: 197 errors)

- `all_types/main_types.py:66-90` `FinalResult` declares `highlight_segment_index`, `edge`,
  `match_type`; the code builds it with `highlight_segment_indices`, `highlight_match_type`,
  `restored_chars` (`kana/kana_highlight.py:809-819`) and reads those with `.get(...)`
  (`kana/kana_highlight.py:266-273`), so the TypedDict guarantees nothing.
- `YomiMatchResult` documents an `all_readings_processed` field that does not exist; the only
  function using the type (`handle_furigana_doubling`, line 584) reads `match_type` which is not
  a field either. Both are dead code (see L3).
- `WrapMatchEntry` requires `is_noun_suru_verb` but `kana/construct_wrapped_furi_word.py:114-204`
  and `kana/kana_highlight.py:771-777` build entries without it (8 mypy errors).
- `kana/kana_highlight.py:1077`: `juku_parts: dict[int, str]` is actually
  `dict[int, WrapMatchEntry]`.
- `okuri/get_conjugatable_okurigana_stem.py:25`: `CONJUGATABLE_LAST_OKURI: set[str]` is assigned a
  `dict_keys`. It is also unused.
- `okuri/okurigana_dict.py:213-242`: declared return `tuple[dict | None, PartOfSpeech]` but
  returns `(None, None)`.

Fix: make `FinalResult` match reality (or drop it and pass a dataclass), make
`is_noun_suru_verb` `NotRequired`, and add mypy to CI once the import scheme (M8) stops producing
"already defined" noise.

### M7. Multi-character `kanji_to_highlight` takes the whole-word path and breaks alignment

`kana/kana_highlight.py:980-986` treats `full_word == kanji_to_highlight` as a whole-word case and
`whole_word_mora_split` (line 830) returns one mora slot for a multi-kanji word. Verified:

```
kana_highlight("漢字", "漢字[かんじ]", "furigana")
-> prints "[ERROR] find_first_complete_alignment - mora_split contains fewer parts than kanji_count"
-> '<juk> 漢字[かんじ]</juk>'
```

The docstring says `kanji_to_highlight` "should be a single kanji character", but the invalid-
furigana branch at line 910 explicitly supports multi-character values, and `word_highlight`
passes `""`. Fix: validate at entry (`len(kanji_to_highlight) <= 1` or raise), and make the
whole-word shortcut condition `len(full_word) == 1 or word_is_repeated_kanji`.

### M8. Dual import scheme and generic top-level package names

Every module repeats this block up to ten times:

```python
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger
```

Consequences observed:
- `mypy` reports "Name already defined (possibly by an import)" for each block, which is most of
  the 197 errors and hides the real ones.
- A real `ImportError` inside a dependency (for example the bundled mecab binary missing at
  `mecab_controller/mecab_exe_finder.py:35`, which asserts at import time) is caught and re-raised
  as a misleading relative-import error.
- The first form imports top-level packages named `kana`, `word`, `kanji`, `okuri`, `regex`,
  `utils`, `test`. `regex` is a widely installed PyPI package and `utils` is the most common
  accidental module name in any environment; whichever is found first on `sys.path` wins, silently.
  When both forms resolve (repo root on `sys.path` and the repo imported as a package) the same
  module is loaded twice under two names, so module-level state such as the mecab singleton and
  the caches is duplicated.
- The scheme is not even consistent: `kana/kana_highlight.py:5` and
  `okuri/check_okurigana_for_inflection.py:2-9` use plain relative imports, while
  `okuri/get_conjugated_okuri_with_mecab.py:174` and the `word/` modules use a third variant
  (`from mecab_common import ...`, no package prefix).

Fix: add a `pyproject.toml` that declares the package (`jp_text_processing`), use relative imports
everywhere, and run tests with `python -m jp_text_processing.kana.kana_highlight_tests` (or
pytest) from the parent directory. `test/run_with_setup.py` and its `.vscode` glue then go away.

---

## Low severity

### L1. Double spaces anywhere in the text are collapsed

`kana/kana_highlight.py:1130` runs `re.sub(r" {2}", " ", processed_text)` over the whole output,
including HTML the caller owns. Verified: `"<pre>a   b</pre> 漢字[かんじ]"` comes back with
`a  b`. Fix: collapse only the spaces the reconstruction itself introduces (the leading space in
`render_segment`), not the entire string.

### L2. `process_jukujikun_positions` mutates its input and has an unbound-variable path

- `kana/jukujikun_processor.py:174-197` appends to `alignment["jukujikun_positions"]` and
  overwrites `alignment["kanji_matches"][0]` on the alignment passed in. The caller then reads the
  same object (`kana/kana_highlight.py:1095`), so the function's effect depends on call order.
- Lines 217-229: if the `try` at 217 raises, `juku_mora_str` is never assigned, and the
  `logger.debug(f"... {juku_mora_str}")` on line 229 raises `NameError` regardless of log level.
  Not reachable today (the only way in is `mora_split=None`, which the fallback at
  `mora_alignment.py:399-411` produces only when both inputs are missing), but the handler is wrong.

### L3. Dead code (about 600 lines)

Unreferenced anywhere outside their own definitions (checked with grep over all `.py` files):

- `kana/kana_highlight.py`: `re_match_from_right/left/middle` (128-137), `onyomi_replacer`,
  `kunyomi_replacer` (140-157), `furigana_reverser` (193-210), `REPLACED_FURIGANA_*_RE` (213-215),
  `apply_katakana_conversion` (218-246), `is_reading_in_furigana_section` (411-520),
  `process_kunyomi_match` (523-546), `handle_furigana_doubling` (549-599),
  `JUKUJIKUN_KUNYOMI_OVERLAP` (119-125), `SMALL_TSU_POSSIBLE_*`/`VOWEL_CHANGE_DICT_*` (102-113,
  duplicates of `reading_matcher.py:40-47`).
- `regex/onyomi.py`: the whole file (438 lines).
- `regex/kanji_furi.py`: `KANJI_RE_OPT`, `FURIGANA_NO_GROUPS_*`, `KANJI_AND_REPEATER_*`,
  `HIRAGANA_RE`, `KATAKANA_REC`.
- `kana/katakana_positions.py:convert_positions_to_katakana`.
- `okuri/check_okurigana_for_inflection.py:check_any_okurigana_for_inflection` (also has an
  off-by-one: `range(len(maybe_okuri) - 1)` never tries the full string).
- `okuri/okurigana_dict.py`: `ONYOMI_GODAN_SU_FIRST_KANA`; `okuri/get_conjugatable_okurigana_stem.py`:
  `CONJUGATABLE_LAST_OKURI`.
- `word/word_up_to_okuri.py`: whole module (and `WORD_SPLIT_REC` inside it is unused even there).
- `kana/construct_wrapped_furi_word.py`: `get_tag_order`, `match_tags_with_kanji`, `TagOrder`
  (57-216) are only used by the module's own inline test; production goes through
  `construct_wrapped_furi_word` with entries built by `reconstruct_from_alignment`.
- `all_types/main_types.py`: `YomiMatchResult`, `Edge`, `MoraAlignment.is_complete` is redundant
  with `jukujikun_positions` being empty (and `kana_highlight.py:1079` tests both).

### L4. Small defects

- `okuri/check_okurigana_for_inflection.py:46`: bare `maybe_okuri` expression statement (ruff B018).
- `kana/construct_wrapped_furi_word.py:423-427`: both branches of the `if` are identical.
- `kanji/number_to_kanji.py:140-141`: `clean_num_str = num_str.strip()` is overwritten on the next
  line using the unstripped `num_str`, so `" 12"` is not converted.
- `kana/kana_highlight.py:862-875`: the docstring sits after the first statement, so it is a
  no-op string expression and `help(kana_highlight)` is empty.
- `kana/kana_highlight.py:884`: `nonlocal kanji_to_highlight` is never assigned.
- `word/word_up_to_okuri.py:251`: `import re` inside the function, already imported at the top.
- `okuri/starts_with_okurigana_conjugation.py:248`: `not x in y` (ruff E713).
- `word/word_highlight.py:254`: `word[: -len(ending_okurigana)]` with an empty
  `ending_okurigana` is `word[:-0]`, i.e. `""`. Harmless today because the branch that follows
  uses `word`, not `word_without_furigana`.
- `word/word_highlight.py:210`: `text=None` is returned as `None` although the signature says `str`.
- `okuri/okurigana_dict.py`: 12 duplicate tuples in `ALL_OKURI_BY_PART_OF_SPEECH` (e.g.
  `(28, "られます")` twice). Harmless, but a sign the table is hand-maintained.

### L5. The empty-okurigana marker is added for every part of speech

`okuri/okurigana_dict.py:1522-1527` calls `add_char_dict("", ..., is_last=True)` inside the loop
for every entry, so `okuri_dict[""]` is `{"is_last": True}` for every POS. The dedicated
`(1, "")` entry at line 267 and the guards `not okuri_dict[""]` at
`starts_with_okurigana_conjugation.py:248` and `:278` are therefore dead, and any unmatched
suffix yields `"empty_okuri"` rather than `"no_okuri"`:

```
starts_with_okurigana_conjugation("かた", "む", "読", "よ")
-> OkuriResults(okurigana='', rest_kana='かた', result='empty_okuri', part_of_speech='v5m')
```

Downstream this scores as priority 1 instead of 0 in `match_kunyomi_to_mora` (line 433-438). It
happens to work for noun forms like 読み方 but the semantics are not what the code claims. Fix:
add the `""` marker only for the POS values that allow a bare stem (adj-i for 〜気な, verb
noun forms), and add a test that a verb with a non-conjugation suffix returns `no_okuri`.

### L6. Kanji character class gaps

`regex/kanji_furi.py:7` (`KANJI_CHAR_RE`) and the copies in `word/word_highlight.py:44-52` and
`kana/make_furigana_from_reading.py:9`:

- CJK Extension B and later (U+20000+) are not matched. Verified:
  `kana_highlight("", "𠮷野[よしの]", "furigana")` gives `'𠮷<juk> 野[よしの]</juk>'`, the kanji is
  pushed outside the bracket. 𠮷 appears in common surnames.
- 〇 (U+3007, used in numbers like 二〇二六) and 〆 are not kanji here.
- `\d` accepts every Unicode decimal digit but `replace_numeric_substrings` only converts
  `[0-9０-９]`, so `३月[さんがつ]` logs "Kanji data not found" twice and tags the digit `<kun>`.
- `all_kanji_data.json` has no entry for `々`, so a word starting with 々 logs an error.

Fix: one shared character class including `\U00020000-\U0003134F`, 〇, 〆; restrict digits to
`[0-9０-９]`; and reference that class from `word_highlight.py` and `make_furigana_from_reading.py`
instead of retyping it.

### L7. Import-time side effects

- `okuri/mecab_common.py:34` constructs `MecabController()` at import. Importing
  `kana.kana_highlight` therefore requires the mecab binary to exist (asserted in
  `mecab_exe_finder.get_bundled_executable`) and `chmod`s it, before any text is processed.
  Anything that only wants `kana_filter` or `number_to_kanji` pays this too.
- `kanji/all_kanji_data.py:15` loads a 1 MB JSON at import.
- `Logger("error")` is evaluated as a default argument in 32 signatures (ruff B008); every function
  shares one instance, so setting a level on it in one place changes it everywhere.

Fix: a lazy `get_mecab()` singleton, a lazily loaded kanji table, and `logger: Logger | None = None`
with a module-level default.

### L8. Logging

`utils/logger.py` is a 35-line reimplementation that prints coloured strings to stdout. Library
code emits `[ERROR]` lines to stdout for ordinary inputs (any kanji absent from the table, any
multi-character `kanji_to_highlight`), which inside Anki go to the console or nowhere. Every
`logger.debug(f"...")` call formats its argument eagerly (see M4). Fix: use `logging` with a
`jp_text_processing` logger; callers configure handlers, `isEnabledFor(DEBUG)` guards the
expensive reprs.

### L9. `get_word_type_from_mecab_token` na-adjective heuristic

`okuri/mecab_common.py:46` classifies any noun ending in か as a na-adjective (intended for 静か).
Nouns such as ほか, なにか, いつか, and anything that is a question word plus か, are then treated
as taking な as okurigana. Fix: use mecab's `形容動詞語幹` subclass (`%f[1]`) instead of the last
kana.

---

## Design observations

### D1. Packaging and developer workflow

There is no `pyproject.toml`, no declared dependencies, no lock file, no CI, no lint or type-check
configuration, and the README covers two functions in six lines. Tests are run through a custom
launcher (`test/run_with_setup.py`) that `exec`s a file with a synthetic `__package__`, wired up
via checked-in `.vscode` files. All of that exists to work around M8. A package definition plus
`pytest` removes the launcher, the VS Code glue, and the try/except import blocks in one change.

### D2. Module boundaries and duplication

- `kana/kana_highlight.py` is 1133 lines, 285 of them in one nested closure (`furigana_replacer`,
  lines 877-1120) that reads eleven variables from the enclosing scope. It also contains the dead
  first-generation matcher (L3). Splitting it into `parse → normalise → align → reconstruct` as
  top-level functions with explicit arguments would make the pipeline testable piece by piece.
- Constants are defined in more than one place: `SMALL_TSU_POSSIBLE_HIRAGANA` and
  `VOWEL_CHANGE_DICT_HIRAGANA` in both `kana_highlight.py` and `reading_matcher.py`; the kanji
  character class retyped five times across `regex/kanji_furi.py`, `word/word_highlight.py` (four
  regexes), and `kana/make_furigana_from_reading.py`; the katakana-position restore loop appears
  in both `reconstruct_furigana` (`kana_highlight.py:288-303`) and `construct_wrapped_furi_word`
  (`:380-394`).
- `all_types/main_types.py` mixes result types with a duplicated `PartOfSpeech`/`PARTS_OF_SPEECH`
  pair that must be kept in sync by hand.

### D3. Special cases are scattered as code, not data

Word- and kanji-specific exceptions live in at least six places: `為` in
`reading_matcher.py:284`, `jukujikun_processor.py:253`, `get_conjugated_okuri_with_mecab.py:242`
and `okurigana_dict.py:170`; `久/仄々/抉` in `get_conjugated_okuri_with_mecab.py:242-279`;
`行/呉/有/在/見/着/煮/似/干/居/射/鋳` in `okurigana_dict.py:167-200`; whole-word overrides in
`furigana_exceptions.py`; `JUKUJIKUN_KUNYOMI_OVERLAP` (dead) in `kana_highlight.py`. Each new
exception means finding the right `if` in the right file. One exceptions table keyed by
(kanji, reading) with a documented precedence would make these reviewable and testable.

The exception dictionary itself (`furigana_exceptions.py:38`) is keyed by a `"word_furigana"`
string that `jukujikun_processor.py:156` splits back apart on `_`; a tuple key avoids the parsing.
`process_jukujikun_positions` also scans every exception with substring tests on every call
(line 153), which is fine at 16 entries and will not be at 500.

### D4. Mutable shared state

The mecab controller is a module singleton with a class-level LRU cache shared by every instance
(`mecab_controller/mecab_controller.py:53`); `process_jukujikun_positions` edits the alignment it
is handed (L2); `Logger` instances are shared through default arguments (L7). None of this is a
problem for single-threaded Anki use, but it makes the functions order-dependent and hard to test
in isolation.

### D5. Test suite shape

The 1874-case suite in `kana_highlight_tests.py` is the project's real asset. Its weaknesses are
mechanical: exit codes (M5), one giant `main()` with 235 `test(...)` calls instead of discoverable
cases, no assertion that a case ran without `[ERROR]` output (H1 and M7 both log errors and still
"pass"), inline `main()` test blocks embedded in seven library modules (which import `sys` and
carry test data into production), and no tests at all for `mora_alignment.py`, `jukujikun_processor.py`,
`furigana_normalizer.py`, or `reading_matcher.py` in isolation. Property-style tests like the
`test_reads_back` loop in `okurigana_mix_cleaning_tests.py` are the right idea and would have
caught H1 if applied to `kana_highlight` output generally (kana_only output must be a permutation-
free copy of the input reading plus okurigana).

---

## Suggested order of work

1. H3, H4, H5: small, local fixes with clear tests. One afternoon.
2. H1 and H2: alignment logic changes; add reads-back property tests first so regressions show.
3. M5 and D1: package definition, pytest conversion, CI. Everything after this is safer.
4. M8 and L3: delete the dual imports and the dead code once tests run under pytest.
5. M6, L7, L8: types, lazy singletons, `logging`.
6. M4: memoise, then DP alignment, guided by the profile in this report.
7. M1, M3, M7, L1, L5, L6, L9 as time allows.
