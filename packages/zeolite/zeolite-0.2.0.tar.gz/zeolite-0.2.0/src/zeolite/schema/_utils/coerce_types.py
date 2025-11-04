# %%
from dataclasses import dataclass
from typing import List, Optional, Literal
from polars import col as pl_col, DataFrame, LazyFrame, InvalidOperationError, DataType
from ...types import (
    SourceColDef,
    ThresholdLevel,
    ValidationResult,
    StructureValidationError,
)


# %%

type CoerceOverride = Literal[
    "force",
    "force_strict",
    "force_skip_all",
    "default_true",
    "default_strict",
    "default_skip",
]


@dataclass
class Coerce:
    name: str
    dtype: DataType
    should_coerce: bool = False
    strict: bool = False


def _get_coerce_options(
    col_def: SourceColDef, dtype: DataType, coerce_override: Optional[CoerceOverride]
):
    override = coerce_override if coerce_override else "default_skip"

    if override == "force_skip_all" or dtype is None or dtype.is_(col_def.dtype):
        return Coerce(name=col_def.name, dtype=dtype, should_coerce=False)
    elif override.startswith("force_"):
        return Coerce(
            name=col_def.name,
            dtype=col_def.dtype,
            should_coerce=True,
            strict=override == "force_strict",
        )
    # The 'force' option overrides the specific column option
    elif col_def.coerce == "skip":
        return Coerce(name=col_def.name, dtype=col_def.dtype, should_coerce=False)

    specific_coerce = col_def.coerce == "strict" or col_def.coerce == "coerce"
    default_coerce = override != "default_skip"

    return Coerce(
        name=col_def.name,
        dtype=col_def.dtype,
        should_coerce=specific_coerce or default_coerce,
        strict=col_def.coerce == "strict" or override == "default_strict",
    )


def coerce_column_types(
    df: DataFrame | LazyFrame,
    *,
    col_defs: List[SourceColDef],
    schema_name: str,
    source_name: str | None,
    coerce_override: Optional[CoerceOverride],
):
    # I
    if coerce_override == "force_skip_all":
        return ValidationResult(data=df.lazy(), errors=[])
    lf = df.lazy()
    coercion_map = {col.name: col for col in col_defs if col.dtype is not None}
    lf_schema = lf.collect_schema()

    errors = []
    mismatches: list[Coerce] = []
    reject = False
    for name, dtype in lf_schema.items():
        expected = coercion_map.get(name, None)
        if expected is None:
            continue

        coerce = _get_coerce_options(expected, dtype, coerce_override)

        if not coerce.should_coerce:
            continue
        else:
            mismatches.append(coerce)
            errors.append(
                StructureValidationError(
                    schema=schema_name,
                    source=source_name,
                    column=name,
                    error="data_type_mismatch",
                    level=ThresholdLevel.WARNING.level,
                    message=f"Column `{name}` type `{dtype}` doesn't match expected type `{expected.dtype}`",
                )
            )
            if coerce.strict:
                try:
                    # TODO: see if there's a more efficient way to test coercion
                    lf.select(
                        pl_col(coerce.name).cast(coerce.dtype, strict=coerce.strict)
                    ).collect()
                except InvalidOperationError as e:
                    reject = True
                    errors.append(
                        StructureValidationError(
                            schema=schema_name,
                            source=source_name,
                            column=coerce.name,
                            error="failed_type_coercion",
                            level=ThresholdLevel.REJECT.level,
                            message=str(e),
                        )
                    )

    if len(mismatches) > 0:
        return ValidationResult(
            data=lf.with_columns(
                pl_col(c.name).cast(c.dtype, strict=c.strict) for c in mismatches
            ),
            errors=errors,
            reject=reject,
        )
    else:
        return ValidationResult(
            data=lf,
            errors=errors,
            reject=False,
        )
