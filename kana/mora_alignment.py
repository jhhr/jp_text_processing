"""
Mora-to-kanji alignment: which run of a word's reading belongs to which kanji.

Given a word of kanji and its reading split into mora, the search finds the way to deal the
mora out to the kanji, in order, that has the most of the reading accounted for by the kanji's
listed readings, then the fewest kanji left without one, and among those the earliest in split
order (the first kanji given the shortest chunk, then the second, and so on). A complete
alignment is one where every kanji is read by one of its own readings; a kanji that none of
its readings account for is jukujikun.

The search is a dynamic program over (next kanji, next mora) states; each state's step is
matched once and remembered. A caller that already has one or two candidate splits (the
whole-word case) hands them in as ``possible_splits`` and they are scored in the order given.
"""

from collections.abc import Sequence
from typing import NamedTuple

from ..all_types.main_types import MoraAlignment, ReadingMatchInfo
from ..regex.rendaku import RENDAKU_CONVERSION_DICT_HIRAGANA
from ..utils.logger import package_logger as logger
from .reading_matcher import cached_reading_match


def contains_repeated_kanji(word: str) -> bool:
    """
    Check if the word contains a repeater (々).
    """
    return "々" in word[1:]


def is_valid_split_for_repeaters(word: str, split: Sequence[Sequence[str]]) -> bool:
    """
    Filter splits to only those valid for repeater kanji (々)
    For each 々 at position i, the mora split at position i must have the same
    length as the mora split at position i-1 (the kanji being repeated)
    """
    for i, kanji in enumerate(word):
        # A repeater's mora count has to match the kanji being repeated
        if kanji == "々" and i > 0 and len(split[i]) != len(split[i - 1]):
            return False
    return True


class AlignContext(NamedTuple):
    """The word-level constants every step of one alignment shares."""

    word: str
    furigana: str
    maybe_okuri: str
    kanji_count: int


class StepResult(NamedTuple):
    """
    What one step of an alignment made of one kanji, or of a kanji and the repeater after it.

    :param matches: One entry per kanji the step consumed, None where the kanji is jukujikun
    :param consumed_kanji: 1, or 2 for a repeater pair
    :param finals: The (okurigana, rest_kana) the step settles for the whole word, or None when
        it leaves the word's okurigana as it was. A matched last kanji and a matched repeater pair
        both set it, so the last step to set it wins.
    """

    matches: tuple[ReadingMatchInfo | None, ...]
    consumed_kanji: int
    finals: tuple[str, str] | None


def repeater_follows(word: str, i: int) -> bool:
    """Whether the kanji at ``i`` is followed by 々 or by itself, so the two are read as a pair."""
    next_kanji = word[i + 1] if i < len(word) - 1 else ""
    return next_kanji == "々" or next_kanji == word[i]


def select_match(
    kunyomi_match: ReadingMatchInfo | None,
    onyomi_match: ReadingMatchInfo | None,
    okurigana_to_check: str,
) -> ReadingMatchInfo | None:
    """
    Pick between a kanji's kunyomi and onyomi match.

    With no okurigana to check the onyomi wins when there is one. With okurigana, the match that
    extracted the longer okurigana wins, the kunyomi on a tie, then the onyomi if neither
    extracted any, then whichever exists.
    """
    if not okurigana_to_check:
        return onyomi_match if onyomi_match else kunyomi_match

    kunyomi_okuri = kunyomi_match["okurigana"] if kunyomi_match else ""
    onyomi_okuri = onyomi_match["okurigana"] if onyomi_match else ""

    if kunyomi_okuri and onyomi_okuri:
        # Both extracted okurigana - use longer one, or kunyomi if same length
        if len(kunyomi_okuri) >= len(onyomi_okuri):
            return kunyomi_match
        return onyomi_match
    if kunyomi_okuri:
        return kunyomi_match
    if onyomi_okuri:
        return onyomi_match
    if onyomi_match:
        # Neither extracted okurigana - prefer onyomi
        return onyomi_match
    return kunyomi_match


