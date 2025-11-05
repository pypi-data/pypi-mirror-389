from dataclasses import dataclass
from typing import Optional, Union

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
class _NumericCompareParams(_CheckParams):
    value: Union[int, float]
    is_inclusive: bool = True


@dataclass(frozen=True, kw_only=True)
class _NumericRangeParams(_CheckParams):
    min_value: Union[int, float]
    max_value: Union[int, float]
    is_range_inclusive: RangeBounds = True


class _BaseNumericCompareCheck(BaseCheck):
    """
    Base class for numeric comparison validation checks.
    """

    _required_args = {"value"}

    def __init__(
        self,
        value: Union[int, float],
        *,
        message: Optional[str] = "",
        is_inclusive: bool = True,
        **kwargs,
    ):
        super().__init__(
            **kwargs,
            message=message.replace("{{match_value}}", str(value)),
            label=f"{self.method_id()}_{str(value)}",
        )
        self._params = self._create_extended_params(
            _NumericCompareParams,
            value=value,
            is_inclusive=is_inclusive,
        )


class _BaseNumericRangeCheck(BaseCheck):
    """
    Base class for numeric range validation checks.
    """

    _required_args = {"min_value", "max_value"}

    def __init__(
        self,
        min_value: Union[int, float],
        max_value: Union[int, float],
        *,
        message: Optional[str] = "",
        is_range_inclusive: RangeBounds = True,
        **kwargs,
    ):
        if min_value > max_value:
            raise CheckConfigurationError(
                "min_value must be less than or equal to max_value"
            )

        super().__init__(
            **kwargs,
            message=message.replace(
                "{{match_value}}", f"{str(min_value)}` and `{str(max_value)}"
            ),
            label=f"{self.method_id()}_{min_value}_to_{max_value}".lower().replace(
                " ", "_"
            ),
        )
        self._params = self._create_extended_params(
            _NumericRangeParams,
            min_value=min_value,
            max_value=max_value,
            is_range_inclusive=is_range_inclusive,
        )


class CheckIsLessThan(_BaseNumericCompareCheck):
    """
    Validation check: Ensures that column values are less than a specified value.
    This will throw an error if any value is greater than the specified value.

    Parameters:
        value (int | float): The value to compare against.
        is_inclusive (bool): Whether to include the boundary value in the check.
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
        value: Union[int, float],
        *,
        is_inclusive: bool = False,
        remove_row_on_fail: bool = False,
        check_on_cleaned: bool = False,
        alias: str | None = None,
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        message: Optional[
            str
        ] = "{{column}} has {{count}} row(s) greater than max `{{match_value}}` ({{fraction}})",
    ):
        super().__init__(
            value=value,
            is_inclusive=is_inclusive,
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
        return RowCheckType.IS_LESS_THAN.value

    def expression(
        self, source_column: str, alias: str, fail_value: CheckFailLevel = "fail"
    ) -> Expr:
        check_exp = (
            col(source_column).le(self._params.value)
            if self._params.is_inclusive
            else col(source_column).lt(self._params.value)
        )
        return (
            when(check_exp)
            .then(lit(ROW_VALIDATION_SUCCESS_VALUE))
            .otherwise(lit(fail_value))
            .alias(alias)
        )


class CheckIsLessThanOrEqual(CheckIsLessThan):
    """
    Validation check: Ensures that column values are less than a specified value.
    This will throw an error if any value is greater than or equal to the specified value.

    Parameters:
        value (int | float): The value to compare against.
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
        value: Union[int, float],
        *,
        remove_row_on_fail: bool = False,
        check_on_cleaned: bool = False,
        alias: str | None = None,
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        message: Optional[
            str
        ] = "{{column}} has {{count}} row(s) greater than or equal to max `{{match_value}}` ({{fraction}})",
    ):
        super().__init__(
            value=value,
            is_inclusive=True,
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
        return RowCheckType.IS_LESS_EQUAL.value


class CheckIsGreaterThan(_BaseNumericCompareCheck):
    """
    Validation check: Ensures that column values are greater than a specified value.
    This will throw an error if any value is less than the specified value.

    Parameters:
        value (int | float): The value to compare against.
        is_inclusive (bool): Whether to include the boundary value in the check.
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
        value: Union[int, float],
        *,
        is_inclusive: bool = False,
        remove_row_on_fail: bool = False,
        check_on_cleaned: bool = False,
        alias: str | None = None,
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        message: Optional[
            str
        ] = "{{column}} has {{count}} row(s) less than min `{{match_value}}` ({{fraction}})",
    ):
        super().__init__(
            value=value,
            is_inclusive=is_inclusive,
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
        return RowCheckType.IS_GREATER_THAN.value

    def expression(
        self, source_column: str, alias: str, fail_value: CheckFailLevel = "fail"
    ) -> Expr:
        check_exp = (
            col(source_column).ge(self._params.value)
            if self._params.is_inclusive
            else col(source_column).gt(self._params.value)
        )
        return (
            when(check_exp)
            .then(lit(ROW_VALIDATION_SUCCESS_VALUE))
            .otherwise(lit(fail_value))
            .alias(alias)
        )


class CheckIsGreaterThanOrEqual(CheckIsGreaterThan):
    """
    Validation check: Ensures that column values are greater than a specified value.
    This will throw an error if any value is less than or equal to the specified value.

    Parameters:
        value (int | float): The value to compare against.
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
        value: Union[int, float],
        *,
        remove_row_on_fail: bool = False,
        check_on_cleaned: bool = False,
        alias: str | None = None,
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        message: Optional[
            str
        ] = "{{column}} has {{count}} row(s) less than or equal to min `{{match_value}}` ({{fraction}})",
    ):
        super().__init__(
            value=value,
            is_inclusive=True,
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
        return RowCheckType.IS_GREATER_EQUAL.value


class CheckIsBetween(_BaseNumericRangeCheck):
    """
    Validation check: Ensures that column values are within a specified range.
    This will throw an error if any value is outside the specified range.

    Parameters:
        min_value (int | float): The minimum value of the range.
        max_value (int | float): The maximum value of the range.
        is_range_inclusive (bool): Whether to include the minimum and max value in the check.
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
        min_value: Union[int, float],
        max_value: Union[int, float],
        *,
        is_range_inclusive: RangeBounds = True,
        remove_row_on_fail: bool = False,
        check_on_cleaned: bool = False,
        alias: str | None = None,
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        message: Optional[
            str
        ] = "{{column}} has {{count}} row(s) which are not between `{{match_value}}` ({{fraction}})",
    ):
        super().__init__(
            min_value=min_value,
            max_value=max_value,
            is_range_inclusive=is_range_inclusive,
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
        return RowCheckType.IS_BETWEEN.value

    def expression(
        self, source_column: str, alias: str, fail_value: CheckFailLevel = "fail"
    ) -> Expr:
        bounds = get_range_bounds(self._params.is_range_inclusive)
        return (
            when(
                col(source_column).is_between(
                    self._params.min_value, self._params.max_value, bounds
                )
            )
            .then(lit(ROW_VALIDATION_SUCCESS_VALUE))
            .otherwise(lit(fail_value))
            .alias(alias)
        )


# %%
