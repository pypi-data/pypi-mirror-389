from enum import Enum
from typing import Literal


class RowCheckType(Enum):
    IS_NOT_NULL = "is_not_null"
    IS_UNIQUE = "is_unique"
    IS_VALID_DATE = "is_valid_date"
    IS_EQUAL_TO = "is_equal_to"
    IS_NOT_EQUAL_TO = "is_not_equal_to"
    IS_PATTERN_MATCH = "is_matched_to"
    IS_NOT_PATTERN_MATCH = "is_not_matched_to"
    IS_IN = "is_in"
    IS_NOT_IN = "is_not_in"
    IS_LESS_THAN = "is_less_than"
    IS_LESS_EQUAL = "is_less_than_or_equal_to"
    IS_GREATER_THAN = "is_greater_than"
    IS_GREATER_EQUAL = "is_greater_than_or_equal_to"
    IS_BETWEEN = "is_between"
    STR_LENGTH = "is_length"
    CUSTOM = "is_custom"


type RangeBounds = Literal["both", "min", "max", "inclusive", "exclusive", True, False]
