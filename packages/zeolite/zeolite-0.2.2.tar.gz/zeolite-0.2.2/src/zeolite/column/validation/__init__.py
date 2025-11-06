from ._base import BaseCheck, CheckFailLevel, ThresholdType
from ._utils.validation_node import create_validation_rule

from .variants import (
    CheckIsNotNull,
    CheckIsUnique,
    CheckIsEqualTo,
    CheckIsNotEqualTo,
    CheckIsIn,
    CheckIsNotIn,
    CheckIsLessThan,
    CheckIsLessThanOrEqual,
    CheckIsGreaterThan,
    CheckIsGreaterThanOrEqual,
    CheckIsBetween,
    CheckIsValidDate,
    CheckIsStrPatternMatch,
    CheckIsNotStrPatternMatch,
    CheckStrLength,
    CheckCustom,
)

type ColumnCheckType = (
    CheckIsNotNull
    | CheckIsUnique
    | CheckIsEqualTo
    | CheckIsNotEqualTo
    | CheckIsStrPatternMatch
    | CheckIsNotStrPatternMatch
    | CheckStrLength
    | CheckIsIn
    | CheckIsNotIn
    | CheckIsLessThan
    | CheckIsLessThanOrEqual
    | CheckIsGreaterThan
    | CheckIsGreaterThanOrEqual
    | CheckIsBetween
    | CheckIsValidDate
    | CheckCustom
)


class Check:
    not_null = CheckIsNotNull
    not_empty = CheckIsNotNull
    unique = CheckIsUnique
    distinct = CheckIsUnique
    eq = CheckIsEqualTo
    equal_to = CheckIsEqualTo
    ne = CheckIsNotEqualTo
    not_equal_to = CheckIsNotEqualTo
    is_in = CheckIsIn
    not_in = CheckIsNotIn
    less_than = CheckIsLessThan
    lt = CheckIsLessThan
    less_than_or_equal = CheckIsLessThanOrEqual
    lte = CheckIsLessThanOrEqual
    greater_than = CheckIsGreaterThan
    gt = CheckIsGreaterThan
    greater_than_or_equal = CheckIsGreaterThanOrEqual
    gte = CheckIsGreaterThanOrEqual
    between = CheckIsBetween
    in_range = CheckIsBetween
    valid_date = CheckIsValidDate
    str_matches = CheckIsStrPatternMatch
    str_not_matches = CheckIsNotStrPatternMatch
    str_len = CheckStrLength
    str_length = CheckStrLength
    custom = CheckCustom


__all__ = [
    "Check",
    "CheckIsNotNull",
    "CheckIsUnique",
    "CheckIsEqualTo",
    "CheckIsNotEqualTo",
    "CheckIsIn",
    "CheckIsNotIn",
    "CheckIsLessThan",
    "CheckIsGreaterThan",
    "CheckIsBetween",
    "CheckIsValidDate",
    "CheckIsStrPatternMatch",
    "CheckIsNotStrPatternMatch",
    "CheckStrLength",
    "CheckCustom",
    "ColumnCheckType",
    "ThresholdType",
    "BaseCheck",
    "CheckFailLevel",
    "create_validation_rule",
]
