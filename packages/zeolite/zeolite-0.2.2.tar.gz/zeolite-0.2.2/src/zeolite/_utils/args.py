from typing import Any, List, Tuple
from collections.abc import Iterable


def flatten_args(
    args: Iterable[Any | Iterable[Any]] | Tuple[Any | List[Any], ...],
) -> List[Any]:
    return [
        item
        for sublist in args
        for item in (sublist if isinstance(sublist, list) else [sublist])
    ]
