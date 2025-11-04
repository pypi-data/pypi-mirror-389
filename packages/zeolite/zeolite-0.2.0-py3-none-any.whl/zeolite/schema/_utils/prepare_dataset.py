from polars import LazyFrame, DataFrame
from polars.exceptions import ColumnNotFoundError
from ...registry import ColumnRegistry
from ...types import ValidationResult, StructureValidationError, ThresholdLevel


def prepare_additional_columns(
    df: LazyFrame | DataFrame,
    *,
    registry: ColumnRegistry,
    schema_name: str,
    source_name: str | None,
) -> ValidationResult:
    """
     Add columns based on the registry definitions

    :param df: Polars LazyFrame or DataFrame
    :param registry: Zeolite ColumnRegistry
    :param schema_name: Name of the schema
    :param source_name: (Optional) Name of the source file (used for error messages)
    :return:
    """
    errors = []
    reject = False
    lf = df.lazy()

    try:
        for stage in registry.get_execution_stages():
            lf = lf.with_columns([c.expression for c in stage])

        # We collect the first row, to make sure the lazy frame is actually valid.
        # If it's invalid it will raise an error that we handle further down
        is_empty = lf.limit(1).collect().is_empty()
        if is_empty:
            errors.append(
                StructureValidationError(
                    schema=schema_name,
                    source=source_name,
                    error="empty_data",
                    level=ThresholdLevel.REJECT.level,
                    message=f"`{schema_name}` has no data after attempting to add columns.",
                )
            )
    except ColumnNotFoundError as e:
        errors.append(
            StructureValidationError(
                schema=schema_name,
                source=source_name,
                error="column_not_found",
                level=ThresholdLevel.REJECT.level,
                message=f"polars.exceptions.ColumnNotFoundError: {e}",
            )
        )

    except Exception as e:
        print(e)
        errors.append(
            StructureValidationError(
                schema=schema_name,
                source=source_name,
                error="unknown",
                level=ThresholdLevel.REJECT.level,
                message=f"{e}",
            )
        )

    for e in errors:
        if e.level == ThresholdLevel.REJECT.level:
            reject = True
            break

    return ValidationResult(data=lf, errors=errors, reject=reject)
