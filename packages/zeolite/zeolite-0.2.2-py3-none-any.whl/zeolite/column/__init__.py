from __future__ import annotations

from typing import List

from polars import Expr

from ..ref import ColumnRef
from ..types import CoerceOption
from ..types.data_type import ColumnDataType
from ..types.sensitivity import Sensitivity
from ._base import Col
from ._clean import CleanStage, Clean
from .validation import ColumnCheckType, ThresholdType

__all__ = [
    "col",
    "column",
    "Col",
    "str_col",
    "bool_col",
    "date_col",
    "int_col",
    "float_col",
    "derived_col",
    "derived_custom_check",
    "meta_col",
    "Clean",
]


# -----------------------------------------------------------------------------------------------------------
# Column Definitions
# -----------------------------------------------------------------------------------------------------------


class ColFactory:
    data_type: ColumnDataType

    def __init__(self, data_type: ColumnDataType = "unknown"):
        self.data_type = data_type

    def __call__(
        self,
        name: str | None = None,
        *,
        data_type: ColumnDataType | None = None,
        sensitivity: Sensitivity = None,
        variants: set[str] = None,
        coerce: CoerceOption = "default",
        validations: List[ColumnCheckType] = None,
        clean: CleanStage | None = None,
    ) -> Col:
        """
        Define a new column.

        Parameters:
            name: Name of the column.
            data_type: Data type of the column.
            sensitivity: Sensitivity of the column.
            variants: variants for the column.
            validations: List of validation checks.
            clean: Clean stage for the column.

        Returns:
            Col: The column schema.
        """
        return Col(
            col_ref=ColumnRef(name),
            data_type=data_type or self.data_type,
            coerce=coerce,
            sensitivity=sensitivity,
            variants=variants,
            validations=validations,
            clean=clean,
        )

    def str(
        self,
        name: str | None = None,
        *,
        sensitivity: Sensitivity = None,
        variants: set[str] = None,
        coerce: CoerceOption = "default",
        validations: List[ColumnCheckType] = None,
        clean: CleanStage | None = None,
    ) -> Col:
        return Col(
            col_ref=ColumnRef(name),
            data_type="string",
            coerce=coerce,
            sensitivity=sensitivity,
            variants=variants,
            validations=validations,
            clean=clean,
        )

    def bool(
        self,
        name: str | None = None,
        *,
        sensitivity: Sensitivity = None,
        variants: set[str] = None,
        coerce: CoerceOption = "default",
        validations: List[ColumnCheckType] = None,
        clean: CleanStage | None = None,
    ) -> Col:
        return Col(
            col_ref=ColumnRef(name),
            data_type="boolean",
            coerce=coerce,
            sensitivity=sensitivity,
            variants=variants,
            validations=validations,
            clean=clean,
        )

    def date(
        self,
        name: str | None = None,
        *,
        sensitivity: Sensitivity = None,
        variants: set[str] = None,
        coerce: CoerceOption = "default",
        validations: List[ColumnCheckType] = None,
        clean: CleanStage | None = None,
    ) -> Col:
        return Col(
            col_ref=ColumnRef(name),
            data_type="date",
            coerce=coerce,
            sensitivity=sensitivity,
            variants=variants,
            validations=validations,
            clean=clean,
        )

    def int(
        self,
        name: str | None = None,
        *,
        sensitivity: Sensitivity = None,
        variants: set[str] = None,
        coerce: CoerceOption = "default",
        validations: List[ColumnCheckType] = None,
        clean: CleanStage | None = None,
    ) -> Col:
        return Col(
            col_ref=ColumnRef(name),
            data_type="integer",
            coerce=coerce,
            sensitivity=sensitivity,
            variants=variants,
            validations=validations,
            clean=clean,
        )

    def float(
        self,
        name: str | None = None,
        *,
        sensitivity: Sensitivity = None,
        variants: set[str] = None,
        coerce: CoerceOption = "default",
        validations: List[ColumnCheckType] = None,
        clean: CleanStage | None = None,
    ) -> Col:
        return Col(
            col_ref=ColumnRef(name),
            data_type="float",
            coerce=coerce,
            sensitivity=sensitivity,
            variants=variants,
            validations=validations,
            clean=clean,
        )

    def derived(
        self,
        name: str | None = None,
        *,
        function: Expr,
        data_type: ColumnDataType = "unknown",
        sensitivity: Sensitivity = None,
        validations: List[ColumnCheckType] = None,
    ) -> Col:
        """
        Define a derived column whose value is computed from an expression.

        Parameters:
            name: Name of the derived column.
            function: Polars expression to compute the column.
            data_type: (Optional) Data type of the column.
            sensitivity: (Optional) Sensitivity of the column.
            validations: (Optional) List of validation checks.

        Returns:
            Col: The derived column schema.
        """
        return Col(
            col_ref=ColumnRef(name).derived(),
            data_type=data_type,
            sensitivity=sensitivity,
            validations=validations,
        ).derived(function)

    def custom_check(
        self,
        name: str | None = None,
        *,
        function: Expr,
        sensitivity: Sensitivity = Sensitivity.NON_SENSITIVE,
        thresholds: ThresholdType = None,
        message: str = "",
    ) -> Col:
        """
        Define a derived custom check/validation that is computed from an expression.

        Parameters:
            name: Name of the derived validation.
            function: Polars expression to compute the validation.
            sensitivity: (Optional) Sensitivity of the validation.
            thresholds: (Optional) Thresholds for the validation.
            message: (Optional) Message for the validation.

        Returns:
            Col: The derived validation schema.
        """
        return Col(
            col_ref=ColumnRef(name).custom_check(),
            data_type="boolean",
            sensitivity=sensitivity,
        ).custom_check(function, thresholds, message)

    def meta(
        self,
        name: str | None = None,
        *,
        function: Expr = None,
        data_type: ColumnDataType = "unknown",
        sensitivity: Sensitivity = None,
    ) -> Col:
        """
        Define a meta column - this is a special column that is usually added
        to the data e.g. during initial ingestion, and should be identified as
        separate from the source data.

        Parameters:
            name: Name of the meta column.
            function: (Optional) Polars expression to compute the column.
            data_type: (Optional) Data type of the column.
            sensitivity: (Optional) Sensitivity of the column.

        Returns:
            Col: The meta column schema.
        """
        m_col = Col(
            col_ref=ColumnRef(name, is_meta=True),
            data_type=data_type,
            sensitivity=sensitivity,
        )
        return m_col.derived(function) if function is not None else m_col

    def temp(
        self,
        name: str | None = None,
        *,
        variants: set[str] = None,
        data_type: ColumnDataType | None = None,
        coerce: CoerceOption = "default",
        validations: List[ColumnCheckType] = None,
        clean: CleanStage | None = None,
    ) -> Col:
        """
        Define a temporary column. This column is treated exactly like other columns, except it is removed
        from the final dataset during the refinement stage.
        Temporary columns can be required in normalisation phase, and have Cleans, Checks, and derived columns based
        on them. Note that unlike other columns any Clean outputs will also be removed during refinement, unless
        the Clean definition is given a separate alias

        Parameters:
            name: Name of the temp column.
            data_type: (Optional) Data type of the column.
            variants: (Optional) variants for the column.
            validations: (Optional) List of validation checks.
            clean: (Optional) Clean stage for the column.
            coerce: (Optional) Whether data type should be coerced on column.

        Returns:
            Col: The meta column schema.
        """
        return Col(
            col_ref=ColumnRef(name),
            data_type=data_type,
            coerce=coerce,
            variants=variants,
            validations=validations,
            clean=clean,
            temporary=True,
        )


