from dataclasses import dataclass, field, KW_ONLY, asdict, replace
from typing import TypeVar
import polars as pl

from ...exceptions import CleanConfigurationError
from ...ref import ColumnRef
from ...types.data_type import ColumnDataType
from ...types.sensitivity import Sensitivity


def _get_column_names(source: "ColumnRef") -> tuple[str, str]:
    source_column = source.name
    # alias = self.alias if self.alias is not None else source.clean().name
    alias = source.clean().name
    return source_column, alias


@dataclass(frozen=True, kw_only=True)
class _CleanParams:
    _: KW_ONLY
    data_type: ColumnDataType = field(default="string")
    col_sensitivity: Sensitivity | None = field(default=None)
    alias: str | None = field(default=None)


T = TypeVar("T", bound="_CleanParams")


class CleanColumn:
    _required_args: set[str] = set()

    def __init__(
        self,
        *,
        data_type: ColumnDataType,
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        self._params = _CleanParams(
            data_type=data_type,
            col_sensitivity=col_sensitivity,
            alias=alias,
        )

    def alias(self, alias: str):
        return self._replace(alias=alias)

    @property
    def params(self) -> _CleanParams:
        return self._params

    def clean_ref(self, source: "ColumnRef") -> "ColumnRef":
        return source.clean()

    def get_alias(self, source: "ColumnRef") -> str:
        return self._params.alias if self._params.alias is not None else source.name

    def clean_expr(self, source: str, alias: str) -> pl.Expr:
        return pl.col(source).cast(pl.String).alias(alias)

    def apply(self, source: "ColumnRef") -> pl.Expr:
        source_column, alias = _get_column_names(source)
        return self.clean_expr(source_column, alias)

    def _create_extended_params(self, params_class: type[T], **extra_params) -> T:
        base_params = {k: v for k, v in asdict(self._params).items()}
        return params_class(
            **{**base_params, **extra_params},
        )

    def _replace(self, **kwargs):
        new_params = replace(self._params, **kwargs)

        args = {}
        for arg in self._required_args:
            if hasattr(new_params, arg):
                args[arg] = getattr(new_params, arg)
            elif hasattr(self, arg):
                args[arg] = getattr(self, arg)
            else:
                raise CleanConfigurationError(f"Required argument '{arg}' not found")

        return self.__class__(**args)._set_params(new_params)

    def _set_params(self, params: _CleanParams) -> "CleanColumn":
        self._params = params
        return self
