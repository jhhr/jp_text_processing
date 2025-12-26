import json
import os

try:
    from reading_matcher import (
        get_onyomi_reading_hiragana,
        get_kunyomi_reading_variants,
        check_reading_match,
    )
except ImportError:
    from .reading_matcher import (
        get_onyomi_reading_hiragana,
        get_kunyomi_reading_variants,
        check_reading_match,
    )
try:
    from utils.logger import Logger
except ImportError:
    from ..utils.logger import Logger
try:
    from kanji.all_kanji_data import all_kanji_data, KANJI_DIR
except ImportError:
    from ..kanji.all_kanji_data import all_kanji_data, KANJI_DIR
try:
    from all_types.main_types import KanjiReadingData, KunyomiReadingToTry
except ImportError:
    from ..all_types.main_types import KanjiReadingData, KunyomiReadingToTry


def generate_cached_reading_data(logger: Logger = Logger("info")) -> None:
    """
    Generate cached reading data for all kanji characters into all_kanji_reading_data.json using
    all_kanji_data.json as source. This script should be run whenever the reading matching logic
    or data is updated.

    The output file directory will be the same as the input file directory.
    """
    logger.info("Generating cached kanji reading data...")
    all_kanji_reading_data: dict[str, KanjiReadingData] = {}
    all_kanji_data_items = list(all_kanji_data.items())
    logger.info(f"Processing {len(all_kanji_data_items)} kanji characters...")
    for kanji, kanji_data in all_kanji_data_items:
        onyomi = kanji_data.get("onyomi", "")
        kunyomi = kanji_data.get("kunyomi", "")
        kanji_reading_data: KanjiReadingData = {
            "onyomi": {},
            "kunyomi": {},
            "lengths": {},
        }

        # Match onyomi readings
        onyomi_readings = [r.strip() for r in onyomi.split("、")]
        for onyomi_reading in onyomi_readings:
            reading_hiragana = get_onyomi_reading_hiragana(onyomi_reading, logger=logger)
            if not reading_hiragana:
                continue

            def cache_reading(matched_reading: str, reading_variant: str) -> None:
                kanji_reading_data["lengths"][len(matched_reading)] = True

                if reading_variant == "u_dropped":
                    # For onyomi u-dropped variants, cache with a suffix in the key, so that
                    # checking them can be skipped when there's no okurigana
                    matched_reading += "_u_dropped"
                kanji_reading_data["onyomi"][matched_reading] = [
                    onyomi_reading,
                    reading_variant,
                ]

            check_reading_match(
                # Pass hiragana reading for matching/caching
                reading=reading_hiragana,
                mora_string="",
                cache_func=cache_reading,
                okurigana="っ",
                logger=logger,
            )

        # Match kunyomi readings
        kunyomi_readings = [r.strip() for r in kunyomi.split("、")]
        for kunyomi_reading in kunyomi_readings:
            readings_to_try: list[KunyomiReadingToTry] = get_kunyomi_reading_variants(
                kunyomi_reading, kanji, logger=logger
            )

            def cache_reading(matched_reading: str, reading_variant: str) -> None:
                kanji_reading_data["lengths"][len(matched_reading)] = True

                if reading_variant == "u_dropped":
                    # For kunyomi u-dropped variants, cache with a suffix in the key, so that
                    # checking them can be skipped when there's no okurigana
                    matched_reading += "_u_dropped"
                prev_value = kanji_reading_data["kunyomi"].get(matched_reading, [])
                # Append to existing list, add mutated value back
                prev_value.append([kunyomi_reading, reading_variant])
                kanji_reading_data["kunyomi"][matched_reading] = prev_value

            for reading_to_match, _, _ in readings_to_try:
                # For kunyomi, don't pass okurigana here - just cache the plain readings
                # and common phonetic variants without special okurigana handling
                check_reading_match(
                    reading=reading_to_match,
                    mora_string="",
                    cache_func=cache_reading,
                    okurigana="っ",
                    logger=logger,
                )

        all_kanji_reading_data[kanji] = kanji_reading_data

    output_filepath = os.path.join(KANJI_DIR, "all_kanji_reading_data.json")
    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(all_kanji_reading_data, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    generate_cached_reading_data()
