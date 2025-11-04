# %%
from polars import (
    String,
    Int64,
    Float64,
    Boolean,
    Date,
    Datetime,
    Categorical,
    Decimal,
    Duration,
    DataType,
)

from ..types import ColumnDataType


# %%
def get_polars_type(data_type: ColumnDataType):
    if isinstance(data_type, DataType):
        return data_type
    elif data_type in ("string", "id", "sanitised_string"):
        return String()
    elif data_type in ("number", "float"):
        return Float64()
    elif data_type == "integer":
        return Int64()
    elif data_type == "boolean":
        return Boolean()
    elif data_type == "date":
        return Date()
    elif data_type == "datetime":
        return Datetime()
    elif data_type == "duration":
        return Duration()
    elif data_type == "categorical":
        return Categorical()
    elif data_type == "decimal":
        print(
            "Decimal defaults to `.2f`, if you need to customise use a polars decimal `pl.Decimal`"
        )
        return Decimal(None, 2)
    elif data_type == "enum":
        raise TypeError(
            "enum must be defined as a polars enum e.g. `pl.Enum(['a', 'b', 'c'])`"
        )
    else:
        # raise ValueError(f"Unsupported data type: {data_type}")
        return None


def get_data_type_label(data_type: ColumnDataType):
    if isinstance(data_type, str):
        return data_type
    elif isinstance(data_type, DataType):
        return str(data_type).split("(")[0].lower()
    else:
        return "unknown"
