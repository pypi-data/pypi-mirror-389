from typing import List

import polars as pl

from ...types import SourceColDef, ThresholdLevel, ValidationResult
from ...types.error import StructureValidationError
from ..._utils.sanitise import sanitise_column_name


# _INTERNAL_COL_PATTERN = r'meta__.*'
# %%


def _rename_columns_from_variants(
    lf: pl.LazyFrame,
    *,
    col_defs: List[SourceColDef],
    schema_name: str,
    source_name: str | None,
) -> ValidationResult:
    """
     Rename columns in a LazyFrame based on a dictionary of variants.

    :param lf: Polars LazyFrame
    :param col_defs: Column definitions (from a TableSchema)
    :param schema_name: Name of the schema
    :param source_name: (Optional) Name of the source file (used for error messages)
    :return:
    """
    errors = []

    schema_variants = {a: c.name for c in col_defs for a in c.variants}

    original_columns = lf.collect_schema().names()
    original_columns_map = {(c, sanitise_column_name(c)) for c in original_columns}

    assigned_targets = set()
    rename_cols = {}

    for original_col, sanitised_original in original_columns_map:
        target = schema_variants.get(sanitised_original, None)

        # print(original_col, " -> ", sanitised_original, " -> ", target, " -> ", target not in assigned_targets)
        if target is None:
            continue

        # Only proceed if source & target aren't the same
        if target != original_col:
            # If the target is already assigned, or present in the original columns, then this is a duplicate
            if target in assigned_targets or (
                target in original_columns and target != original_col
            ):
                errors.append(
                    StructureValidationError(
                        schema=schema_name,
                        source=source_name,
                        # column=original_columns_map[sanitised_original],
                        column=original_col,
                        error="duplicate_column",
                        level=ThresholdLevel.REJECT.level,
                        message=f"Column `{original_col}` cannot be assigned, as another column already maps to `{target}`",
                    )
                )
            else:
                rename_cols[original_col] = target

        assigned_targets.add(target)

    for old_col, new_col in rename_cols.items():
        if old_col != new_col:
            errors.append(
                StructureValidationError(
                    schema=schema_name,
                    source=source_name,
                    column=old_col,
                    error="renamed_column",
                    level=ThresholdLevel.DEBUG.level,
                    message=f"Renamed `{old_col}` to `{new_col}`",
                )
            )

    return ValidationResult(data=lf.rename(rename_cols), errors=errors)


# %%


def _remove_null_rows(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.filter(~pl.all_horizontal(pl.all().is_null()))


# %%


def _check_critical_columns(
    data_cols: list[str],
    *,
    col_defs: List[SourceColDef],
    schema_name: str,
    source_name: str | None,
) -> list[StructureValidationError]:
    critical_cols = {
        c.name: c.if_missing for c in col_defs if c.if_missing == ThresholdLevel.REJECT
    }
    return [
        StructureValidationError(
            schema=schema_name,
            source=source_name,
            column=col_key,
            error="required_column",
            level=lvl.level,
            message=f"Column '{col_key}' is required but missing from the dataset",
        )
        for col_key, lvl in critical_cols.items()
        if col_key not in data_cols
    ]


def _check_non_critical_columns(
    data_cols: list[str],
    *,
    col_defs: List[SourceColDef],
    schema_name: str,
    source_name: str | None,
) -> list[StructureValidationError]:
    non_critical_cols = {
        c.name: c.if_missing
        for c in col_defs
        if c.if_missing != ThresholdLevel.REJECT and c.if_missing is not None
    }
    return [
        StructureValidationError(
            schema=schema_name,
            source=source_name,
            column=col_key,
            error="missing_column",
            level=lvl.level,
            message=f"Column '{col_key}' is missing from the data",
        )
        for col_key, lvl in non_critical_cols.items()
        if col_key not in data_cols
    ]


def _check_extra_columns(
    data_cols: list[str],
    *,
    col_defs: List[SourceColDef],
    schema_name: str,
    source_name: str | None,
) -> list[StructureValidationError]:
    all_cols = {c.name for c in col_defs}
    return [
        StructureValidationError(
            schema=schema_name,
            source=source_name,
            column=c,
            error="extra_column",
            level=ThresholdLevel.DEBUG.level,
            message=f"Column '{c}' is additional and not required",
        )
        for c in data_cols
        if c not in all_cols  # and not re.match(_INTERNAL_COL_PATTERN, c)
    ]


# %%


def _normalise_table_structure(
    lf: pl.LazyFrame,
    col_defs: List[SourceColDef],
    schema_name: str,
    source_name: str | None,
) -> ValidationResult:
    """
    Normalise the structure of a table based on the column definitions.

    :param lf: Polars LazyFrame
    :param schema_name: The name of the schema
    :param col_defs: List of Column Schema definitions
    :param source_name: (Optional) Name of the source file (used for error messages)
    :return:
    """
    errors: list[StructureValidationError] = []
    missing_cols: list[StructureValidationError] = []
    data_cols = lf.collect_schema().names()

    critical_errors = _check_critical_columns(
        data_cols, col_defs=col_defs, schema_name=schema_name, source_name=source_name
    )
    missing_cols.extend(critical_errors)

    non_critical = _check_non_critical_columns(
        data_cols, col_defs=col_defs, schema_name=schema_name, source_name=source_name
    )
    missing_cols.extend(non_critical)

    if len(missing_cols) > 0:
        lf = lf.with_columns(
            [pl.lit(None).cast(pl.String).alias(mc.column) for mc in missing_cols]
        )
        errors.extend(missing_cols)

    extra_cols = _check_extra_columns(
        data_cols, col_defs=col_defs, schema_name=schema_name, source_name=source_name
    )

    # if lf has extra columns, drop them
    if len(extra_cols) > 0:
        lf = lf.drop([c.column for c in extra_cols])
        errors.extend(extra_cols)

    is_empty = (
        lf.select([c.name for c in col_defs if not c.is_meta])
        .pipe(_remove_null_rows)
        .limit(1)
        .collect()
        .is_empty()
    )
    if is_empty:
        errors.append(
            StructureValidationError(
                schema=schema_name,
                source=source_name,
                error="empty_data",
                level=ThresholdLevel.REJECT.level,
                message=f"`{schema_name}` has no data after additional/unused columns have been removed",
            )
        )

    return ValidationResult(data=lf, errors=errors)


# %%
def normalise_column_headers(
    df: pl.LazyFrame | pl.DataFrame,
    col_defs: List[SourceColDef],
    schema_name: str,
    source_name: str | None,
) -> ValidationResult:
    """
    Normalise the column headers of a table to a common structure based on the column definitions.
    :param df: Polars LazyFrame or DataFrame
    :param col_defs: Column definitions (from a TableSchema)
    :param schema_name: Name of the schema
    :param source_name: (Optional) Name of the source file (used for error messages)
    :return:
    """
    errors = []
    reject = False
    lf = df.lazy()

    sanitised = _rename_columns_from_variants(
        lf, col_defs=col_defs, schema_name=schema_name, source_name=source_name
    )
    errors.extend(sanitised.errors)

    normalised = _normalise_table_structure(
        sanitised.data,
        col_defs=col_defs,
        schema_name=schema_name,
        source_name=source_name,
    )
    errors.extend(normalised.errors)

    for e in errors:
        if e.level == ThresholdLevel.REJECT.level:
            reject = True
            break

    return ValidationResult(data=normalised.data, errors=errors, reject=reject)
