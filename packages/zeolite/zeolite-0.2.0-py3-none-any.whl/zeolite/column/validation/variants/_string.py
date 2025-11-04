from dataclasses import dataclass
from typing import Optional
import re

from polars import lit, col, when, Expr

from .._utils.range import get_range_bounds
from .._utils.types import RowCheckType, RangeBounds
from .._base import BaseCheck, CheckFailLevel, ThresholdType, _CheckParams
from .._utils.data_checks import (
    ROW_VALIDATION_SUCCESS_VALUE,
)
from ....exceptions import CheckConfigurationError
from ....types.validation.threshold import CheckThreshold


# %%
@dataclass(frozen=True, kw_only=True)
class _PatternMatchParams(_CheckParams):
    pattern: str
    is_inverse: bool
    regex_flags: int = 0  # re.IGNORECASE, re.MULTILINE, etc.


class _BasePatternCheck(BaseCheck):
    """
    Base class for pattern-based validation checks.
    """

    _required_args = {"pattern"}

    def __init__(
        self,
        pattern: str,
        *,
        message: Optional[str] = None,
        is_inverse: bool = False,
        regex_flags: int = 0,
        **kwargs,
    ):
        if message is None:
            message = (
                "{{column}} has {{count}} row(s) not matching pattern `{{match_value}}` ({{fraction}})"
                if not is_inverse
                else "{{column}} has {{count}} row(s) matching pattern `{{match_value}}` ({{fraction}})"
            )

        # Validate the pattern is a valid regex
        try:
            re.compile(pattern, regex_flags)
        except re.error as e:
            raise CheckConfigurationError(f"Invalid regex pattern: {e}")

        super().__init__(
            **kwargs,
            message=message.replace("{{match_value}}", pattern),
            label=f"{self.method_id()}_{pattern}".lower().replace(" ", "_"),
        )
        self._params = self._create_extended_params(
            _PatternMatchParams,
            pattern=pattern,
            is_inverse=is_inverse,
            regex_flags=regex_flags,
        )

    def expression(
        self, source_column: str, alias: str, fail_value: CheckFailLevel = "fail"
    ) -> Expr:
        if not self._params.is_inverse:
            return (
                when(col(source_column).str.contains(self._params.pattern))
                .then(lit(ROW_VALIDATION_SUCCESS_VALUE))
                .otherwise(lit(fail_value))
                .alias(alias)
            )
        else:
            return (
                when(col(source_column).str.contains(self._params.pattern))
                .then(lit(fail_value))
                .otherwise(lit(ROW_VALIDATION_SUCCESS_VALUE))
                .alias(alias)
            )


class CheckIsStrPatternMatch(_BasePatternCheck):
    """
    Validation check: Ensures that column values match a specified regex pattern. This will
    throw an error if the value DOES NOT MATCH the pattern.

    Parameters:
        pattern (str): The regex pattern to match against.
        regex_flags (int): Regex flags (e.g., re.IGNORECASE, re.MULTILINE).
        remove_row_on_fail (bool): Whether to exclude rows with empty values.
        check_on_cleaned (bool): Whether to check on cleaned column or the original.
        thresholds (Threshold): Thresholds for error capturing when the table is processed.
        warning (CheckThreshold): Warning threshold (used when no thresholds are provided).
        error (CheckThreshold): Error threshold (used when no thresholds are provided).
        reject (CheckThreshold): Reject threshold (used when no thresholds are provided).
        message (str): Error message template.
    """

    def __init__(
        self,
        pattern: str,
        *,
        regex_flags: int = 0,
        remove_row_on_fail: bool = False,
        check_on_cleaned: bool = False,
        alias: str | None = None,
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        message: Optional[str] = None,
    ):
        super().__init__(
            pattern=pattern,
            is_inverse=False,
            regex_flags=regex_flags,
            remove_row_on_fail=remove_row_on_fail,
            check_on_cleaned=check_on_cleaned,
            alias=alias,
            thresholds=thresholds,
            debug=debug,
            warning=warning,
            error=error,
            reject=reject,
            message=message,
        )

    @classmethod
    def method_id(cls) -> str:
        return RowCheckType.IS_PATTERN_MATCH.value


class CheckIsNotStrPatternMatch(_BasePatternCheck):
    """
    Validation check: Ensures that column values do NOT match a specified regex pattern. This will
    throw an error if the value DOES MATCH the pattern.

    Parameters:
        pattern (str): The regex pattern to match against.
        regex_flags (int): Regex flags (e.g., re.IGNORECASE, re.MULTILINE).
        remove_row_on_fail (bool): Whether to exclude rows with empty values.
        check_on_cleaned (bool): Whether to check on cleaned column or the original.
        thresholds (Threshold): Thresholds for error capturing when the table is processed.
        warning (CheckThreshold): Warning threshold (used when no thresholds are provided).
        error (CheckThreshold): Error threshold (used when no thresholds are provided).
        reject (CheckThreshold): Reject threshold (used when no thresholds are provided).
        message (str): Error message template.
    """

    def __init__(
        self,
        pattern: str,
        *,
        regex_flags: int = 0,
        remove_row_on_fail: bool = False,
        check_on_cleaned: bool = False,
        alias: str | None = None,
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        message: Optional[str] = None,
    ):
        super().__init__(
            pattern=pattern,
            is_inverse=True,
            regex_flags=regex_flags,
            remove_row_on_fail=remove_row_on_fail,
            check_on_cleaned=check_on_cleaned,
            alias=alias,
            thresholds=thresholds,
            debug=debug,
            warning=warning,
            error=error,
            reject=reject,
            message=message,
        )

    @classmethod
    def method_id(cls) -> str:
        return RowCheckType.IS_NOT_PATTERN_MATCH.value


