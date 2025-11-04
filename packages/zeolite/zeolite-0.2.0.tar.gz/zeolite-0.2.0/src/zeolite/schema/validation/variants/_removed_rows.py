from typing import TYPE_CHECKING, Optional

from polars import len as pl_len

from .._base import BaseTableCheck
from ..._table import VALIDATION_CHECK_COL
from ....types.validation.threshold import CheckThreshold

if TYPE_CHECKING:
    from polars import LazyFrame
    from ....types.error import TableValidationError


class TableCheckRemovedRows(BaseTableCheck):
    """
    Check if too many rows were removed during validation.

    Supports both fraction-based and count-based thresholds:
    - Fractions (0-1): Percentage of input rows that were removed
    - Counts (>1): Absolute number of rows removed

    Examples:
        # Reject if more than 40% of rows removed
        z.TableCheck.removed(reject=0.4)

        # Reject if more than 100 rows removed
        z.TableCheck.removed(reject=100)

        # Multiple levels
        z.TableCheck.removed(warning=0.2, error=0.3, reject=0.5)

        # Reject if ALL rows removed
        z.TableCheck.removed(reject="all")
    """

    row_check_col: Optional[str]

    def __init__(
        self,
        *,
        message: str = "",
        row_check_col: Optional[str] = VALIDATION_CHECK_COL,
        thresholds=None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
    ):
        self.row_check_col = row_check_col
        super().__init__(
            message,
            thresholds=thresholds,
            debug=debug,
            warning=warning,
            error=error,
            reject=reject,
        )

    @classmethod
    def method_id(cls) -> str:
        return "removed_rows"

    def validate(
        self,
        validated_lf: "LazyFrame",
        filtered_lf: "LazyFrame",
        *,
        schema_name: str,
        source: str | None = None,
    ) -> "TableValidationError | None":
        """Evaluate if too many rows were removed"""
        from ....types.error import TableValidationError

        total_rows = validated_lf.select(pl_len()).collect().item()
        filtered_row = filtered_lf.select(pl_len()).collect().item()
        removed_rows = total_rows - filtered_row

        if removed_rows == 0:
            return None

        # Use standard Threshold.resolve logic
        res = self._params.thresholds.resolve(
            failed_rows=removed_rows, total_rows=total_rows
        )

        if res.level == "pass":
            return None

        # Format message
        if self._params.message:
            message = self._params.message
        else:
            fraction = removed_rows / total_rows if total_rows > 0 else 1
            message = (
                f"{removed_rows:,} rows removed ({fraction:.1%} of input), "
                f"exceeds {res.level} threshold"
            )

        return TableValidationError(
            schema=schema_name,
            source=source,
            error=self.method_id(),
            level=res.level,
            fraction_failed=res.fraction_failed,
            count_failed=res.count_failed,
            message=message,
        )
