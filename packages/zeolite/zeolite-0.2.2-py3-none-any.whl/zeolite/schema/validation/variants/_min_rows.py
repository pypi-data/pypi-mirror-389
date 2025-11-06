from typing import TYPE_CHECKING, Optional
from polars import len as pl_len

from .._base import BaseTableCheck
from ....exceptions import InvalidThresholdError
from ....types.validation.threshold import ThresholdLevel

if TYPE_CHECKING:
    from polars import LazyFrame
    from ....types.error import TableValidationError


class TableCheckMinRows(BaseTableCheck):
    """
    Check if output has minimum required number of rows.

    Only supports absolute count-based thresholds (>1), not fractions.

    Examples:
        # Reject if output has fewer than 10 rows
        z.TableCheck.min_output_rows(reject=10)

        # Multiple levels
        z.TableCheck.min_output_rows(warning=100, error=50, reject=10)
    """

    def __init__(
        self,
        *,
        message: str = "",
        debug: Optional[int] = None,
        warning: Optional[int] = None,
        error: Optional[int] = None,
        reject: Optional[int] = None,
    ):
        # Validate and convert threshold values
        # For min_output_rows, we only support count-based thresholds
        converted_thresholds = {}

        for key, val in [
            ("debug", debug),
            ("warning", warning),
            ("error", error),
            ("reject", reject),
        ]:
            if val is not None:
                # Check if it's a fraction (0-1) which we don't support
                if isinstance(val, float) and 0 < val <= 1:
                    raise InvalidThresholdError(
                        f"min_output_rows does not support fraction thresholds. "
                        f"Use integer counts only. Got {key}={val}"
                    )
                # Also reject special keywords that don't make sense
                if isinstance(val, str) and val in ["any", "all"]:
                    raise InvalidThresholdError(
                        f"min_output_rows does not support '{val}'. "
                        f"Use integer counts only."
                    )

                # Convert 1 to "any" since Threshold doesn't allow 1
                # For min_output_rows(reject=1), this means "at least 1 row"
                if val == 1:
                    converted_thresholds[key] = "any"
                else:
                    converted_thresholds[key] = val

        super().__init__(message=message, **converted_thresholds)

    @classmethod
    def method_id(cls) -> str:
        return "min_rows"

    def validate(
        self,
        validated_lf: "LazyFrame",
        filtered_lf: "LazyFrame",
        *,
        schema_name: str,
        source: str | None = None,
    ) -> "TableValidationError | None":
        """Evaluate if output has minimum required rows"""
        from ....types.error import TableValidationError

        total_rows = filtered_lf.select(pl_len()).collect().item()

        # Manually check each threshold level in priority order
        for level in sorted(ThresholdLevel, key=lambda x: x.priority, reverse=True):
            if level == ThresholdLevel.PASS:
                continue

            # Access the internal _thresholds dict to get count values
            fraction, count = self._params.thresholds._thresholds.get(
                level, (None, None)
            )

            # We should only have count-based thresholds (validated in __init__)
            if fraction is not None and fraction != 0:
                raise InvalidThresholdError(
                    "min_output_rows does not support fraction thresholds. "
                    "This should have been caught during initialization."
                )

            # Check if remaining rows fall below the required count
            if count is not None and total_rows < count:
                shortage = count - total_rows

                # Format message
                if self._params.message:
                    message = self._params.message
                else:
                    message = (
                        f"Table has {total_rows:,} rows, requires at least {count:,}"
                    )

                return TableValidationError(
                    schema=schema_name,
                    source=source,
                    error=self.method_id(),
                    level=level.level,
                    count_failed=shortage,
                    fraction_failed=None,
                    message=message,
                )

        return None