# %%


@dataclass(frozen=True, kw_only=True)
class _StrLengthParams(_CheckParams):
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    is_inclusive: RangeBounds = True
    trim: bool = True


class CheckStrLength(BaseCheck):
    """
    Validation check: Ensures that string column values have a length within specified bounds.
    At least one of min_length or max_length must be specified.

    Parameters:
        min_length (int, optional): Minimum allowed string length (inclusive).
        max_length (int, optional): Maximum allowed string length (inclusive).
        is_inclusive (RangeBounds): Should the check include the values (e.g. '>=' vs '>').
        trim (RangeBounds): Should the string get trimmed before checking length.
        remove_row_on_fail (bool): Whether to exclude rows with invalid lengths.
        check_on_cleaned (bool): Whether to check on cleaned column or the original.
        thresholds (Threshold): Thresholds for error capturing when the table is processed.
        warning (CheckThreshold): Warning threshold (used when no thresholds are provided).
        error (CheckThreshold): Error threshold (used when no thresholds are provided).
        reject (CheckThreshold): Reject threshold (used when no thresholds are provided).
        message (str): Error message template.
    """

    _required_args = {"min_length", "max_length"}

    def __init__(
        self,
        *,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        is_inclusive: RangeBounds = True,
        trim: bool = False,
        remove_row_on_fail: bool = False,
        check_on_cleaned: bool = False,
        alias: str | None = None,
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        message: Optional[str] = None,
    ):
        if min_length is None and max_length is None:
            raise CheckConfigurationError(
                "At least one of min_length or max_length must be specified"
            )

        if min_length is not None and max_length is not None:
            if min_length > max_length:
                raise CheckConfigurationError(
                    "min_length cannot be greater than max_length"
                )

        if (min_length is not None and min_length < 0) or (
            max_length is not None and max_length < 0
        ):
            raise CheckConfigurationError(
                "min_length/max_length must be greater than or equal to 0"
            )

        if message is None:
            if min_length is not None and max_length is not None:
                message = "{{column}} has {{count}} row(s) with length not between `{{min_length}} <-> {{max_length}}` ({{fraction}})"
            elif min_length is not None:
                message = "{{column}} has {{count}} row(s) with length less than min `{{min_length}}` ({{fraction}})"
            else:
                message = "{{column}} has {{count}} row(s) with length greater than max `{{max_length}}` ({{fraction}})"

        if min_length is not None and max_length is not None:
            label = f"{self.method_id()}_between_{min_length}_and_{max_length}"
        elif min_length is not None:
            label = f"{self.method_id()}_greater_than_{min_length}"
        else:
            label = f"{self.method_id()}_less_than_{max_length}"

        super().__init__(
            remove_row_on_fail=remove_row_on_fail,
            alias=alias,
            check_on_cleaned=check_on_cleaned,
            message=message.replace("{{min_length}}", str(min_length)).replace(
                "{{max_length}}", str(max_length)
            ),
            thresholds=thresholds,
            debug=debug,
            warning=warning,
            error=error,
            reject=reject,
            label=label,
        )
        self._params = self._create_extended_params(
            _StrLengthParams,
            min_length=min_length,
            max_length=max_length,
            is_inclusive=is_inclusive,
            trim=trim,
        )

    def expression(
        self, source_column: str, alias: str, fail_value: CheckFailLevel = "fail"
    ) -> Expr:
        if self._params.trim:
            length_expr = col(source_column).str.strip_chars().str.len_chars()
        else:
            length_expr = col(source_column).str.len_chars()

        min_len = self._params.min_length
        max_len = self._params.max_length
        bounds = get_range_bounds(self._params.is_inclusive)
        if min_len is not None and max_len is not None:
            condition = length_expr.is_between(min_len, max_len, bounds)
        elif min_len is not None:
            if bounds == "both" or bounds == "min":
                condition = length_expr.ge(min_len)
            else:
                condition = length_expr.gt(min_len)
        else:
            if bounds == "both" or bounds == "max":
                condition = length_expr.le(max_len)
            else:
                condition = length_expr.lt(max_len)

        return (
            when(condition)
            .then(lit(ROW_VALIDATION_SUCCESS_VALUE))
            .otherwise(lit(fail_value))
            .alias(alias)
        )

    @classmethod
    def method_id(cls) -> str:
        return RowCheckType.STR_LENGTH.value


# %%
