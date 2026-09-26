# Working on jp_text_processing

Guidance for coding agents (and anyone new to the repo). It describes what the repository is, how
to run its checks, and the conventions a change is expected to follow. The code's own docstrings
and comments are the reference for how each piece works; this file is about how to work on it.

## What this repository is

This directory *is* the Python package `jp_text_processing`: furigana, reading and word-highlighting
processing shared by the author's Anki add-ons. It is not a distribution root. The add-ons vendor
it with their own `build.py` and import it as `<addon>.shared.jp_text_processing`; nothing here is
ever pip-installed, and `pyproject.toml` exists only to declare the package and to hold the tool
configuration.

Two functions are the public surface, re-exported lazily from `__init__.py`:

- `kana_highlight(kanji_to_highlight, text, return_type, with_tags_def)` splits the reading in
  each `漢字[かんじ]` group between the individual kanji, decides for every kanji whether its
  reading is onyomi, kunyomi or jukujikun, and renders the text again in one of three modes
  (`furigana`, `furikanji`, `kana_only`), optionally wrapping each reading in `<on>`, `<kun>`,
  `<juk>` tags with `<oku>` around okurigana, and bolding the kanji asked for.
- `word_highlight(text, word)` finds a dictionary-form word or phrase in furigana text, inflected
  forms included, and wraps each occurrence in `<b>`. MeCab does the inflection checking.

Everything else is machinery for those two.

### Furigana syntax

Text is in Anki's furigana syntax: the reading follows its kanji in square brackets and a word
is preceded by a space that marks where its kanji start, except at the start of the string:
`この 家[いえ]は`, `家[いえ]で 居[い]る`. Digits, `々`, `ヶ` and `ヵ` count as kanji
(`regex/kanji_furi.py`). `[sound:...]` tags are left untouched. HTML in the text is preserved and
the highlight is placed around it rather than through it.

## Layout

| Path | What it holds |
| --- | --- |
| `__init__.py` | The two lazy re-exports. Do not import the submodules eagerly here (see its docstring). |
| `all_types/main_types.py` | The shared `TypedDict`s and `Literal`s: `MoraAlignment`, `ReadingMatchInfo`, `WrapMatchEntry`, `FinalResult`, `WithTagsDef`, parts of speech. |
| `kana/` | The `kana_highlight` pipeline: cleaning replacers, the exception table, furigana normalisation, mora splitting, the reading matcher, the mora-to-kanji alignment search, jukujikun handling, reconstruction. |
| `okuri/` | Okurigana: the conjugation dictionary, inflection checks, and the MeCab-backed okurigana detection. `mecab_common.py` holds the one `MecabController` instance. |
| `word/` | The `word_highlight` pipeline: patterns, tag storage and restoration, `<b>` balancing, MeCab-backed inflected matching. |
| `kanji/` | `all_kanji_data.json` (about 11 000 kanji, each with its onyomi and kunyomi as strings) and the digit-to-kanji converter. |
| `regex/` | Character classes and tables: kanji ranges, mora lists, rendaku conversions. |
| `utils/logger.py` | The package logger. |
| `mecab_controller/` | A git submodule, vendored from an upstream fork. **Never edit it.** mypy ignores errors inside it and ruff excludes it, on purpose. It bundles a MeCab binary per platform under `support/`, so nothing has to be installed for the tests. |
| `conftest.py` | pytest configuration shared by the suites, including the `timed` marker. |

The `kana_highlight` pipeline, in the order `furigana_replacer` in `kana/kana_highlight.py` runs
it: three regex cleaning passes over the whole text (orphaned `々`, leading kana, mixed
okurigana), then per word the exception table (`kana/furigana_exceptions.py`), furigana
normalisation, mora splitting, the alignment search (`kana/mora_alignment.py`), jukujikun
processing, and reconstruction (`kana/construct_wrapped_furi_word.py`).

## Running the checks

The working directory has to be the *parent* of this directory, so that `jp_text_processing` is
importable as a package (in the add-on repositories that parent is `anki_shared/`). Anything that
prints Japanese needs `PYTHONIOENCODING=utf-8`; in PowerShell that is
`$env:PYTHONIOENCODING = "utf-8"`.

```
cd <parent of jp_text_processing>
PYTHONIOENCODING=utf-8 python -m pytest jp_text_processing -q
python -m mypy --config-file jp_text_processing/pyproject.toml -p jp_text_processing
ruff check jp_text_processing
ruff format --check jp_text_processing
```

All four have to come back clean before a change is committed: every test passing (the one
`xfail` is a known colloquial case in `word_highlight_tests.py`), mypy with no issues, ruff with no
findings, and the formatter with nothing to change. There is no CI; the checks are run locally.
The whole test run takes a few seconds; pytest needs to be version 8.4 or newer (`minversion` in
`pyproject.toml`). Nothing needs Anki, and `addopts = "-p no:anki"` keeps the pytest-anki plugin
out of the way where it is installed.

Useful variations:

- One suite: `python -m pytest jp_text_processing/kana/kana_highlight_tests.py`.
- One case, by its id: `-k "no kanji_to_highlight"`. Ids are not escaped, so Japanese works in
  `-k`, but `-k` cannot take a space inside one term; join the words with `and` instead
  (`-k "search and cost"`).