def align_step(ctx: AlignContext, i: int, chunk: str, next_chunk: str | None) -> StepResult:
    """
    Match the kanji at ``i`` to ``chunk``, and the repeater after it to ``next_chunk`` when it
    has one.

    Pure in its arguments: nothing here depends on which split the chunks came from, which is
    what lets a search memoise it and revisit a chunk without re-matching it.

    :param ctx: The word being aligned
    :param i: Index of the kanji in the word
    :param chunk: The joined mora this kanji is given
    :param next_chunk: The joined mora the next kanji is given, None when the split has none
    """
    word, furigana, maybe_okuri, kanji_count = ctx
    kanji = word[i]
    is_last_kanji = i == kanji_count - 1
    next_kanji = word[i + 1] if i < kanji_count - 1 else ""
    next_kanji_is_repeater = repeater_follows(word, i)

    repeater_is_last = next_kanji_is_repeater and (i + 1) == kanji_count - 1
    check_okurigana = is_last_kanji or repeater_is_last

    logger.debug(
        "align_step - processing kanji: %s, mora_sequence: %s, is_last_kanji: %s,"
        " next_kanji_is_repeater: %s, check_okurigana: %s, okurigana: %s",
        kanji,
        chunk,
        is_last_kanji,
        next_kanji_is_repeater,
        check_okurigana,
        maybe_okuri,
    )

    # Try to match reading to either kunyomi or onyomi
    repeater_mora_sequence = None
    if next_kanji_is_repeater and next_chunk is not None:
        repeater_mora_sequence = f"{chunk}{next_chunk}"

    kunyomi_match, onyomi_match = cached_reading_match(
        kanji=kanji,
        word=word,
        furigana=furigana,
        mora_sequence=chunk,
        maybe_okuri=maybe_okuri if check_okurigana else "",
        is_last_kanji=is_last_kanji and not next_kanji_is_repeater,
        repeater_mora_sequence=repeater_mora_sequence,
    )

    match_info = select_match(kunyomi_match, onyomi_match, maybe_okuri if check_okurigana else "")

    logger.debug(
        "align_step - kanji: %s, mora_sequence: %s, kunyomi_match: %s, onyomi_match: %s,"
        " selected match_info: %s",
        kanji,
        chunk,
        kunyomi_match,
        onyomi_match,
        match_info,
    )

    if match_info is None:
        # No match - mark as jukujikun, and the repeater with it
        if next_kanji_is_repeater:
            return StepResult((None, None), 2, None)
        return StepResult((None,), 1, None)

    if not next_kanji_is_repeater:
        if is_last_kanji:
            return StepResult((match_info,), 1, (match_info["okurigana"], match_info["rest_kana"]))
        return StepResult((match_info,), 1, None)

    # For repeater, check if second occurrence has rendaku. A split can come back with fewer
    # parts than the word has kanji, so the second chunk is guarded the same way
    # repeater_mora_sequence is above
    first_mora = chunk
    second_mora = next_chunk if next_chunk is not None else ""

    # Check for rendaku in second occurrence: the same reading again, but voiced,
    # the way 国々 reads くに+ぐに. An empty chunk leaves nothing to voice.
    rendaku_matched = bool(first_mora) and any(
        second_mora.startswith(rendaku_kana + first_mora[1:])
        for rendaku_kana in RENDAKU_CONVERSION_DICT_HIRAGANA.get(first_mora[0], [])
    )

    # 々 has no readings of its own, so it can only copy the first match, but a
    # kanji written out twice is as often two words meeting - the 月月 of 毎月月末
    # reads つき+ゲツ - so the second occurrence gets matched on its own readings.
    second_match = None
    if next_kanji != "々":
        second_kunyomi_match, second_onyomi_match = cached_reading_match(
            kanji=kanji,
            word=word,
            furigana=furigana,
            mora_sequence=second_mora,
            maybe_okuri=maybe_okuri if check_okurigana else "",
            is_last_kanji=(i + 1) == kanji_count - 1,
        )
        second_match = second_onyomi_match if second_onyomi_match else second_kunyomi_match

    # Add duplicate match for 々 (copy reading but mark as second occurrence).
    # The copy is also the fallback for a doubled kanji whose second mora matches
    # nothing on its own, the way 各々 only lists the doubled reading.
    # Mark it as the repeater only when the word gives us evidence of one: either
    # it was written with 々, or the second reading is a rendaku of the first, which
    # only happens inside a single word. Two identical readings prove nothing - the
    # 物物 of 生物物理学 reads exactly like the 我我 of 我々 - so a kanji doubled
    # with a plain repeat keeps its own spelling.
    if second_match is not None:
        repeater_match = second_match
    else:
        repeater_match = match_info.copy()
        repeater_match["matched_mora"] = second_mora
    repeater_match["kanji"] = "々" if next_kanji == "々" or rendaku_matched else kanji

    # We'll remove the okurigana from the first match for now as it should only
    # apply to the last kanji in the word
    match_info["okurigana"] = ""
    match_info["rest_kana"] = ""

    return StepResult(
        (match_info, repeater_match),
        2,
        (repeater_match["okurigana"], repeater_match["rest_kana"]),
    )