column: ColFactory = ColFactory()
col: ColFactory = ColFactory()
"""
Define a new column.
Example:
    zeolite.col("id").validations(zeolite.check_is_value_empty(), ...)

Parameters:
    name: Name of the column.
    data_type: Data type of the column.
    sensitivity: Sensitivity of the column.
    variants: Variants for the column.
    validations: List of validation checks.
    clean: Clean stage for the column.

Returns:
    ColumnSchema: The column schema.
"""

# -----------------------------------------------------------------------------------------------------------
# Data-Type Specific Column Definitions (backward compatibility aliases)
# -----------------------------------------------------------------------------------------------------------

str_col = col.str
"""
Helper to define a new string column.
Alias for col.str() - prefer using col.str() directly.
"""

bool_col = col.bool
"""
Helper to define a new boolean column.
Alias for col.bool() - prefer using col.bool() directly.
"""

date_col = col.date
"""
Helper to define a new date column.
Alias for col.date() - prefer using col.date() directly.
"""

int_col = col.int
"""
Helper to define a new integer column.
Alias for col.int() - prefer using col.int() directly.
"""

float_col = col.float
"""
Helper to define a new float column.
Alias for col.float() - prefer using col.float() directly.
"""

# -----------------------------------------------------------------------------------------------------------
# Derived Column Definitions (backward compatibility alias)
# -----------------------------------------------------------------------------------------------------------

derived_col = col.derived
"""
Define a derived column whose value is computed from an expression.
Alias for col.derived() - prefer using col.derived() directly.

Parameters:
    name: Name of the derived column.
    function: Polars expression to compute the column.
    data_type: (Optional) Data type of the column.
    sensitivity: (Optional) Sensitivity of the column.
    validations: (Optional) List of validation checks.

Returns:
    ColumnSchema: The derived column schema.
"""

# -----------------------------------------------------------------------------------------------------------
# Custom Check Column Definitions (backward compatibility alias)
# -----------------------------------------------------------------------------------------------------------

derived_custom_check = col.custom_check
"""
Define a derived custom check/validation that is computed from an expression.
Alias for col.custom_check() - prefer using col.custom_check() directly.

Parameters:
   name: Name of the derived validation.
   function: Polars expression to compute the validation.
   sensitivity: (Optional) Sensitivity of the validation.
   thresholds: (Optional) Thresholds for the validation.
   message: (Optional) Message for the validation.

Returns:
   ColumnSchema: The derived validation schema.
"""

# -----------------------------------------------------------------------------------------------------------
# Meta Column Definitions (backward compatibility alias)
# -----------------------------------------------------------------------------------------------------------

meta_col = col.meta
"""
Define a meta column - this is a special column that is usually added
to the data e.g. during initial ingestion, and should be identified as
separate from the source data.
Alias for col.meta() - prefer using col.meta() directly.

Parameters:
    name: Name of the meta column.
    function: (Optional) Polars expression to compute the column.
    data_type: (Optional) Data type of the column.
    sensitivity: (Optional) Sensitivity of the column.

Returns:
    ColumnSchema: The meta column schema.
"""
