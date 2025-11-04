from typing import Optional

from ._reference import ColumnRef, parse_column_name

__all__ = [
    "ref",
    "ref_meta",
    "ref_derived",
    "ref_custom_check",
    "ColumnRef",
    "parse_column_name",
]


# -----------------------------------------------------------------------------------------------------------
# Column References
# -----------------------------------------------------------------------------------------------------------


class Ref:
    def __call__(
        self,
        name: str,
        *,
        schema: Optional[str] = None,
        stage: Optional[str] = None,
        is_clean: bool = False,
        is_derived: bool = False,
        is_check: bool = False,
        is_meta: bool = False,
        is_custom_check: bool = False,
        check_name: str | None = None,
    ) -> ColumnRef:
        """
        Create a column reference for use in schema definitions.

        Parameters:
            name: Name of the column.

            is_clean: Whether the column is cleaned.
            is_derived: Whether the column is derived (calculated from other columns).
            is_check: Whether the column is a check/validation.
            is_meta: Whether the column is a meta column.
            is_custom_check: Whether the column is a custom check derived from an expression.
            check_name: Name of the check/validation.
            schema: Table schema name.
            stage: Pipeline stage name.

        Returns:
            ColumnRef: The column reference.
        """
        parsed = parse_column_name(name)

        return ColumnRef(
            base_name=parsed.base_name,
            schema=schema,
            stage=stage,
            is_clean=is_clean or parsed.is_clean,
            is_derived=is_derived or parsed.is_derived,
            is_check=is_check or parsed.is_check,
            is_meta=is_meta or parsed.is_meta,
            is_custom_check=is_custom_check or parsed.is_custom_check,
            check_name=check_name or parsed.check_name,
        )

    def __getattr__(self, name: str) -> ColumnRef:
        # For autocomplete to work with IPython
        if name.startswith("__wrapped__"):
            return getattr(type(self), name)

        return parse_column_name(name)


ref: Ref = Ref()
"""
   Create a column reference for use in schema definitions.
   
   Example:
    zeolite.ref("other_column")

   Parameters:
       name: Name of the column.

       is_clean: Whether the column is cleaned.
       is_derived: Whether the column is derived (calculated from other columns).
       is_check: Whether the column is a check/validation.
       is_meta: Whether the column is a meta column.
       is_custom_check: Whether the column is a custom check derived from an expression.
       check_name: Name of the check/validation.
       schema: Table schema name.
       stage: Pipeline stage name.

   Returns:
       ColumnRef: The column reference.
   """


# -----------------------------------------------------------------------------------------------------------
# Column Reference Shortcuts
# -----------------------------------------------------------------------------------------------------------
def ref_meta(name: str) -> ColumnRef:
    """
    Create a column reference for a meta column.

    Example:
    zeolite.ref_meta("other_column")

    Parameters:
        name: Name of the column.

    Returns:
        ColumnRef: The column reference.
    """
    return ref(name=name, is_meta=True)


def ref_derived(name: str) -> ColumnRef:
    """
    Create a column reference to a derived column whose
    value is computed from an expression.

    Example:
    zeolite.ref_derived("other_column")

    Parameters:
        name: Name of the column.

    Returns:
        ColumnRef: The column reference.
    """
    return ref(name=name, is_derived=True)


def ref_custom_check(name: str) -> ColumnRef:
    """
    Create a column reference to derived custom check/validation
    (that is computed from an expression).

    Example:
    zeolite.ref_custom_check("other_column")

    Parameters:
        name: Name of the column.

    Returns:
        ColumnRef: The column reference.
    """
    return ref(name=name, is_custom_check=True, is_derived=True)
