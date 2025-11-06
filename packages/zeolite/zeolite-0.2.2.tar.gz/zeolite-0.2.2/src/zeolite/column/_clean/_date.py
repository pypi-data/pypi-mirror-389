from dataclasses import dataclass

from typing import Literal
from polars import col, Expr, Date, Datetime, String, Time, duration, Float64

from ._base import CleanColumn, _CleanParams
from ..._utils.parse_dates import mega_date_handler
from ...exceptions import CleanConfigurationError
from ...types.sensitivity import Sensitivity


# %%-----------------------------------------------------------------
# Date Cleans
# ------------------------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class _DateParams(_CleanParams):
    output_format: Date | Datetime
    day_first: bool


class CleanDateColumn(CleanColumn):
    def __init__(
        self,
        *,
        output_format: Date | Datetime = Date,
        day_first: bool = True,
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        if output_format not in [Date, Datetime]:
            raise CleanConfigurationError(
                "output_format must be either pl.Date or pl.Datetime"
            )
        super().__init__(
            data_type="date" if output_format == Date else "datetime",
            col_sensitivity=col_sensitivity,
            alias=alias,
        )
        self._params = self._create_extended_params(
            _DateParams,
            output_format=output_format,
            day_first=day_first,
        )

    def clean_expr(self, source_column: str, alias: str) -> Expr:
        return mega_date_handler(
            source_column,
            alias=alias,
            output_format=self._params.output_format,
            day_first=self._params.day_first,
        )


class CleanDatetimeColumn(CleanDateColumn):
    def __init__(
        self,
        *,
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        super().__init__(
            output_format=Datetime, col_sensitivity=col_sensitivity, alias=alias
        )


@dataclass(frozen=True, kw_only=True)
class _TimeParams(_CleanParams):
    time_format: str


class CleanTimeColumn(CleanColumn):
    def __init__(
        self,
        *,
        time_format: str = "%H:%M",
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        super().__init__(data_type="time", col_sensitivity=col_sensitivity, alias=alias)
        self._params = self._create_extended_params(
            _TimeParams,
            time_format=time_format,
        )

    def clean_expr(self, source_column: str, alias: str) -> Expr:
        return (
            col(source_column)
            .cast(String)
            .str.strptime(Time, self._params.time_format)
            .alias(alias)
        )


type DurationType = Literal[
    "weeks",
    "days",
    "hours",
    "minutes",
    "seconds",
    "milliseconds",
    "microseconds",
    "nanoseconds",
]


@dataclass(frozen=True, kw_only=True)
class _DurationParams(_CleanParams):
    input_unit: DurationType
    output_unit: Literal[None, "us", "ms", "ns"]


class CleanDurationColumn(CleanColumn):
    _required_args = {"input_unit"}

    def __init__(
        self,
        *,
        input_unit: DurationType,
        output_unit: Literal[None, "us", "ms", "ns"] = None,
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        super().__init__(
            data_type="duration", col_sensitivity=col_sensitivity, alias=alias
        )
        self._params = self._create_extended_params(
            _DurationParams,
            input_unit=input_unit,
            output_unit=output_unit,
        )

    def clean_expr(self, source_column: str, alias: str) -> Expr:
        return duration(
            **{self._params.input_unit: col(source_column).cast(Float64)},
            time_unit=self._params.output_unit,
        ).alias(alias)