def youon_small_kana_match(ctx: AlignContext, i: int, chunk: str) -> str | None:
    """
    The small kana of ``chunk`` when the chunk is exactly one yōon mora (きゃ, しゅ, ...) whose
    small kana on its own reads the kanji at ``i``, else None.

    A search uses it to try the split where the base kana belongs to the previous kanji and only
    the small kana to this one.
    """
    if len(chunk) != 2 or chunk[1] not in ["ゃ", "ゅ", "ょ"]:
        return None
    word, furigana, maybe_okuri, kanji_count = ctx
    kanji = word[i]
    small = chunk[1]
    is_last_kanji = i == kanji_count - 1 and not repeater_follows(word, i)
    youon_kunyomi_match, youon_onyomi_match = cached_reading_match(
        kanji=kanji,
        word=word,
        furigana=furigana,
        mora_sequence=small,
        maybe_okuri=maybe_okuri if is_last_kanji else "",
        is_last_kanji=is_last_kanji,
    )
    youon_match_info = youon_onyomi_match if youon_onyomi_match else youon_kunyomi_match
    if youon_match_info:
        logger.debug("youon_small_kana_match - found youon match_info: %s", youon_match_info)
        return small
    return None


def empty_alignment(ctx: AlignContext, mora_split: list[str]) -> MoraAlignment:
    """The alignment with every kanji jukujikun, for when no split of the reading exists."""
    return MoraAlignment(
        kanji_matches=[None] * ctx.kanji_count,
        mora_split=mora_split,
        jukujikun_positions=list(range(ctx.kanji_count)),
        final_okurigana="",
        final_rest_kana=ctx.maybe_okuri,
    )


def walk_split(
    ctx: AlignContext, mora_split: list[str], youon_queue: list[list[str]] | None
) -> MoraAlignment:
    """
    Align the word along one split, one joined mora string per kanji.

    :param youon_queue: Where to queue the yōon variants of this split (see
        youon_small_kana_match), or None to try none
    """
    word, _, maybe_okuri, kanji_count = ctx
    logger.debug("walk_split - trying mora_split: %s", mora_split)
    kanji_matches: list[ReadingMatchInfo | None] = []
    jukujikun_positions: list[int] = []
    final_okurigana = ""
    final_rest_kana = maybe_okuri

    i = 0
    while i < kanji_count:
        try:
            mora_sequence = mora_split[i]
        except IndexError:
            mora_sequence = ""
            logger.error(
                "walk_split - mora_split contains fewer parts than kanji_count for word '%s': %s"
                " vs %s",
                word,
                mora_split,
                kanji_count,
            )
        next_mora_sequence = mora_split[i + 1] if (i + 1) < len(mora_split) else None

        step = align_step(ctx, i, mora_sequence, next_mora_sequence)

        # Test for possible youon match
        prev_mora_sequence = mora_split[i - 1] if i > 0 else None
        if (
            youon_queue is not None
            and step.consumed_kanji == 1
            # yōon only possible if previous mora exists
            and prev_mora_sequence is not None
        ):
            small = youon_small_kana_match(ctx, i, mora_sequence)
            # If the current kanji matches the small kana as yōon, we'll make a new youon
            # mora split to be tested fully after this loop
            if small:
                youon_mora_split = mora_split.copy()
                # Adjust previous mora to include base kana
                youon_mora_split[i - 1] = prev_mora_sequence + mora_sequence[0]
                # Adjust current mora to just small kana
                youon_mora_split[i] = small
                youon_queue.append(youon_mora_split)
                logger.debug("walk_split - queued youon_mora_split: %s", youon_mora_split)

        for offset, match_info in enumerate(step.matches):
            kanji_matches.append(match_info)
            if match_info is None:
                jukujikun_positions.append(i + offset)
        if step.finals is not None:
            final_okurigana, final_rest_kana = step.finals
        i += step.consumed_kanji

    alignment = MoraAlignment(
        kanji_matches=kanji_matches,
        mora_split=mora_split,
        jukujikun_positions=jukujikun_positions,
        final_okurigana=final_okurigana,
        final_rest_kana=final_rest_kana,
    )
    logger.debug("walk_split - alignment result: %s", alignment)
    return alignment


