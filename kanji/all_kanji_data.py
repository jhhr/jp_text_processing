import os
import json

try:
    from all_types.main_types import KanjiData
except ImportError:
    from ..all_types.main_types import KanjiData

# import all_kanji_data from the json file in ./all_kanji_data.json

KANJI_DIR = os.path.dirname(os.path.abspath(__file__))
KANJI_DATA_FILEPATH = os.path.join(KANJI_DIR, "all_kanji_data.json")

all_kanji_data: dict[str, KanjiData] = {}
with open(KANJI_DATA_FILEPATH, "r", encoding="utf-8") as f:
    all_kanji_data = json.load(f)
