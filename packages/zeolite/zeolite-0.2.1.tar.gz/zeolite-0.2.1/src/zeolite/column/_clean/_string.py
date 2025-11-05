from dataclasses import dataclass

from polars import Expr

from ._base import CleanColumn, _CleanParams
from ...types import ColumnDataType
from ...types.sensitivity import Sensitivity
from ..._utils.sanitise import SanitiseLevelType, SanitiseLevel, sanitise_string_col
from ...exceptions import CleanConfigurationError


# %%-----------------------------------------------------------------
# String Cleans
# ------------------------------------------------------------------


@dataclass(frozen=True, kw_only=True)
class _StringParams(_CleanParams):
    sanitise: SanitiseLevelType | None
    sanitise_join_char: str | None


class CleanStringColumn(CleanColumn):
    def __init__(
        self,
        *,
        sanitise: SanitiseLevelType | None = None,
        sanitise_join_char: str = "_",
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
        data_type: ColumnDataType = None,
    ):
        if sanitise is not None and sanitise not in SanitiseLevel:
            raise CleanConfigurationError(
                f"sanitise must be one of {', '.join(f"'{s}'" for s in SanitiseLevel)} or None. Received {sanitise}"
            )
        super().__init__(
            data_type=data_type or "string" if sanitise is None else "sanitised_string",
            col_sensitivity=col_sensitivity,
            alias=alias,
        )
        self._params = self._create_extended_params(
            _StringParams,
            sanitise=sanitise,
            sanitise_join_char=sanitise_join_char,
        )

    def _sanitise(self, source_column: str | Expr) -> Expr:
        return sanitise_string_col(
            source_column,
            sanitise_level=self._params.sanitise,
            join_char=self._params.sanitise_join_char,
        )

    def clean_expr(self, source_column: str, alias: str) -> Expr:
        return self._sanitise(source_column).alias(alias)


class CleanSanitisedStringColumn(CleanStringColumn):
    _required_args = {"sanitise"}

    def __init__(
        self,
        *,
        sanitise: SanitiseLevelType = "full",
        sanitise_join_char: str = "_",
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        if sanitise not in SanitiseLevel:
            raise CleanConfigurationError(
                f"sanitise must be one of {', '.join(f"'{s}'" for s in SanitiseLevel)}. Received {sanitise}"
            )

        super().__init__(
            data_type="sanitised_string",
            sanitise=sanitise,
            sanitise_join_char=sanitise_join_char,
            col_sensitivity=col_sensitivity,
            alias=alias,
        )
