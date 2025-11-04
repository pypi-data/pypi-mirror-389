# ---------------------------------------------------------------------------------
# Schema Construction Exceptions (raised during schema building, not data processing)
# ---------------------------------------------------------------------------------
class ZeoliteError(Exception):
    """Base exception for all Zeolite errors."""

    pass


class SchemaConfigurationError(ZeoliteError):
    """
    Raised when schema definition is invalid during construction.

    This is raised during schema construction (before .apply()), not during
    data processing.
    """

    def __init__(
        self,
        message: str,
        *,
        schema_name: str | None = None,
        column_name: str | None = None,
    ):
        self.schema_name = schema_name
        self.column_name = column_name
        super().__init__(message)


class MissingParentColumnError(SchemaConfigurationError):
    """
    Raised when a column references parent columns that don't exist in the schema.

    Example:
        A derived column references 'price' but no 'price' column is defined.
    """

    def __init__(
        self,
        message: str,
        *,
        column_name: str,
        missing_parents: set[str],
        schema_name: str | None = None,
    ):
        self.missing_parents = missing_parents
        super().__init__(message, schema_name=schema_name, column_name=column_name)


class DuplicateColumnError(SchemaConfigurationError):
    """
    Raised when duplicate column names or aliases are detected.

    Example:
        Two columns both named 'id', or two columns with aliases that
        sanitize to the same value.
    """

    def __init__(
        self,
        message: str,
        *,
        column_name: str,
        duplicate_of: str | None = None,
        schema_name: str | None = None,
    ):
        self.duplicate_of = duplicate_of
        super().__init__(message, schema_name=schema_name, column_name=column_name)


class CircularDependencyError(SchemaConfigurationError):
    """
    Raised when circular dependencies are detected in column definitions.

    Example:
        col_1 depends on col_2, which depends on col_1 (A -> B -> A)
        col_1 -> col_2 -> col_3 -> col_1 (A -> B -> C -> A)
    """

    def __init__(
        self,
        message: str,
        *,
        cycle: list[str],
        schema_name: str | None = None,
    ):
        self.cycle = cycle
        super().__init__(message, schema_name=schema_name)


class RegistryIntegrityError(SchemaConfigurationError):
    """
    Raised when column registry validation fails.

    This indicates internal inconsistencies in the registry such as
    invalid parent IDs or incorrect mappings.
    """

    pass


class TableCheckConfigurationError(SchemaConfigurationError):
    """
    Raised when validation check is invalid during construction.

    This is raised during column/schema construction, not during
    data processing.
    """

    pass


class ColumnConfigurationError(ZeoliteError):
    """
    Raised when column definition is invalid during construction.

    This is raised during column/schema construction, not during
    data processing.
    """

    def __init__(
        self,
        message: str,
        *,
        column_name: str | None = None,
    ):
        self.column_name = column_name
        super().__init__(message)


class CleanConfigurationError(ColumnConfigurationError):
    """
    Raised when column cleaning definition is invalid during construction.

    This is raised during column/schema construction, not during
    data processing.
    """

    def __init__(
        self,
        message: str,
        *,
        column_name: str | None = None,
    ):
        super().__init__(message, column_name=column_name)


class CheckConfigurationError(ColumnConfigurationError):
    """
    Raised when column validation check is invalid during construction.

    This is raised during column/schema construction, not during
    data processing.
    """

    def __init__(
        self,
        message: str,
        *,
        column_name: str | None = None,
    ):
        super().__init__(message, column_name=column_name)


class InvalidThresholdError(CheckConfigurationError):
    """
    Raised when threshold configuration is invalid.

    Example:
        Negative threshold values, min > max, or invalid threshold types.
    """

    pass