def chars_matched(alignment: MoraAlignment) -> int:
    return sum(
        len(match["matched_mora"]) for match in alignment["kanji_matches"] if match is not None
    )


def align_given_splits(
    ctx: AlignContext, possible_splits: Sequence[Sequence[Sequence[str]]]
) -> MoraAlignment:
    """
    Score ready-made splits in the order given: the first complete one wins, then the yōon
    variants they queued, else the best partial.

    The best partial is chosen while iterating: a split replaces the best so far when it has
    fewer jukujikun positions and at least as many matched characters, or at most as many
    jukujikun positions and strictly more matched characters.
    """
    word, _, _, kanji_count = ctx

    if contains_repeated_kanji(word):
        filtered_splits = [s for s in possible_splits if is_valid_split_for_repeaters(word, s)]
        logger.debug(
            "align_given_splits - filtered splits for repeaters, remaining count: %s",
            len(filtered_splits),
        )
        if filtered_splits:
            possible_splits = filtered_splits
        else:
            logger.debug(
                "align_given_splits - no valid splits remain after filtering for repeaters, using"
                " original splits"
            )

    # From here on a split is one joined mora string per kanji, which is what MoraAlignment
    # carries and what every reader of mora_split expects
    joined_splits: list[list[str]] = [
        ["".join(mora) for mora in split] for split in possible_splits
    ]

    best_alignment: MoraAlignment | None = None
    best_jukujikun_count = kanji_count + 1  # Start with worst possible
    best_chars_matched_count = 0
    youon_mora_splits: list[list[str]] = []

    def consider(alignment: MoraAlignment) -> None:
        nonlocal best_alignment, best_jukujikun_count, best_chars_matched_count
        jukujikun_count = len(alignment["jukujikun_positions"])
        chars_matched_count = chars_matched(alignment)
        if (
            jukujikun_count < best_jukujikun_count
            and chars_matched_count >= best_chars_matched_count
        ) or (
            jukujikun_count <= best_jukujikun_count
            and chars_matched_count > best_chars_matched_count
        ):
            logger.debug(
                "align_given_splits - new best partial alignment found with %s jukujikun"
                " positions and %s chars matched: %s",
                jukujikun_count,
                chars_matched_count,
                alignment,
            )
            best_chars_matched_count = chars_matched_count
            best_jukujikun_count = jukujikun_count
            best_alignment = alignment

    for mora_split in joined_splits:
        alignment = walk_split(ctx, mora_split, youon_mora_splits)
        if not alignment["jukujikun_positions"]:
            return alignment
        consider(alignment)
    for youon_mora_split in youon_mora_splits:
        alignment = walk_split(ctx, youon_mora_split, None)
        if not alignment["jukujikun_positions"]:
            return alignment
        consider(alignment)

    if best_alignment:
        logger.debug("align_given_splits - returning best partial alignment")
        return best_alignment

    logger.error("align_given_splits - no splits given for word '%s'", word)
    return empty_alignment(ctx, [])


