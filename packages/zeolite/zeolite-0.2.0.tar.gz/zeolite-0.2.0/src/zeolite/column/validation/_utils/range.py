from typing import Literal

from .types import RangeBounds

type _PolarsRange = Literal["both", "left", "right", "none"]


def get_range_bounds(bound: RangeBounds) -> _PolarsRange:
    if not bound or bound == "exclusive":
        return "none"
    elif bound == "min":
        return "left"
    elif bound == "max":
        return "right"
    # if bound == True or bound == "both" or bound == "inclusive" or bound is None:
    return "both"
