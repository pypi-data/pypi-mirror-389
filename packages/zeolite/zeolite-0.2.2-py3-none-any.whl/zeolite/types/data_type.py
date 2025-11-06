from typing import Literal
from polars import DataType

type ColumnDataTypeLabel = Literal[
    "string",
    "id",
    "number",
    "integer",
    "float",
    "decimal",
    "boolean",
    "date",
    "datetime",
    "duration",
    "time",
    "enum",
    "categorical",
    "sanitised_string",
    "unknown",
]

type ColumnDataType = ColumnDataTypeLabel | DataType

NO_DATA = "NO_DATA"
INVALID_DATA = "INVALID_DATA"
