import os
import json

try:
    from all_types.main_types import KanjiReadingData
except ImportError:
    from ..all_types.main_types import KanjiReadingData

# import all_kanji_reading_data from the json file in ./all_kanji_reading_data.json

KANJI_DIR = os.path.dirname(os.path.abspath(__file__))
KANJI_READING_DATA_FILEPATH = os.path.join(KANJI_DIR, "all_kanji_reading_data.json")

all_kanji_reading_data: dict[str, KanjiReadingData] = {}

if os.path.exists(KANJI_READING_DATA_FILEPATH):
    with open(KANJI_READING_DATA_FILEPATH, "r", encoding="utf-8") as f:
        all_kanji_reading_data = json.load(f)
else:
    print(f"Warning: Kanji reading data file not found at {KANJI_READING_DATA_FILEPATH}")
