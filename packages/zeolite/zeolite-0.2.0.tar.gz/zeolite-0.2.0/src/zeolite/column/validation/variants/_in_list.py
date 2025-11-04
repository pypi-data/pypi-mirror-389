from dataclasses import dataclass
from typing import Optional
from collections.abc import Collection

from polars import lit, col, when, Expr

from .._utils.types import RowCheckType
from .._base import BaseCheck, CheckFailLevel, ThresholdType, _CheckParams
from .._utils.data_checks import (
    ROW_VALIDATION_SUCCESS_VALUE,
)
from ....types.validation.threshold import CheckThreshold
from ....exceptions import CheckConfigurationError

# %%


@dataclass(frozen=True, kw_only=True)
class _ListMatchParams(_CheckParams):
    values: Collection[str | int | float | bool]
    is_inverse: bool


class _BaseListCheck(BaseCheck):
    """
    Base class for list-based validation checks.
    """

    def __init__(
        self,
        values: Collection[str | int | float | bool],
        *,
        message: Optional[str] = None,
        is_inverse: bool = False,
        **kwargs,
    ):
        if message is None:
            message = (
                "{{column}} has {{count}} row(s) not in `[ {{match_value}} ]` ({{fraction}})"
                if not is_inverse
                else "{{column}} has {{count}} row(s) in `[ {{match_value}} ]` ({{fraction}})"
            )

        if not isinstance(values, Collection):
            raise CheckConfigurationError("values must be an iterable collection")
        v_list = list(values)

        values_str = (
            f"{v_list[0]} | {v_list[1]} ... {v_list[2]} | {v_list[-1]}"
            if len(v_list) > 5
            else " | ".join(str(x) for x in v_list)
        )
        formatted_label = (
            f"{v_list[0]}...{v_list[-1]}"
            if len(v_list) > 3
            else values_str.lower().replace(" | ", "|").replace(" ", "_")
        )

        super().__init__(
            **kwargs,
            message=message.replace("{{match_value}}", str(values_str)),
            label=f"{self.method_id()}_[{formatted_label}]",
        )
        self._params = self._create_extended_params(
            _ListMatchParams,
            values=v_list,
            is_inverse=is_inverse,
        )

    def expression(
        self, source_column: str, alias: str, fail_value: CheckFailLevel = "fail"
    ) -> Expr:
        if not self._params.is_inverse:
            return (
                when(col(source_column).is_in(self._params.values))
                .then(lit(ROW_VALIDATION_SUCCESS_VALUE))
                .otherwise(lit(fail_value))
                .alias(alias)
            )
        else:
            return (
                when(col(source_column).is_in(self._params.values))
                .then(lit(fail_value))
                .otherwise(lit(ROW_VALIDATION_SUCCESS_VALUE))
                .alias(alias)
            )


class CheckIsIn(_BaseListCheck):
    """
    Validation check: Ensures that column values are in a list of given values.

    Parameters:
        allowed_values (Iterable[str | int | float | bool]): The list of values to check against.
        remove_row_on_fail (bool): Whether to exclude rows with empty values.
        check_on_cleaned (bool): Whether to check on cleaned column or the original.
        thresholds (Threshold): Thresholds for error capturing when the table is processed.
        warning (CheckThreshold): Warning threshold (used when no thresholds are provided).
        error (CheckThreshold): Error threshold (used when no thresholds are provided).
        reject (CheckThreshold): Reject threshold (used when no thresholds are provided).
        message (str): Error message template.
    """

    _required_args = {"allowed_values"}

    def __init__(
        self,
        allowed_values: Collection[str | int | float | bool],
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
            values=allowed_values,
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
        return RowCheckType.IS_IN.value


class CheckIsNotIn(_BaseListCheck):
    """
    Validation check: Ensures that column values are NOT in a list of given values.

    Parameters:
        restricted_values (Iterable[str | int | float | bool]): The list of values to check against.
        remove_row_on_fail (bool): Whether to exclude rows with empty values.
        check_on_cleaned (bool): Whether to check on cleaned column or the original.
        thresholds (Threshold): Thresholds for error capturing when the table is processed.
        warning (CheckThreshold): Warning threshold (used when no thresholds are provided).
        error (CheckThreshold): Error threshold (used when no thresholds are provided).
        reject (CheckThreshold): Reject threshold (used when no thresholds are provided).
        message (str): Error message template.
    """

    _required_args = {"restricted_values"}

    def __init__(
        self,
        restricted_values: Collection[str | int | float | bool],
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
            values=restricted_values,
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
        return RowCheckType.IS_NOT_IN.value
