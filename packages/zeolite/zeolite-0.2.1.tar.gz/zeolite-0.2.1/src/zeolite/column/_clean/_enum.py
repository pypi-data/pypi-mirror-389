from dataclasses import dataclass

from typing import Any
from polars import Expr, Enum

from ._string import CleanStringColumn, _StringParams
from ...types.data_type import NO_DATA, INVALID_DATA
from ..._utils.sanitise import sanitise_scalar_string, SanitiseLevelType, SanitiseLevel
from ...types.sensitivity import Sensitivity
from ...exceptions import CleanConfigurationError


# %%-----------------------------------------------------------------
# Enum Cleans
# ------------------------------------------------------------------
@dataclass(frozen=True, kw_only=True)
class _EnumParams(_StringParams):
    enum_map: dict[str, Any]
    invalid_value: str | None
    null_value: str | None


class CleanEnumColumn(CleanStringColumn):
    _required_args = {"enum_map"}

    def __init__(
        self,
        *,
        enum_map: dict[str, Any],
        invalid_value: str | None = INVALID_DATA,
        null_value: str | None = NO_DATA,
        sanitise: SanitiseLevelType | None = None,
        sanitise_join_char: str = "_",
        col_sensitivity: Sensitivity | None = None,
        alias: str | None = None,
    ):
        if not isinstance(enum_map, dict):
            raise CleanConfigurationError(f"enum_map must be a dictionary: {enum_map}")

        super().__init__(
            data_type="enum",
            col_sensitivity=col_sensitivity,
            sanitise=sanitise,
            sanitise_join_char=sanitise_join_char,
            alias=alias,
        )
        self._params = self._create_extended_params(
            _EnumParams,
            sanitise=sanitise,
            sanitise_join_char=sanitise_join_char,
            invalid_value=invalid_value,
            null_value=null_value,
            enum_map=_clean_enum_keys(
                enum_map,
                sanitise=sanitise,
                sanitise_join_char=sanitise_join_char,
            ),
        )

    def clean_expr(self, source_column: str, alias: str) -> Expr:
        unique_values = set(self._params.enum_map.values())
        enum_mapping = self._params.enum_map

        if self._params.invalid_value is not None:
            unique_values.add(self._params.invalid_value)
        if self._params.null_value is not None:
            unique_values.add(self._params.null_value)
            enum_mapping = {**enum_mapping, None: self._params.null_value}

        return (
            self._sanitise(source_column)
            .replace(
                enum_mapping,
                default=self._params.invalid_value,
                return_dtype=Enum(list(unique_values)),
            )
            .alias(alias)
        )


# ---------------------------------------------------------------------------------------------------


def _sanitise_and_validate_keys(
    enum_map: dict[str, Any], sanitise_fn: callable
) -> dict[str, str]:
    sanitised_map = {}
    for k, v in enum_map.items():
        sanitised_key = sanitise_fn(k)
        if sanitised_key in sanitised_map and sanitised_map[sanitised_key] != v:
            raise CleanConfigurationError(
                f"Duplicate sanitised keys found: '{k}' and '{list(enum_map.keys())[list(sanitised_map.keys()).index(sanitised_key)]}' both sanitise to '{sanitised_key}' but have different values: '{v}' and '{sanitised_map[sanitised_key]}'"
            )
        sanitised_map[sanitised_key] = v
    return sanitised_map


def _clean_enum_keys(
    enum_map: dict[str, Any], *, sanitise: SanitiseLevelType, sanitise_join_char: str
) -> dict[str, str]:
    if sanitise == SanitiseLevel.FULL:
        return _sanitise_and_validate_keys(
            enum_map, lambda k: sanitise_scalar_string(k, join_char=sanitise_join_char)
        )
    elif sanitise == SanitiseLevel.LOWERCASE:
        return _sanitise_and_validate_keys(enum_map, lambda k: k.lower().strip())
    elif sanitise == SanitiseLevel.TRIM:
        return _sanitise_and_validate_keys(enum_map, lambda k: k.strip())
    else:
        return enum_map
