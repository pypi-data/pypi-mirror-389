from dataclasses import KW_ONLY, dataclass
from polars import LazyFrame, DataFrame, col, len as pl_len

from .threshold import Threshold, ThresholdLevel
from ..error import DataValidationError


@dataclass(frozen=True)
class ColumnValidationRule:
    check_id: str
    _: KW_ONLY
    thresholds: Threshold
    message: str
    source_column: str
    check_column: str
    schema: str
    remove_row_on_fail: bool

    def validate(
        self, lf: LazyFrame | DataFrame, source: str | None = None
    ) -> DataValidationError | None:
        checks = (
            lf.lazy()
            .select(
                pl_len().alias("total_rows"),
                col(self.check_column)
                .ne(ThresholdLevel.PASS.level)
                .sum()
                .alias("failed_rows"),
            )
            .collect()
        )

        total_rows = checks["total_rows"].item()
        failed_rows = checks["failed_rows"].item()

        if failed_rows == 0:
            return None

        res = self.thresholds.resolve(failed_rows=failed_rows, total_rows=total_rows)

        return (
            DataValidationError(
                schema=self.schema,
                source=source,
                column=self.check_column,
                error=self.check_id,
                level=res.level,
                fraction_failed=res.fraction_failed,
                count_failed=res.count_failed,
                message=self._format_message(
                    self.source_column, failed_rows, total_rows
                ),
            )
            if res.level != "pass"
            else None
        )

    def _format_message(
        self,
        col: str,
        count: int,
        total: int,
        value: str | int | float | bool | None = None,
    ) -> str:
        return (
            self.message.replace("{{column}}", f"`{col}`")
            .replace("{{count}}", f"{count:,}")
            .replace("{{fraction}}", f"{count / total:,.2%}")
        )
