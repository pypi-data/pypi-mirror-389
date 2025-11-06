from dataclasses import dataclass

from polars import col, Expr, Int64, Float64, Decimal, String

from ._base import CleanColumn, _CleanParams
from ...types.sensitivity import Sensitivity


# %%-----------------------------------------------------------------
# Number Cleans
# ------------------------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class _NumberParams(_CleanParams):
    output_format: type[Int64 | Float64]


def _clean_float(
    name: str, *, thousand_separator=",", output_format: Float64 | Decimal = Float64
) -> Expr:
    return (
        col(name)
        .cast(String, strict=False)
        .str.replace_all(" ", "")
        .str.replace_all(thousand_separator, "")
        .cast(output_format, strict=False)
    )


class CleanNumberColumn(CleanColumn):
    def __init__(
        self,
        *,
        output_format: type[Int64 | Float64] = Float64,
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        super().__init__(
            data_type="integer" if output_format == Int64 else "float",
            col_sensitivity=col_sensitivity,
            alias=alias,
        )
        self._params = self._create_extended_params(
            _NumberParams,
            output_format=output_format,
        )

    def clean_expr(self, source_column: str, alias: str) -> Expr:
        output = self._params.output_format
        expr = _clean_float(source_column)

        if output == Float64:
            return expr.alias(alias)
        elif output == Int64:
            return expr.round(0).cast(Int64).alias(alias)
        else:
            return col(source_column).cast(output, strict=False).alias(alias)


class CleanIntegerColumn(CleanNumberColumn):
    def __init__(
        self,
        *,
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        super().__init__(
            output_format=Int64, col_sensitivity=col_sensitivity, alias=alias
        )


@dataclass(frozen=True, kw_only=True)
class _DecimalParams(_CleanParams):
    scale: int
    output_format: type[Int64 | Float64]


class CleanDecimalColumn(CleanColumn):
    def __init__(
        self,
        *,
        decimal_places: int = 2,
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        super().__init__(
            data_type="decimal", col_sensitivity=col_sensitivity, alias=alias
        )
        self._params = self._create_extended_params(
            _DecimalParams,
            scale=decimal_places,
        )

    def clean_expr(self, source_column: str, alias: str) -> Expr:
        return _clean_float(
            source_column, output_format=Decimal(None, self._params.scale)
        ).alias(alias)
