from ._base import BaseTableCheck
from .variants import TableCheckRemovedRows, TableCheckMinRows


class TableCheck:
    """
    Factory for creating table-level validation checks.

    Table checks validate aggregate properties of the output data,
    such as how many rows were removed or whether minimum row counts are met.

    Examples:
        # Reject if more than 40% of rows removed
        z.TableCheck.removed(reject=0.4)

        # Reject if output has fewer than 10 rows
        z.TableCheck.min_output_rows(reject=10)

        # Multiple checks
        schema.table_validation(
            z.TableCheck.removed(warning=0.2, error=0.3, reject=0.5),
            z.TableCheck.min_output_rows(reject=10)
        )
    """

    removed_rows = TableCheckRemovedRows
    min_rows = TableCheckMinRows


__all__ = ["BaseTableCheck", "TableCheckRemovedRows", "TableCheckMinRows", "TableCheck"]