class Cut(NamedTuple):
    """
    A place in the joined reading where one kanji's chunk may end and the next one's begin.

    :param offset: Character offset into the joined reading
    :param mora_index: How many whole mora lie before it; a cut inside a yōon mora counts the
        mora it sits in as not yet passed
    :param inside: Whether the cut sits inside a yōon mora, between the base kana and the small
        kana. A chunk ending there gives the small kana alone to the next kanji.
    """

    offset: int
    mora_index: int
    inside: bool


def path_cost(jukujikun: int, chars: int) -> tuple[int, int]:
    """
    What a path through the search costs; lower is better.

    The most chars of the reading accounted for by listed readings win, then the fewest
    jukujikun. Chars come first because a short reading is easy to match by accident - a
    one-mora stem, a rendaku of it - and counting jukujikun first would let a kanji swallow the
    unreadable part of the reading in one long chunk so that the kanji after it can each pick
    up a mora that happens to fit: 趙清々しい came out as 趙[ちょうすが]清[す]々[が] that way,
    against the 趙[ちょう]清々[すがすが] that explains more of the reading. Ranked on chars first,
    the search agreed with the split enumeration it replaced on every input it was compared on.
    """
    return (-chars, jukujikun)


class Choice(NamedTuple):
    """
    The best way on from one state of the search.

    :param cost: path_cost of the best path to the goal from here; lower is better
    :param jukujikun: How many kanji on that path are jukujikun
    :param chars: How many chars of the reading that path matches to a listed reading
    :param chunks: The chunk of the kanji at this state, and of the repeater after it if it
        has one
    :param next_state: The state the chunks lead to, None at the goal
    """

    cost: tuple[int, int]
    jukujikun: int
    chars: int
    chunks: tuple[str, ...]
    next_state: tuple[int, int, int] | None


def pair_starts(word: str) -> set[int]:
    """The kanji indexes the search steps from, skipping the second of each repeater pair."""
    starts = set()
    i = 0
    while i < len(word):
        starts.add(i)
        i += 2 if repeater_follows(word, i) else 1
    return starts


