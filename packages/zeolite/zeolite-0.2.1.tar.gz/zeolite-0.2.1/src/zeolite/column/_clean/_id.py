from dataclasses import dataclass

from polars import Expr, col, lit, String

from ._string import CleanStringColumn, _StringParams
from ..._utils.sanitise import SanitiseLevelType
from ...ref import ColumnRef
from ...types.sensitivity import Sensitivity


# %%-----------------------------------------------------------------
# Id Cleans
# ------------------------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class _IdParams(_StringParams):
    prefix: ColumnRef | str | None
    separator: str


class CleanIdColumn(CleanStringColumn):
    def __init__(
        self,
        *,
        prefix: ColumnRef | str | None = None,
        separator: str = "::",
        sanitise: SanitiseLevelType | None = None,
        sanitise_join_char: str = "_",
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        super().__init__(
            data_type="id",
            col_sensitivity=col_sensitivity,
            sanitise=sanitise,
            sanitise_join_char=sanitise_join_char,
            alias=alias,
        )
        self._params = self._create_extended_params(
            _IdParams,
            prefix=prefix,
            separator=separator,
        )

    def prefix(self, prefix: ColumnRef | str):
        self._replace(prefix=prefix)

    def clean_expr(self, source_column: str, alias: str) -> Expr:
        if self._params.prefix is not None:
            prefix_expr = (
                col(self._params.prefix.name).cast(String).str.strip_chars()
                if isinstance(self._params.prefix, ColumnRef)
                else lit(str(self._params.prefix).strip())
            ) + self._params.separator
            return (
                prefix_expr
                + self._sanitise(
                    col(source_column).cast(String).str.strip_prefix(prefix_expr)
                )
            ).alias(alias)
        else:
            return self._sanitise(source_column).alias(alias)
