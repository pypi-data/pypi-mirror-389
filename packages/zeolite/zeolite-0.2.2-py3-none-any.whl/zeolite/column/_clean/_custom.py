from dataclasses import dataclass
from typing import Callable

from polars import Expr, col

from ._base import CleanColumn, _CleanParams
from ...exceptions import CleanConfigurationError
from ...types.data_type import ColumnDataType
from ...types.sensitivity import Sensitivity


# %%-----------------------------------------------------------------
# Custom Clean Column
# ------------------------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class _CustomCleanParams(_CleanParams):
    function: Callable[[Expr], Expr] | Expr


class CustomCleanColumn(CleanColumn):
    """
    Custom cleaning column that allows users to define their own cleaning logic.

    Parameters:
        function: Polars expression or callable that takes (source_col: pl.Expr) and returns a pl.Expr.
        data_type: Data type of the cleaned column (default: "unknown")
        col_sensitivity: Optional sensitivity level for the cleaned column
        alias: Optional alias for the cleaned column output
    """

    _required_args = {"function"}

    def __init__(
        self,
        function: Callable[[Expr], Expr] | Expr,
        *,
        data_type: ColumnDataType = "unknown",
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        if not callable(function) and not isinstance(function, Expr):
            raise CleanConfigurationError(
                "A function or Polars Expression must be provided"
            )
        if callable(function) and not isinstance(function, Expr):
            if not isinstance(function(col("test")), Expr):
                raise CleanConfigurationError(
                    "function must return a Polars Expression (pl.Expr)"
                )

        super().__init__(
            data_type=data_type,
            col_sensitivity=col_sensitivity,
            alias=alias,
        )
        self._params = self._create_extended_params(
            _CustomCleanParams,
            function=function,
        )

    def clean_expr(self, source: str, alias: str) -> Expr:
        if isinstance(self._params.function, Expr):
            expr = self._params.function
        else:
            expr = self._params.function(col(source))
        return expr.alias(alias)
