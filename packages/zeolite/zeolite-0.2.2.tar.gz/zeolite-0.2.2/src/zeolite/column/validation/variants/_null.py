# %%
from dataclasses import dataclass
from typing import Optional

from polars import Expr

from .._utils.types import RowCheckType
from .._base import BaseCheck, CheckFailLevel, ThresholdType, _CheckParams
from .._utils.data_checks import (
    check_col_row_not_empty,
)
from ....types.validation.threshold import CheckThreshold


# %%


@dataclass(frozen=True, kw_only=True)
class _EmptyParams(_CheckParams):
    treat_empty_strings_as_null: bool


class CheckIsNotNull(BaseCheck):
    """
    Validation check: Ensures that column values are not empty or null.

    Parameters:
        treat_empty_strings_as_null (bool): Whether to treat empty strings as null.

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
        *,
        treat_empty_strings_as_null: bool = True,
        # --------------------------------------------
        remove_row_on_fail: bool = False,
        alias: str | None = None,
        check_on_cleaned: bool = False,
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        message: str = "{{column}} has {{count}} null (empty) value(s) ({{fraction}})",
    ):
        super().__init__(
            remove_row_on_fail=remove_row_on_fail,
            alias=alias,
            check_on_cleaned=check_on_cleaned,
            message=message,
            thresholds=thresholds,
            debug=debug,
            warning=warning,
            error=error,
            reject=reject,
        )
        self._params = self._create_extended_params(
            _EmptyParams,
            treat_empty_strings_as_null=treat_empty_strings_as_null,
        )

    @classmethod
    def method_id(cls) -> str:
        return RowCheckType.IS_NOT_NULL.value

    def expression(
        self, source_column: str, alias: str, fail_value: CheckFailLevel = "fail"
    ) -> Expr:
        return check_col_row_not_empty(
            source_column,
            alias=alias,
            str_check=self._params.treat_empty_strings_as_null,
            error_as_value=fail_value,
        )