class AlignmentSearch:
    """
    The dynamic program over (next kanji, next cut) states.

    From a state the kanji takes a chunk ending at any later cut, or the kanji and the repeater
    after it take two, and the best way on from where that leaves the search is looked up or
    computed once. Chunks are tried shortest first and a later chunk only replaces the best so
    far when it is strictly better, so among equally good alignments the earliest in split order
    wins: for complete alignments that is the same one an enumeration of every split, first kanji
    shortest first, would have reached first.

    :param constrained: Whether a 々 has to take as many mora as the kanji before it
    """

    def __init__(self, ctx: AlignContext, reading: str, cuts: list[Cut], constrained: bool):
        self.ctx = ctx
        self.reading = reading
        self.cuts = cuts
        self.mora_count = cuts[-1].mora_index
        self.last = len(cuts) - 1
        # A 々 that steps on its own (人々々) is held to the chunk before it, which the state has
        # to carry; for every other kanji the previous chunk's length is dropped from the key.
        self.single_constrained = (
            {i for i in pair_starts(ctx.word) if i > 0 and ctx.word[i] == "々"}
            if constrained
            else set()
        )
        self.constrained = constrained
        self.memo: dict[tuple[int, int, int], Choice | None] = {}

    def key(self, i: int, cut: int, prev_len: int) -> tuple[int, int, int]:
        return (i, cut, prev_len if i in self.single_constrained else 0)

    def chunk(self, start: int, end: int) -> str:
        return self.reading[self.cuts[start].offset : self.cuts[end].offset]

    def best(self, i: int, cut: int, prev_len: int) -> Choice | None:
        """The best way to the goal from the state, None when the goal cannot be reached."""
        key = self.key(i, cut, prev_len)
        if key in self.memo:
            return self.memo[key]
        word, _, _, kanji_count = self.ctx
        choice: Choice | None = None
        if i == kanji_count:
            choice = Choice(path_cost(0, 0), 0, 0, (), None) if cut == self.last else None
        elif cut < self.last:
            choice = self.best_from(i, cut, prev_len)
        self.memo[key] = choice
        logger.debug(
            "AlignmentSearch - kanji %s at offset %s: %s",
            i,
            self.cuts[cut].offset,
            choice if choice is not None else "no way to the end",
        )
        return choice

    def best_from(self, i: int, cut: int, prev_len: int) -> Choice | None:
        word, _, _, kanji_count = self.ctx
        start = self.cuts[cut]
        best_choice: Choice | None = None

        def consider(chunks: tuple[str, ...], end: int, chunk_len: int) -> None:
            nonlocal best_choice
            rest = self.best(i + len(chunks), end, chunk_len)
            if rest is None:
                return
            step = align_step(self.ctx, i, chunks[0], chunks[1] if len(chunks) > 1 else None)
            jukujikun = sum(1 for match in step.matches if match is None)
            chars = sum(len(match["matched_mora"]) for match in step.matches if match is not None)
            jukujikun += rest.jukujikun
            chars += rest.chars
            cost = path_cost(jukujikun, chars)
            if best_choice is None or cost < best_choice.cost:
                best_choice = Choice(
                    cost, jukujikun, chars, chunks, self.key(i + len(chunks), end, chunk_len)
                )

        if start.inside:
            # The chunk before this one ended inside a yōon mora, so this kanji gets the small
            # kana on its own, and only if that reads it: the split is the variant an
            # enumeration would have queued on finding the small kana matches.
            if repeater_follows(word, i):
                return None
            end = cut + 1
            if self.mora_count - self.cuts[end].mora_index < kanji_count - i - 1:
                return None
            small = self.chunk(cut, end)
            if align_step(self.ctx, i, small, None).matches[0] is None:
                return None
            consider((small,), end, 1)
            return best_choice

        if not repeater_follows(word, i):
            remaining = kanji_count - i - 1
            for end in range(cut + 1, self.last + 1):
                chunk_len = self.cuts[end].mora_index - start.mora_index
                if chunk_len < 1:
                    continue
                if self.mora_count - self.cuts[end].mora_index < remaining:
                    break
                if i in self.single_constrained and chunk_len != prev_len:
                    continue
                consider((self.chunk(cut, end),), end, chunk_len)
            return best_choice

        # A repeater pair: two chunks, the second held to the first's length for a 々
        held = self.constrained and word[i + 1] == "々"
        remaining = kanji_count - i - 2
        for middle in range(cut + 1, self.last):
            first_len = self.cuts[middle].mora_index - start.mora_index
            if first_len < 1 or self.cuts[middle].inside:
                continue
            if self.mora_count - self.cuts[middle].mora_index - 1 < remaining:
                break
            first = self.chunk(cut, middle)
            for end in range(middle + 1, self.last + 1):
                second_len = self.cuts[end].mora_index - self.cuts[middle].mora_index
                if second_len < 1:
                    continue
                if self.mora_count - self.cuts[end].mora_index < remaining:
                    break
                if held and second_len != first_len:
                    continue
                consider((first, self.chunk(middle, end)), end, second_len)
        return best_choice

    def run(self) -> tuple[Choice, list[str]] | None:
        """The root choice and the split it leads to, or None when no split reaches the goal."""
        choice = self.best(0, 0, 0)
        if choice is None:
            return None
        root = choice
        mora_split: list[str] = []
        while choice is not None and choice.next_state is not None:
            mora_split.extend(choice.chunks)
            choice = self.memo[choice.next_state]
        return root, mora_split


