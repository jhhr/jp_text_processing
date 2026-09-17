# M2 plan: replacing the exhaustive mora alignment search

Spec for finding M2 of `CODE_REVIEW.md` (main at `1536ad7`). It describes the current search, the
behaviour a replacement has to preserve exactly, the two steps to take (a cache, then a dynamic
program), and how to prove each step changes nothing it should not. Measurements in this document
were taken on the current tree with the patches described, on a scratch copy.

## 1. The problem

`find_first_complete_alignment` (`kana/mora_alignment.py`) enumerates every ordered split of the
mora list into one chunk per kanji (`get_ordered_sublists`, C(mora−1, kanji−1) splits), scores
each split kanji by kanji through `match_reading_to_mora`, and returns the first split in which
every kanji matched. Each (kanji, chunk) pair is therefore re-matched once for every split that
contains it, and the number of such splits grows combinatorially.

| Input | Splits | `match_reading_to_mora` calls | Distinct (kanji, chunk, context) | Time |
| --- | --- | --- | --- | --- |
| 東京特許許可局 (7 kanji, 12 mora) | 462 | | | 18 ms |
| ご協力者募集中 (6 kanji, prefix) | 3 × 462 | | | 133 ms |
| 国際連合安全保障理事会 (11 kanji, 16 mora) | 2 588 | 29 511 | 188 | 1 020 ms |
| same, followed by する | 2 588 | | | 1 144 ms |
| same kanji, nonsense reading | 2 588 | 33 033 | 192 | 1 259 ms |

Three things multiply it: a word that opens with kana is aligned three times
(`leading_kana_cleaning_replacer` runs two probe alignments before the real one); okurigana after
the word makes every last-kanji check test both kunyomi and onyomi; and a reading that matches
nothing never exits early, so the whole space is walked and then the yōon retries on top.

The per-chunk work is the expensive part and it is almost entirely repeated: 188 distinct chunk
matches carry the 29 511 calls. The mecab okurigana lookups inside `match_onyomi_to_mora` are
*not* a significant cost (31 ms of the 3.2 s on the する input, thanks to the submodule's LRU cache
on `translate`) and this plan does not touch them.

## 2. What must be preserved

Every rule below is something the current search does that a caller or a test depends on. The
replacement has to reproduce each one; where it cannot reproduce one exactly, that is called out
in §6.

### 2.1 The per-kanji step

For kanji `i` with chunk `c = split[i]`, the loop body of `process_mora_split` does, in order:

1. `next_kanji_is_repeater = word[i+1] == "々" or word[i+1] == word[i]`.
2. `check_okurigana = is_last_kanji or (next_kanji_is_repeater and i + 1 == kanji_count − 1)`;
   the okurigana handed to the matcher is `maybe_okuri` only when this holds, else `""`.
3. `is_last_kanji` handed to the matcher is `i == kanji_count − 1 and not next_kanji_is_repeater`
   (the first of a repeater pair is never "last", even when the pair ends the word).
4. `repeater_mora_sequence = c + split[i+1]` when the next kanji is a repeater, else `None`.
5. `match_reading_to_mora(kanji, word, furigana, c, kanji_data, okuri, is_last, repeater_seq)`
   returns `(kunyomi_match, onyomi_match)`.
6. Selection between the two: with no okurigana to check, onyomi wins if present; with okurigana,
   the one that extracted the longer okurigana wins, kunyomi on a tie, then onyomi if neither
   extracted any, then whichever exists.
