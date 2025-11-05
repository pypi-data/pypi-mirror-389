from dataclasses import dataclass
from typing import Optional

from polars import lit, col, when, Expr

from .._utils.types import RowCheckType
from .._base import BaseCheck, CheckFailLevel, ThresholdType, _CheckParams
from .._utils.data_checks import (
    ROW_VALIDATION_SUCCESS_VALUE,
)
from ....types.validation.threshold import CheckThreshold


# %%
@dataclass(frozen=True, kw_only=True)
class _ValueMatchParams(_CheckParams):
    value: str | int | float | bool
    is_inverse: bool


class _BaseEqualityCheck(BaseCheck):
    """
    Base class for equality-based validation checks.
    """

    _required_args = {"value"}

    def __init__(
        self,
        value: str | int | float | bool,
        *,
        message: Optional[str] = None,
        is_inverse: bool = False,
        **kwargs,
    ):
        if message is None:
            message = (
                "{{column}} has {{count}} row(s) not equal to `{{match_value}}` ({{fraction}})"
                if not is_inverse
                else "{{column}} has {{count}} row(s) equal to `{{match_value}}` ({{fraction}})"
            )

        super().__init__(
            **kwargs,
            message=message.replace("{{match_value}}", str(value)),
            label=f"{self.method_id()}_{value}".lower().replace(" ", "_"),
        )
        self._params = self._create_extended_params(
            _ValueMatchParams,
            value=value,
            is_inverse=is_inverse,
        )

    def expression(
        self, source_column: str, alias: str, fail_value: CheckFailLevel = "fail"
    ) -> Expr:
        if not self._params.is_inverse:
            return (
                when(col(source_column).eq(self._params.value))
                .then(lit(ROW_VALIDATION_SUCCESS_VALUE))
                .otherwise(lit(fail_value))
                .alias(alias)
            )
        else:
            return (
                when(col(source_column).eq(self._params.value))
                .then(lit(fail_value))
                .otherwise(lit(ROW_VALIDATION_SUCCESS_VALUE))
                .alias(alias)
            )


class CheckIsEqualTo(_BaseEqualityCheck):
    """
    Validation check: Ensures that column values are equal to a specified value. This will
    throw an error if the value IS NOT FOUND in the column.

    Parameters:
        value (str | int | float | bool): The value to check against.
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
        value: str | int | float | bool,
        *,
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
            value=value,
            is_inverse=False,
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
        return RowCheckType.IS_EQUAL_TO.value


class CheckIsNotEqualTo(_BaseEqualityCheck):
    """
    Validation check: Ensures that column values are not equal to a specified value. This will
    throw an error if the value IS FOUND in the column.

    Parameters:
        value (str | int | float | bool): The value to check against.
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
        value: str | int | float | bool,
        *,
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
            value=value,
            is_inverse=True,
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
        return RowCheckType.IS_NOT_EQUAL_TO.value