def align_by_search(ctx: AlignContext, mora_list: list[str]) -> MoraAlignment:
    """
    Find the alignment with the most matched chars, then the fewest jukujikun, then the earliest
    in split order, by dynamic programming over the mora boundaries.

    A 々 is first held to as many mora as the kanji before it; when that leaves no split at all
    the constraint is dropped. When no alignment at mora boundaries is complete, a second pass
    also lets a chunk end inside a yōon mora (きゃ → き | ゃ), giving the small kana alone to the
    next kanji when it reads it that way, and its result stands when it is strictly better.
    """
    word, _, _, kanji_count = ctx
    mora_count = len(mora_list)
    if mora_count < kanji_count:
        logger.debug(
            "align_by_search - fewer mora than kanji for word '%s', all jukujikun: %s",
            word,
            mora_list,
        )
        # It doesn't matter that the mora_list is not split per kanji here: split_mora_for_jukujikun
        # redistributes the mora among the jukujikun kanji later
        return empty_alignment(ctx, mora_list)

    reading = "".join(mora_list)
    boundaries: list[Cut] = [Cut(0, 0, False)]
    for mora in mora_list:
        boundaries.append(Cut(boundaries[-1].offset + len(mora), len(boundaries), False))

    constrained = contains_repeated_kanji(word)
    found = None
    if constrained:
        found = AlignmentSearch(ctx, reading, boundaries, constrained=True).run()
        if found is None:
            logger.debug(
                "align_by_search - no split gives each 々 the mora count of the kanji before it,"
                " dropping the constraint"
            )
            constrained = False
    if found is None:
        found = AlignmentSearch(ctx, reading, boundaries, constrained=False).run()
    if found is None:
        # Cannot happen with at least one mora per kanji, but the search must return something
        logger.error("align_by_search - no split found for word '%s': %s", word, mora_list)
        return empty_alignment(ctx, mora_list)
    choice, mora_split = found
    logger.debug(
        "align_by_search - best split at mora boundaries: %s, cost: %s", mora_split, choice.cost
    )
    if choice.jukujikun == 0:
        return walk_split(ctx, mora_split, None)

    # Yōon pass: every boundary, plus a cut inside each yōon mora that has a kanji before it
    cuts: list[Cut] = []
    for index, boundary in enumerate(boundaries):
        cuts.append(boundary)
        if 0 < index < mora_count:
            mora = mora_list[index]
            if len(mora) == 2 and mora[1] in ["ゃ", "ゅ", "ょ"]:
                cuts.append(Cut(boundary.offset + 1, index, True))
    if len(cuts) > len(boundaries):
        youon_found = AlignmentSearch(ctx, reading, cuts, constrained).run()
        if youon_found is not None and youon_found[0].cost < choice.cost:
            choice, mora_split = youon_found
            logger.debug(
                "align_by_search - better split with a yōon cut: %s, cost: %s",
                mora_split,
                choice.cost,
            )
    logger.debug("align_by_search - returning best partial alignment")
    return walk_split(ctx, mora_split, None)


def find_first_complete_alignment(
    word: str,
    furigana: str,
    maybe_okuri: str,
    mora_list: list[str] | None = None,
    possible_splits: Sequence[Sequence[Sequence[str]]] | None = None,
) -> MoraAlignment:
    """
    Find the complete alignment of mora to kanji that is earliest in split order, or failing
    that the best partial alignment (most matched chars, then fewest jukujikun positions).

    :param word: The word to align (string of kanji, may include 々)
    :param furigana: The full reading of the word in kana
    :param maybe_okuri: The kana following the word (for last kanji extraction)
    :param mora_list: List of mora units to distribute across kanji, searched over; optional if
       possible_splits is provided
    :param possible_splits: Precomputed list of possible mora splits, each split a list of
       mora lists, one per kanji, scored in the order given; optional, replaces mora_list
    :return: MoraAlignment with the first complete match or best partial match
    """
    kanji_count = len(word)
    ctx = AlignContext(word, furigana, maybe_okuri, kanji_count)

    # Handle edge case: empty word
    if kanji_count == 0:
        return MoraAlignment(
            kanji_matches=[],
            mora_split=[],
            jukujikun_positions=[],
            final_okurigana="",
            final_rest_kana=maybe_okuri,
        )

    if possible_splits is not None:
        return align_given_splits(ctx, possible_splits)
    if mora_list is None:
        raise ValueError("Either mora_list or possible_splits must be provided")
    logger.debug(
        "find_first_complete_alignment - searching splits for word '%s' with mora_list: %s",
        word,
        mora_list,
    )
    return align_by_search(ctx, mora_list)
