from ._removed_rows import TableCheckRemovedRows
from ._min_rows import TableCheckMinRows

type TableCheckType = TableCheckRemovedRows | TableCheckMinRows

__all__ = ["TableCheckRemovedRows", "TableCheckMinRows", "TableCheckType"]
