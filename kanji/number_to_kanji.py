import re

from ..utils.logger import package_logger as logger

JPN_NUMBER_TO_NUM = {
    "１": 1,
    "２": 2,
    "３": 3,
    "４": 4,
    "５": 5,
    "６": 6,
    "７": 7,
    "８": 8,
    "９": 9,
    "０": 0,
}


KANJI_NUMERALS = {
    0: "零",
    1: "一",
    2: "二",
    3: "三",
    4: "四",
    5: "五",
    6: "六",
    7: "七",
    8: "八",
    9: "九",
}

KANJI_UNITS = {
    1: "",
    10: "十",
    100: "百",
    1000: "千",
    10000: "万",
    # 億 is 万 number of 万
    100000000: "億",
    # 兆 is 万 number of 億
    1000000000000: "兆",
    # 京 is 万 number of 兆 etc.
    10000000000000000: "京",
}

# 十/百/千 vs the myriad units 万/億/兆/京: a leading 一 is dropped before the former but kept
# before the latter.
SUB_MYRIAD_UNITS = "".join(kanji for unit, kanji in KANJI_UNITS.items() if 1 < unit < 10000)
MYRIAD_UNITS = "".join(kanji for unit, kanji in KANJI_UNITS.items() if unit >= 10000)

NUMBER_TO_KANJI = {}
for num, kanji in KANJI_NUMERALS.items():
    NUMBER_TO_KANJI[str(num)] = kanji
for jpn_num, num in JPN_NUMBER_TO_NUM.items():
    NUMBER_TO_KANJI[jpn_num] = KANJI_NUMERALS[num]


def recursive_number_to_kanji(num: int, result: list[str], digit_mult=1) -> None:
    """
    Recursively converts a number to its kanji representation.
    Args:
        num (int): The number to convert.
        result (list[str]): The list to append the kanji representation to.
    """
    logger.debug("Converting number: %s, digit_mult: %s", num, digit_mult)
    unit = 1
    # how many 十, 百, 千, 万, 億 we have
    while num > 0:
        digit = num % 10
        logger.debug("Processing digit: %s, unit: %s", digit, unit)
        if digit > 0:
            try:
                kanji_digit = NUMBER_TO_KANJI[str(digit)]
            except KeyError:
                logger.error("Digit %s not found in NUMBER_TO_KANJI mapping.", digit)
                return
            if unit in KANJI_UNITS:
                logger.debug("Adding kanji digit %s with unit %s", kanji_digit, KANJI_UNITS[unit])
                # digit_mult > 1 means the recursion split off a 十/百/千 of this unit, so
                # the digit carries that sub-unit with it: 1000万 -> 一千 + 万. The 一 in front of the
                # sub-unit is always written here; number_to_kanji decides whether to drop it.
                if digit_mult > 1 and digit_mult in KANJI_UNITS:
                    kanji_digit += KANJI_UNITS[digit_mult]
                partial_num = kanji_digit
                cur_unit = KANJI_UNITS[unit]
                # If previous units is the same, omit it from this append
                max_further_index = len(result) - 1
                if cur_unit == "万":
                    max_further_index = len(result) - 3
                if cur_unit == "億":
                    max_further_index -= 4
                if cur_unit == "兆":
                    max_further_index -= 7
                if cur_unit == "京":
                    max_further_index -= 11
                further_index = len(result) - 1
                found_same_unit = False
                while (
                    further_index >= 0
                    and further_index >= max_further_index
                    and not found_same_unit
                ):
                    if result[further_index].endswith(cur_unit):
                        found_same_unit = True
                    further_index -= 1

                logger.debug(
                    "Cur unit: %s, Found same unit: %s, further_index: %s, max_further_index: %s",
                    cur_unit,
                    found_same_unit,
                    further_index,
                    max_further_index,
                )
                if not found_same_unit:
                    partial_num += cur_unit
                result.append(partial_num)
                logger.debug("Appended %s to result, current result: %s", partial_num, result)
            else:
                # The unit is a multiple of another smaller unit, start from 10
                logger.debug("Recursive call for unit %s, digit %s", unit, digit)
                sub_num = digit * unit // 10
                logger.debug("Recursively processing number %s", sub_num)
                recursive_number_to_kanji(sub_num, result, digit_mult * 10)

        num //= 10
        unit *= 10


def number_to_kanji(num_str: str) -> str:
    """
    Converts a string representation of a number into its kanji representation.

    Args:
        num_str (str): The string representation of the number to convert.

    Returns:
        str: The kanji representation of the number.
    """

    # Normalize the input string to handle full-width characters
    clean_num_str = num_str.strip()
    clean_num_str = "".join(str(JPN_NUMBER_TO_NUM.get(char, char)) for char in num_str)

    if not clean_num_str.isdigit():
        logger.debug("Input string '%s' is not a valid number.", num_str)
        # If the string contains non-digit characters, return it as is
        return num_str

    num = int(clean_num_str)

    if num in KANJI_NUMERALS:
        return KANJI_NUMERALS[num]

    result: list[str] = []

    recursive_number_to_kanji(num, result, digit_mult=1)

    # Reverse the result to get the correct order
    result.reverse()
    kanji_result = "".join(result)
    # Remove the 一 in front of 十, 百 and 千 (十, 二百, 千二百) but never in front of 万 and
    # above, which always keep it (一万, 一億). A 千 that tops a 万-group keeps it too, so
    # 10000000 is 一千万 and not 千万.
    kanji_result = re.sub(rf"一(?=[{SUB_MYRIAD_UNITS}])(?!千[{MYRIAD_UNITS}])", "", kanji_result)
    logger.debug("Stripped leading '一' where droppable, result: %s", kanji_result)

    return kanji_result
