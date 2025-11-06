# %%
from dataclasses import dataclass
from typing import Optional, Callable

from polars import lit, when, Expr, col

from .._utils.types import RowCheckType
from .._base import BaseCheck, CheckFailLevel, ThresholdType, _CheckParams
from .._utils.data_checks import (
    ROW_VALIDATION_SUCCESS_VALUE,
)
from ....types.validation.threshold import CheckThreshold
from ....exceptions import CheckConfigurationError


# %%


@dataclass(frozen=True, kw_only=True)
class _CustomParams(_CheckParams):
    expr: Callable[[Expr], Expr] | Expr


class CheckCustom(BaseCheck):
    """
    Custom Validation check: Ensures that column values are not empty or null.

    Parameters:
        function (Callable[[Expr], Expr] | Expr): Polars expression or callable/lambda that takes (source_col: pl.Expr) and returns a pl.Expr.

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
        function: Callable[[Expr], Expr] | Expr,
        *,
        # --------------------------------------------
        label: str,
        remove_row_on_fail: bool = False,
        alias: str | None = None,
        check_on_cleaned: bool = False,
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        message: str = "{{column}} has {{count}} failed value(s) ({{fraction}})",
    ):
        if not callable(function) and not isinstance(function, Expr):
            raise CheckConfigurationError(
                "A function or Polars Expression must be provided"
            )
        if callable(function) and not isinstance(function, Expr):
            if not isinstance(function(col("test")), Expr):
                raise CheckConfigurationError(
                    "Function must return a Polars Expression (pl.Expr)"
                )
        if label is None:
            raise CheckConfigurationError("Label must be provided")

        # assert json.loads(function.meta.serialize(format="json")).get("BinaryExpr") is not None

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
            label=label,
        )
        self._params = self._create_extended_params(
            _CustomParams,
            expr=function,
        )

    @classmethod
    def method_id(cls) -> str:
        return RowCheckType.CUSTOM.value

    def expression(
        self, source_column: str, alias: str, fail_value: CheckFailLevel = "fail"
    ) -> Expr:
        if isinstance(self._params.expr, Expr):
            expr = self._params.expr
        else:
            expr = self._params.expr(col(source_column))

        return (
            when(expr)
            .then(lit(ROW_VALIDATION_SUCCESS_VALUE))
            .otherwise(lit(fail_value))
            .alias(alias)
        )