7. Repeater pair: on a match, the second kanji gets a copy of the match with `matched_mora =
   split[i+1]`, `kanji = "々"` if written 々 or if the second chunk is a rendaku of the first, else
   the kanji itself; the first kanji's `okurigana`/`rest_kana` are blanked and the pair's
   okurigana comes from the second. Both kanji then advance (`i += 2`). On no match both are
   jukujikun. (H3 in the review changes the copy into a verified match of the second chunk; the
   plan assumes H3 lands first, and the step function in §3 is where H3's check lives.)
8. Last kanji (not a repeater pair): `final_okurigana`/`final_rest_kana` come from its match.
9. Yōon side-effect: if `c` is exactly one yōon mora (`きゃ`, `しゅ`, …), the previous kanji
   exists, and the small kana alone matches the current kanji, a variant split is queued in which
   the base kana moves to the previous chunk and the small kana stays (`youon_mora_splits`). The
   queued splits are tried, without generating further variants, after every ordinary split has
   failed.

`match_reading_to_mora` and the two matchers under it depend on nothing but their arguments:
`kanji_data` is `all_kanji_data[kanji]` (or the empty record for an unknown kanji), and the mecab
call inside `match_onyomi_to_mora` is a function of `(word, furigana, maybe_okuri)`. The step is
pure in `(i, split[i], split[i+1])` given the word, its furigana and its okurigana.

**Callers mutate the returned dicts.** `mora_alignment.py:291-298` writes `matched_mora`, `kanji`,
`okurigana` and `rest_kana` into the match dicts, and `match_kunyomi_to_mora` writes into its own
candidates. Anything that memoises a match has to hand out a copy.

### 2.2 Which alignment wins

- The candidate splits are `get_ordered_sublists(mora_list, kanji_count)`, i.e. `combinations`
  of split positions in lexicographic order: the earliest split position varies slowest, so the
  first kanji gets the shortest chunks first, then the second, and so on.
- If the word contains 々, splits in which a 々's chunk has a different mora count from the chunk
  before it are removed first; if that removes every split, the unfiltered list is used.
- **Complete alignments:** the first split, in that order, where no kanji is jukujikun wins,
  and the search stops there. Equivalently: among complete alignments, the one whose split
  positions are lexicographically smallest.
- **Yōon retry:** only if no ordinary split is complete; the queued variants are tried in the
  order they were queued, and the first complete one wins.
- **Partial alignments:** if nothing is complete, the best partial is chosen while iterating:
  a split replaces the best so far when it has fewer jukujikun positions and at least as many
  matched characters, or at most as many jukujikun positions and strictly more matched
  characters (`mora_alignment.py:360-365`). Matched characters is the summed length of
  `matched_mora` over matched kanji.
- **No split at all** (fewer mora than kanji): every kanji is jukujikun and `mora_split` is the
  raw mora list; `process_jukujikun_positions` deals the mora out afterwards.

The partial rule is not a total order. It depends on enumeration order: with splits A (1 jukujikun,
5 chars) and B (2 jukujikun, 8 chars), A-then-B keeps A and B-then-A keeps B, because neither
replaces the other once installed. §6 addresses this.

### 2.3 The result

`MoraAlignment` with `kanji_matches` (one `ReadingMatchInfo` or `None` per kanji), `mora_split`
(one joined string per kanji, in the split that won), `jukujikun_positions`, `final_okurigana`,
`final_rest_kana`. Downstream, `process_jukujikun_positions` re-deals the mora of each contiguous
jukujikun run from `mora_split`, so within a run only the run's total mora matters, but the mora
assigned to matched kanji and the run boundaries are used as they are.

### 2.4 Entry points

- `kana_highlight.furigana_replacer` (`kana/kana_highlight.py:708,719`): the whole-word case
  passes a ready-made `possible_splits` (the entire reading as one chunk, or two character-level
  halves for kanji+々); every other word passes `mora_list`.
- `okurigana_mix_cleaning_replacer.unread_kanji_count` (`:50`): the two probe alignments, with
  `maybe_okuri=""`. Only `len(jukujikun_positions)` is read.

`get_ordered_sublists` has no other importer.

## 3. Step 0: isolate the step

Before either optimisation, pull the loop body of `process_mora_split` (§2.1 items 1-8) into a
function with no free variables beyond the word-level constants:

```python
class StepResult(NamedTuple):
    matches: tuple[Optional[ReadingMatchInfo], ...]  # 1 entry, or 2 for a repeater pair
    consumed_kanji: int                              # 1 or 2
    okurigana: str                                   # only meaningful when the step ends the word
    rest_kana: str

def align_step(ctx: AlignContext, i: int, chunk: str, next_chunk: Optional[str]) -> StepResult
```

`AlignContext` holds `word`, `furigana`, `maybe_okuri`, `kanji_count`. The yōon side-effect (item
9) stays in the caller: it needs the previous chunk and the queue, and it is a search concern.

This is a pure refactor: `process_mora_split` calls `align_step` and appends its results. Suite
must be green and the debug log identical apart from the step's own lines. It is worth doing on
its own because it is the seam every later step and every differential test hangs on.

## 4. Step 1: memoise the step

Wrap `match_reading_to_mora` (or `align_step`, once it exists) in a bounded cache keyed by
`(kanji, word, furigana, mora_sequence, maybe_okuri, is_last_kanji, repeater_mora_sequence)`.
`kanji_data` is left out of the key and re-derived from `kanji` inside the cached function.
Return a shallow copy of each dict (`dict(match)` is enough, every value is a string or bool), so
that the mutations in §2.1 never reach the cached object.

`functools.lru_cache(maxsize=4096)` on a module-level function is sufficient. The key carries
`word` and `furigana`, so entries are specific to one word and the cache is only warm across the
three alignments of a prefixed word and across a sentence that repeats a word. The point is not
cross-word reuse; it is that within one alignment the 29 511 calls collapse to 188.

Measured with exactly this patch, outputs identical on the full suite (2601 passed) and on every
input below:

| Input | Before | Cache, cold | Cache, warm |
| --- | --- | --- | --- |
| 東京特許許可局 | 18 ms | 2.7 ms | 1.2 ms |
| ご協力者募集中 | 133 ms | 10 ms | 8 ms |
| 国際連合安全保障理事会 | 1 020 ms | 62 ms | 45 ms |
| same + する | 1 144 ms | 47 ms | 46 ms |
| same, nonsense reading | 1 259 ms | 58 ms | 54 ms |

The remaining 45-60 ms is the Python loop over 2 588 splits × 11 kanji doing cache lookups, the
selection logic and the debug-logging calls. That is what step 2 removes.

Also in this step, the cheap short-circuit for the probes: in `leading_kana_cleaning_replacer`,
run the stripped probe first; if it leaves nothing unread and `SELF_READING_PREFIX_REC` matches
the prefix, the kept probe cannot change the decision (a fully readable stripped reading with a
self-reading prefix is always taken) and is skipped. Two alignments become one on the common
お-/ご- words.

## 5. Step 2: dynamic program

### 5.1 State and transitions

State `(i, s)`: the next kanji is `word[i]` and the next unassigned mora is `mora_list[s]`.
Goal: `(kanji_count, len(mora_list))`. From `(i, s)` the step consumes either

- one kanji with chunk `mora_list[s:s+L]`, going to `(i+1, s+L)`, or
- a repeater pair (`word[i+1]` is 々 or equal to `word[i]`) with chunks `mora_list[s:s+L1]` and
  `mora_list[s+L1:s+L1+L2]`, going to `(i+2, s+L1+L2)`.

Chunk lengths range over `1 ≤ L ≤ n − s − (remaining kanji after this step)`, so every later
kanji keeps at least one mora; that is the same bound the enumeration has implicitly. For a 々
pair with the repeater filter active, `L2 == L1`. Each transition calls `align_step` once (cached
from step 1, so cheap even when the DP revisits it).

At most `kanji_count × (mora + 1)` states and `mora` transitions per state: 11 × 17 × 16 ≈ 3 000
step evaluations for the 11-kanji word, against 28 000 in the enumeration, and each one a cache
hit after the first ~190.

### 5.2 Objective

Each transition contributes `(jukujikun, chars)`: the number of `None` in its matches, and the
summed `matched_mora` lengths of its non-`None` matches. Both are additive over a path, so the
best suffix from a state is well defined under the lexicographic order

```
minimise total jukujikun, then maximise total matched chars, then earliest split
```

and optimal substructure holds (adding a prefix's constant vector preserves the order between two
suffixes). `best(i, s)` returns `(jukujikun, chars, first_L, …)` for the best suffix, memoised on
`(i, s)`.

"Earliest split" is the tie-break that reproduces §2.2's enumeration order: try `L` in ascending
order and keep the first suffix that achieves the best `(jukujikun, chars)`. A complete alignment
has `jukujikun == 0` and, since every mora is assigned, the same `chars` as every other complete
alignment, so among complete alignments the DP picks the one with the shortest first chunk, then
the shortest second chunk given that, and so on: exactly the first complete split in
`get_ordered_sublists` order. **For complete alignments the DP is output-identical by
construction.**

### 5.3 Reconstruction

`best(i, s)` stores the chosen `L` (or `L1, L2`) per state; walk from `(0, 0)` to rebuild
`mora_split`, then re-run `align_step` along the chosen path to collect `kanji_matches`,
`jukujikun_positions`, and the last step's `okurigana`/`rest_kana`. Re-running is cheaper than
storing match dicts in every state and gives the same dicts the enumeration would have built.

### 5.4 Repeater filter

Run the DP with `L2 == L1` enforced for 々 pairs. If no path reaches the goal at all (not even an
all-jukujikun one: the constraint can make the mora count unreachable, e.g. an odd count for 人々
alone), run it again unconstrained. That is the same "filtered list empty → use the unfiltered
list" rule as today, decided per word rather than per split. A spelled-out double (`物物`) has
no constraint today and none in the DP.

### 5.5 Yōon retry

The enumeration only ever splits at mora boundaries; the retry adds one boundary inside a yōon
mora (`きゃ` → `き` | `ゃ`) when the small kana matches the current kanji on its own, and only
after every boundary-only split has failed. The DP does the same in two passes:

1. Pass A, boundaries only. Return its result if any complete path exists.
2. Pass B, the same DP over an extended position set: every mora boundary plus one extra
   position inside each yōon mora `XY` (X the base kana, Y ∈ ゃゅょ). A chunk may end at an extra
   position only when the *next* chunk is exactly `Y` and the current chunk then ends in `X`;
   both are what the queued variant produces today. Return pass B's best if it is complete,
   otherwise the better of the two passes' partials under §5.2's order.

Pass B is a superset of today's retry: the enumeration only queues variants derived from splits
it actually visited, one modification each, whereas the DP can combine two yōon splits in one
word. A complete alignment found by B and not by the enumeration is an improvement, not a
regression; the differential test in §7 counts these separately.

### 5.6 `possible_splits`

The whole-word path hands over one or two candidate splits already made. Keep that path as it
is: score each given split with `align_step` in order, apply the repeater filter to the list,
return the first complete one or the best partial by today's rule. It is one or two splits, so
there is nothing to optimise, and it keeps the character-level halves behaviour untouched.

Signature stays `find_first_complete_alignment(word, furigana, maybe_okuri, mora_list=None,
possible_splits=None)`. With `mora_list`, the DP; with `possible_splits`, the scorer.
`get_ordered_sublists.py` is deleted once nothing imports it.

## 6. Where behaviour may differ, and what to do about each

| Case | Enumeration | DP | Decision |
| --- | --- | --- | --- |
| Complete alignment exists at mora boundaries | first in lexicographic split order | same, by construction | identical |
| Complete only via yōon retry | first queued variant that completes | best under §5.2 over all yōon-extended splits | superset; accept, record in the test log |
| No complete alignment | order-dependent best partial (§2.2) | fewest jukujikun, then most chars, then earliest split | **semantic change**; see below |
| No split at all | all jukujikun, raw mora list | same | identical |

The partial case is the one to think about. The DP's rule is what the current code's comment
says it intends ("fewest jukujikun positions and most total kana chars matched"); the current
implementation is that rule applied greedily in enumeration order, and the two agree whenever the
best split under the DP's order is also the first one the enumeration would have installed and
never displaced. They can disagree when an early split with few jukujikun but few matched chars
blocks a later split with the same jukujikun count and more chars. The DP then returns the later
one, which is the better alignment by the stated rule. The differential test decides whether any
existing case depends on the old greedy result; if one does, the case's expectation is examined by
hand, and the plan is to update the expectation rather than to replicate order dependence in the
DP.

Logging changes too: the enumeration logs every split it tries at DEBUG. The DP should log each
state the first time it is evaluated and the chosen path at the end. `okurigana_mix_cleaning_tests`
asserts the probes log *nothing* (they run under `silenced()`), which still holds.

## 7. Verification

Each step lands on its own commit with the suite green. In addition:

1. **Differential harness** (a script under `kana/`, not shipped in the package, or a test marked
   slow): run the old `find_first_complete_alignment` and the new one on the same inputs and
   compare every field of `MoraAlignment`. Keep the old implementation importable (e.g. renamed
   `_enumerate_alignments`) until the harness has run once on:
   - every `text` in `kana_highlight_tests.CASES`, `kana_filter_tests`,
     `okurigana_mix_cleaning_tests` and `word_highlight_tests`, each bracket group extracted and
     fed with its following kana as `maybe_okuri`;
   - a generated corpus: for 2 000 random words of 1-8 kanji drawn from `all_kanji_data`, a
     reading built by concatenating one listed reading per kanji (so a complete alignment
     exists), the same reading with one kanji's part replaced by nonsense (partial), and a
     nonsense reading of the same mora count (all jukujikun); with and without a random
     okurigana tail; with 々 inserted after a random kanji in a tenth of them.
   Report divergences in the three classes of §6. Class 1 must be empty; classes 2 and 3 are
   listed with the inputs so they can be looked at.
2. **Timing**: the five inputs of §4, plus the full suite wall time, before and after each step.
   Targets after step 2: every input under 10 ms cold, and the suite no slower than today.
3. **Cache correctness**: a unit test that calls `match_reading_to_mora` twice with the same
   arguments, mutates the first result, and asserts the second is unchanged.
4. **Repeater filter fallback**: a unit test with an unreachable 々 constraint (人々 with three
   mora) asserting the unconstrained result matches today's.

## 8. Order of work and sizing

| Step | Change | Risk | Size |
| --- | --- | --- | --- |
| 0 | Extract `align_step`; no behaviour change | none | half a day |
| 1 | `lru_cache` on the matcher, copy on return; probe short-circuit | low; verified here | half a day, most of it the copy discipline |
| 2a | DP pass A + repeater fallback + reconstruction, behind `mora_list`; harness | medium; the partial rule | 1-2 days |
| 2b | Yōon pass B; harness rerun | low | half a day |
| 2c | Delete the enumeration and `get_ordered_sublists.py` | none | an hour |

Step 1 alone takes the worst measured input from 1.0 s to 50 ms and is safe to ship on its own.
Step 2 is worth doing for the remaining 20×, for the okurigana-tail inputs that step 1 leaves at
~50 ms, and because it makes the search's selection rule explicit instead of a side effect of
enumeration order.