- Everything a case logged: add `--log-cli-level=debug`. pytest captures the package logger by
  itself; nothing in the suites turns logging on.
- A suite also runs as a script: `python -m jp_text_processing.kana.kana_highlight_tests`.

## Test conventions

Suites live next to the code they test and are named `<module>_tests.py` (`python_files` in
`pyproject.toml`); pytest's default `test_*.py` is not collected. A suite is a `CASES` list of
`pytest.param(...)` entries, each with an `id` that says what the case is about (a sentence in
English, or the input itself when that names it best), fed to one parametrised test function.

`kana/kana_highlight_tests.py` is the main suite. Every case there is one sentence run through
each of the nine modes (three return types, each without tags, with tags split, with tags merged),
and its expectations are a dict keyed by the mode id. A mode the case gives no expectation for is
skipped, and a key that is not a mode id fails at collection. When adding a case, give it all
nine modes unless there is a reason not to; the outputs are recorded from the code and then read
by a human for correctness, so read them, do not just paste them.

- A case known to fail is `pytest.param(..., marks=pytest.mark.xfail(reason="why", strict=True))`.
  Never delete or loosen a case to get a run green.
- A case that pins a performance fix carries `pytest.mark.timed(max_ms=...)`; `conftest.py`
  measures the test function's own call, not its fixtures, and fails the case when it runs over.
  The run lists the timed cases at the end. The five `search cost:` cases in the main suite hold
  the alignment search to 200 ms per mode; a change to `kana/mora_alignment.py` or
  `kana/reading_matcher.py` should keep them well under that. MeCab is brought up once by an
  autouse session fixture so its start-up is not charged to a case.
- Behaviour the package does not promise but should survive is pinned too: a degenerate input
  gets a case that records what comes out, with a comment saying it is degenerate and that the
  point is not crashing.

When a change alters the output of existing cases, the new outputs have to be intentional and
explained in the commit message. A refactor that is meant to change nothing is best verified
differentially: keep the old implementation in a scratch copy and compare the two over every
input the test files contain (and over generated inputs when the change is to the search).

## Behaviour policy

`kana_highlight` handles sensible input correctly, handles some degenerate input in some sensible
way, and never crashes on any input. `word_highlight` follows the same rule: empty or `None`
text and word are returned as they came. A crash on any input is a bug to fix; the output for
invalid Japanese (`々々々`, an empty furigana bracket, readings that fit no kanji) only has to be
sensible, and what "sensible" is gets recorded in a test once decided.

Words the reading matcher cannot get right on its own (jukujikun with a partial listed reading,
mixed on/kun words) go into `FURIGANA_EXCEPTION_ALIGNMENTS` in `kana/furigana_exceptions.py`,
keyed `word_reading` with the word in its `々` spelling; the entry lists, per kanji, the reading
type and the mora it takes. Prefer fixing the matcher when the case is a class of words, and the
table when it is one word.

## Code conventions

- Python 3.10 is the floor (`requires-python` and ruff's `target-version`): no `NotRequired`,
  `Self` or `ExceptionGroup`; the optional keys of a `TypedDict` are done with a `total=False`
  base class, as `all_types/main_types.py` does.
- Everything is type-annotated and mypy has to stay clean. Data that crosses module boundaries
  is a `TypedDict` or `NamedTuple` from `all_types/main_types.py`; add fields there, with the
  docstring's `:param` list kept current.
- Logging goes through `from ..utils.logger import package_logger as logger`; library code never
  prints, and no logger is threaded through call signatures. `silenced()` wraps a probe whose
  failures are expected. Scripts turn output on with `console_logging(level)`.
- ruff, with the rule set in `pyproject.toml`, and `ruff format` at a 100-column line length.
  E501 is ignored because a Japanese character counts as two columns; the formatter still wraps
  the code.
- Comments say *why*, in prose, and stay accurate: a comment or docstring that no longer
  describes the code is a defect. Regexes carry a comment saying what each group is. Module
  docstrings describe what the module is for and the rules it implements.
- Imports are relative within the package (`from ..regex.kanji_furi import ...`), which is what
  lets the add-ons vendor it under another name.
- Keep the alignment search's contract as its module docstring states it (most of the reading
  accounted for by listed readings, then fewest jukujikun, then earliest split). If the ranking
  has to change, change the docstring and `path_cost` together and say so in the commit.

## Commits and branches

- One topic per commit. Fixes for different things go in different commits, even when they come
  out of the same review.
- The subject line is `<area>: <what changed>` in lower case, written as a sentence about the
  behaviour: `kana_filter: an empty furigana bracket no longer swallows the next word`,
  `tests: time a case on request, and pin the alignment search's cost`. Areas in use: `kana`,
  `kana_highlight`, `word`, `okuri`, `regex`, `number`, `alignment`/`mora_alignment`, `tests`,
  `tooling`, `style`.
- The body says why, what was verified and how (test counts, differential comparisons, timings
  before and after), and what deliberately did not change.
- Work on a branch (`fix/...`, `feat/...`) and merge to `main` through a pull request. Never
  rewrite history on a branch someone else works on. Do not touch the submodule pointer unless
  updating the submodule is the point of the change.
- Do not put model or tool identifiers in code, comments, tests or docs.
