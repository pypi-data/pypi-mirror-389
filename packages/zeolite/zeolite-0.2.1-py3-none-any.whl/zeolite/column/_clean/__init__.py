from dataclasses import dataclass

from ._base import CleanColumn
from ._boolean import CleanBooleanColumn
from ._date import (
    CleanDateColumn,
    CleanDatetimeColumn,
    CleanTimeColumn,
    CleanDurationColumn,
)
from ._enum import CleanEnumColumn
from ._id import CleanIdColumn
from ._number import CleanNumberColumn, CleanIntegerColumn, CleanDecimalColumn
from ._string import CleanStringColumn, CleanSanitisedStringColumn
from ._custom import CustomCleanColumn


@dataclass(frozen=True)
class Clean:
    string = CleanStringColumn
    sanitised_string = CleanSanitisedStringColumn
    number = CleanNumberColumn
    float = CleanNumberColumn
    int = CleanIntegerColumn
    integer = CleanIntegerColumn
    decimal = CleanDecimalColumn
    boolean = CleanBooleanColumn
    date = CleanDateColumn
    datetime = CleanDatetimeColumn
    time = CleanTimeColumn
    duration = CleanDurationColumn
    id = CleanIdColumn
    enum = CleanEnumColumn
    custom = CustomCleanColumn


type CleanStage = (
    CleanColumn
    | CleanStringColumn
    | CleanNumberColumn
    | CleanDecimalColumn
    | CleanIntegerColumn
    | CleanBooleanColumn
    | CleanDateColumn
    | CleanDatetimeColumn
    | CleanTimeColumn
    | CleanDurationColumn
    | CleanEnumColumn
    | CleanIdColumn
    | CustomCleanColumn
)
__all__ = [
    "Clean",
    "CleanStage",
    "CleanColumn",
    "CustomCleanColumn",
]
