from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Literal

from .validation.threshold import CheckLevel


@dataclass(frozen=True)
class SchemaValidationError:
    schema: str

    error: str
    level: CheckLevel
    message: str
    column: str | None = None
    fraction_failed: str | None = None
    count_failed: str | None = None
    category: Literal["file", "schema", "logic"] = field(init=False, default="unknown")

    # Meta fields
    source: str | None = None
    batch: datetime | None = None
    period: str | None = None
    year: str | None = None

    def with_meta(
        self,
        *,
        source: str | None = None,
        period: str | None = None,
        year: str | None = None,
        batch: datetime | None = None,
    ) -> "SchemaValidationError":
        return replace(
            self,
            **{
                "source": source or self.source,
                "batch": batch or self.batch,
                "period": period or self.period,
                "year": year or self.year,
            },
        )


@dataclass(frozen=True)
class UnknownValidationError(SchemaValidationError):
    category = "unknown"
    level: CheckLevel
    column: None = field(init=False, default=None)


@dataclass(frozen=True)
class FileValidationError(SchemaValidationError):
    category = "file"
    level: CheckLevel
    column: None = field(init=False, default=None)


@dataclass(frozen=True)
class StructureValidationError(SchemaValidationError):
    category = "schema_structure"
    level: CheckLevel
    column: str | None = None


@dataclass(frozen=True)
class DataValidationError(SchemaValidationError):
    category = "row_data"
    level: CheckLevel
    column: str


@dataclass(frozen=True)
class TableValidationError(SchemaValidationError):
    category = "table_data"
    level: CheckLevel
    column: None = field(init=False, default=None)
