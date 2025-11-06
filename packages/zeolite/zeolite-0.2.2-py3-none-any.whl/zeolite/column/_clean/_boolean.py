from dataclasses import dataclass

from typing import Any
from polars import Expr, Boolean

from ._base import CleanColumn, _CleanParams
from ..._utils.sanitise import sanitise_scalar_string, full_sanitise_string_col
from ...types.sensitivity import Sensitivity
from ...exceptions import CleanConfigurationError


# %%-----------------------------------------------------------------
# Boolean Cleans
# ------------------------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class _BooleanParams(_CleanParams):
    true_values: frozenset[Any] | set[Any]
    false_values: frozenset[Any] | set[Any]
    bool_map: dict[str, bool]


class CleanBooleanColumn(CleanColumn):
    def __init__(
        self,
        *,
        true_values: frozenset[Any] | set[Any] = frozenset({"yes", "y", "true", "1"}),
        false_values: frozenset[Any] | set[Any] = frozenset({"no", "n", "false", "0"}),
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        if not isinstance(true_values, (set, frozenset)):
            raise CleanConfigurationError(
                f"true_values must be a set or frozenset: {true_values}"
            )
        if not isinstance(false_values, (set, frozenset)):
            raise CleanConfigurationError(
                f"false_values must be a set or frozenset: {false_values}"
            )

        if len(true_values) == 0 and len(true_values) == 0:
            raise CleanConfigurationError(
                "true_values and/or false_values must be non-empty"
            )

        sanitised_true = frozenset(sanitise_scalar_string(val) for val in true_values)
        sanitised_false = frozenset(sanitise_scalar_string(val) for val in false_values)

        if any(value in sanitised_false for value in sanitised_true):
            raise CleanConfigurationError(
                f"true_values and false_values must be disjoint sets: {sanitised_true} and {sanitised_false}"
            )

        super().__init__(
            data_type="boolean", col_sensitivity=col_sensitivity, alias=alias
        )
        self._params = self._create_extended_params(
            _BooleanParams,
            true_values=true_values,
            false_values=false_values,
            bool_map={
                **{val: True for val in sanitised_true},
                **{val: False for val in sanitised_false},
            },
        )

    def clean_expr(self, source_column: str, alias: str) -> Expr:
        return (
            full_sanitise_string_col(source_column)
            .replace(self._params.bool_map, default=None, return_dtype=Boolean)
            .alias(alias)
        )
