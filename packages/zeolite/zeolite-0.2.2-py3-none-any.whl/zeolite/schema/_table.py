from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, List, Literal, Optional
from collections.abc import Iterable

from polars import LazyFrame, DataFrame, any_horizontal, col, lit

from ._utils.coerce_types import coerce_column_types, CoerceOverride
from ._utils.normalise import normalise_column_headers
from ._utils.prepare_dataset import prepare_additional_columns
from ..types import (
    ColumnNode,
    SourceColDef,
    ThresholdLevel,
    ValidationResult,
    ProcessingFailure,
    ProcessingSuccess,
    ProcessingStage,
)
from ..exceptions import DuplicateColumnError, SchemaConfigurationError
from .._utils.sanitise import sanitise_column_name
from ..column import Col
from ..registry import ColumnRegistry

if TYPE_CHECKING:
    from .validation.variants import TableCheckType
    from ..types.error import TableValidationError

VALIDATION_CHECK_COL = "validation__check__ROW_PASSED"


@dataclass(frozen=True, kw_only=True)
class _SchemaParams:
    name: str
    is_required: bool = False
    stage: Optional[str] = None
    source_columns: dict[str, SourceColDef] = field(default_factory=dict)
    refined_columns: dict[str, str] = field(default_factory=dict)
    registry: ColumnRegistry = field(default_factory=ColumnRegistry)
    strict: bool = True
    coerce: CoerceOverride = "default_true"
    table_checks: list["TableCheckType"] = field(default_factory=list)

    def __post_init__(self):
        self.registry.verify_integrity()


class TableSchema:
    """
    Defines a table schema for data validation and processing.

    Parameters:
        name (str): Name of the schema.
        columns (List[ColumnSchema] | dict[str, ColumnSchema], optional): List of column schemas.
        optional (bool): Whether the schema is optional or required.
        stage (str, optional): Processing stage.

    Usage:
        demo_schema = z.schema("demo", columns=[...])
    """

    def __init__(
        self,
        name: str,
        columns: Iterable[Col] | dict[str, Col] | None = None,
        *,
        optional: bool = False,
        stage: Optional[str] = None,
        strict: bool = True,
        coerce: CoerceOverride = "default_true",
        table_validations: Iterable["TableCheckType"] | None = None,
    ):
        cols = _parse_columns_into_list(columns)
        nodes = _cols_to_nodes(schema=name, stage=stage, columns=cols)
        registry = ColumnRegistry(nodes)

        self._params = _SchemaParams(
            name=name,
            is_required=not optional,
            stage=stage,
            registry=registry,
            source_columns=_cols_to_sources(cols, schema_name=name),
            refined_columns=_cols_to_refined_targets(nodes),
            strict=strict,
            coerce=coerce,
            table_checks=list(table_validations) if table_validations else [],
        )

    def columns(
        self,
        *args: Col | Iterable[Col] | dict[str, Col],
        method: Literal["merge", "replace"] = "merge",
        **kwargs: Col,
    ) -> "TableSchema":
        """Add or replace columns in the schema.

        Args:
            *args: ColumnSchema objects, lists of ColumnSchema, or dicts mapping names to ColumnSchema
            method: Either "merge" to add to existing columns or "replace" to replace all columns
            **kwargs: Named ColumnSchema objects where the key is the column name

        Returns:
            TableSchema: A new schema with the updated columns
        """
        cols = _parse_columns_into_list(*args, **kwargs)
        new_nodes = _cols_to_nodes(self._params.name, self._params.stage, columns=cols)
        if method == "merge":
            new_registry = _reset_registry(self._params.registry.nodes() + new_nodes)
            new_source_columns = {
                **self._params.source_columns,
                **_cols_to_sources(cols, schema_name=self._params.name),
            }
            new_refined_columns = {
                **self._params.refined_columns,
                **_cols_to_refined_targets(new_nodes),
            }
            return self._replace(
                registry=new_registry,
                source_columns=new_source_columns,
                refined_columns=new_refined_columns,
            )
        elif method == "replace":
            return self._replace(
                registry=_reset_registry(new_nodes),
                source_columns=_cols_to_sources(cols, schema_name=self._params.name),
                refined_columns=_cols_to_refined_targets(new_nodes),
            )
        else:
            raise SchemaConfigurationError(f"Invalid method: {method}")

    def optional(self, optional: bool = True) -> "TableSchema":
        """Set the schema as required"""
        return self._replace(is_required=not optional)

    def strict(self, strict: bool = True) -> "TableSchema":
        """Set the schema to strict mode"""
        return self._replace(strict=strict)

    def coerce(self, coerce: CoerceOverride) -> "TableSchema":
        """Set the coercion mode for the schema"""
        return self._replace(coerce=coerce)

    def table_validation(
        self, *checks: "TableCheckType | Iterable[TableCheckType]"
    ) -> "TableSchema":
        """
        Configure table-level validation checks.

        Table checks validate aggregate properties of the output data,
        such as how many rows were removed or minimum row count requirements.

        Args:
            *checks: BaseTableCheck instances

        Returns:
            TableSchema: A new schema with table validation checks configured

        Examples:
            # Reject if more than 40% of rows removed
            schema.table_validation(
                z.TableCheck.removed_rows(reject=0.4)
            )

            # Multiple checks
            schema.table_validation(
                z.TableCheck.removed_rows(warning=0.2, error=0.3, reject=0.5),
                z.TableCheck.min_rows(reject=10)
            )
        """
        from .validation import BaseTableCheck

        for check in checks:
            if not isinstance(check, BaseTableCheck):
                raise SchemaConfigurationError(
                    f"All table checks must be TableCheck instances, got {type(check)}"
                )

        return self._replace(table_checks=list(checks))

    @property
    def name(self) -> str:
        """Get the name of the table schema"""
        return self._params.name

    @property
    def is_required(self) -> bool:
        """Get the required status of the table schema"""
        return self._params.is_required

    @property
    def stage(self) -> str:
        """Get the stage of the table schema"""
        return self._params.stage

    def step_1_normalise_table_structure(
        self, df: LazyFrame | DataFrame, *, source_name: str | None = None
    ) -> ValidationResult:
        """
        Normalises the provided Polars LazyFrame to ensure column headers align with the
        defined schema/column definitions. It will attempt to rename columns based on
        the column variants, if column headers are missing it will add them, and drop any
        additional column not defined in the schema.

        Args:
            df (LazyFrame | DataFrame): The Polars LazyFrame or DataFrame to be normalised.
            source_name (str | None): Optional name of the source for populating error messages.

        Returns:
            ValidationResult: The result of the normalization process, including the
            normalized lazy frame and any errors encountered during the process.

        """
        source_columns = list(self._params.source_columns.values())
        return normalise_column_headers(
            df.lazy(),
            schema_name=self._params.name,
            col_defs=source_columns,
            source_name=source_name,
        )

    def step_2_coerce_datatypes(
        self, df: LazyFrame | DataFrame, *, source_name: str | None = None
    ) -> ValidationResult:
        """
        Coerces the data types of the columns in the provided Polars LazyFrame (lf) to match the
        defined schema/column definitions. This function uses the column definitions to determine
        the expected data types and applies the necessary coercions to the LazyFrame.

        Args:
            df (LazyFrame | DataFrame): The Polars LazyFrame or DataFrame to be coerced.
            source_name (str | None): Optional name of the source for populating error messages.

        Returns:
            ValidationResult: The result of the coercion process, including the
            coerced lazy frame and any errors encountered during the process.
        """
        return coerce_column_types(
            df.lazy(),
            schema_name=self._params.name,
            col_defs=list(self._params.source_columns.values()),
            source_name=source_name,
            coerce_override=self._params.coerce,
        )

    def step_3_prepare_additional_columns(
        self, df: LazyFrame | DataFrame, *, source_name: str | None = None
    ) -> ValidationResult:
        """
        Applies optimized transformations to the provided Polars LazyFrame (lf). This function
        uses the column definitions to create cleaned & derived/calculated columns, and creates
        check columns based on the validation rules defined for each column.

        Args:
            df (LazyFrame | DataFrame): The Polars LazyFrame or DataFrame to be processed.
            source_name (str | None): Optional name of the source for populating error messages.

        Returns:
            ValidationResult: The result of the preparation process, including the
            processed LazyFrame and any errors encountered during the process.
        """
        return prepare_additional_columns(
            df.lazy(),
            schema_name=self._params.name,
            source_name=source_name,
            registry=self._params.registry,
        )

    def step_4_validate_columns(
        self, df: LazyFrame | DataFrame, *, source_name: str | None = None
    ) -> ValidationResult:
        """
        Applies validation rules to the provided Polars LazyFrame (lf) based on the column definitions.
        This uses the check columns created in step 2 and applies the validation thresholds to determine
        the resulting validation status/level. The returned LazyFrame isn't modified, but should only be used
        if the entire validation process succeeds without any `reject` level errors.

        Args:
            df (LazyFrame | DataFrame): The Polars LazyFrame or DataFrame to be validated.
            source_name (str | None): Optional name of the source for populating error messages.

        Returns:
            ValidationResult: The result of the validation process, including the
            validated LazyFrame and any errors encountered during the process.
        """
        lf = df.lazy()
        validation_errors = []
        rejectable_columns: list[str] = []

        reject = False
        for c in self._params.registry.nodes():
            if c.validation_rule is None:
                continue
            check = c.validation_rule.validate(lf, source=source_name)
            if check is not None:
                validation_errors.append(check)
                if check.level == ThresholdLevel.REJECT.level:
                    reject = True
            if c.validation_rule.remove_row_on_fail:
                rejectable_columns.append(c.name)

        if len(rejectable_columns) > 0:
            lf_with_reject_col = lf.with_columns(
                ~any_horizontal(
                    *[col(r).ne(ThresholdLevel.PASS.level) for r in rejectable_columns]
                ).alias(VALIDATION_CHECK_COL)
            )
        else:
            lf_with_reject_col = lf.with_columns(lit(True).alias(VALIDATION_CHECK_COL))

        return ValidationResult(
            data=lf_with_reject_col, errors=validation_errors, reject=reject
        )

    def step_5_validate_and_filter_table(
        self, df: LazyFrame | DataFrame, *, source_name: str | None = None
    ) -> ValidationResult:
        """
        Drop rows that failed validation and evaluate table-level checks.

        This step:
        1. Filters out rows marked for removal (via VALIDATION_CHECK_COL)
        2. Counts total rows and rows removed
        3. Evaluates table-level validation checks against these metrics
        4. Returns rejection if any table check reaches reject threshold

        Args:
            df (LazyFrame | DataFrame): The Polars LazyFrame or DataFrame with validation columns.
            source_name (str | None): Optional name of the source for populating error messages.

        Returns:
            ValidationResult: The result with filtered data and any table validation errors.
        """
        lf = df.lazy()
        filtered_lf = lf.filter(col(VALIDATION_CHECK_COL))

        table_errors = []

        if not self._params.table_checks:
            return ValidationResult(data=filtered_lf, errors=table_errors, reject=False)

        should_reject = False
        for check in self._params.table_checks:
            result = check.validate(
                validated_lf=lf,
                filtered_lf=filtered_lf,
                schema_name=self._params.name,
                source=source_name,
            )
            if result:
                table_errors.append(result)
                if result.level == ThresholdLevel.REJECT.level:
                    should_reject = True

        return ValidationResult(
            data=filtered_lf, errors=table_errors, reject=should_reject
        )

    def step_6_refine_structure(
        self, df: LazyFrame | DataFrame, *, source_name: str | None = None
    ):
        """
        Refines the schema to a final state by:

        - replacing original columns with clean columns (unless the Clean definition was given an `alias`)
        - dropping the check columns used in validation (unless the Check definition was given an `alias`)
        - renaming derived/calculated columns to remove prefix

        Args:
            df (LazyFrame | DataFrame): The Polars LazyFrame or DataFrame from the filter stage.
            source_name (str | None): Optional name of the source for populating error messages.

        Returns:
            ValidationResult: The result of the refinement process, including the
            tidy LazyFrame and any errors encountered during the process.
        """
        lf = df.lazy()

        try:
            refined = lf.select(
                *[
                    col(self._params.registry.get_by_id(col_id).name).alias(alias)
                    for alias, col_id in self._params.refined_columns.items()
                ]
            )
            return ValidationResult(data=refined, errors=[], reject=False)
        except Exception as e:
            return ValidationResult(
                data=lf,
                errors=[
                    TableValidationError(
                        message="Fatal error refining to final schema",
                        schema=self._params.name,
                        level="reject",
                        error=f"{e}",
                        source=source_name,
                    )
                ],
                reject=True,
            )

    def apply(
        self, df: LazyFrame | DataFrame, *, source_name: str | None = None
    ) -> ProcessingFailure | ProcessingSuccess:
        """
        Applies the schema to the DataFrame/LazyFrame and processes data through multiple stages:

        `normalisation -> preparation -> validation -> filtering -> refinement`

        Each stage processes the input data and checks for errors. If any stage fails,
        the process aborts (in 'strict' mode), returning the stage results and a failure status. If all stages
        are successful, the method returns a success status with all intermediate and final
        results.

        Args:
            df (LazyFrame | DataFrame): Polars LazyFrame or DataFrame containing the data to be processed.
            source_name (str | None): Optional name of the source for populating error messages.

        Returns:
            ProcessingResult: If any stage (`normalise`, `prepare`, `validate`, 'filter', 'refine') fails with a `reject`,
            returns a `ProcessingFailure` containing intermediate results, encountered errors, and
            the name of the failed stage. Otherwise, returns a `ProcessingSuccess` containing
            intermediate and final results, as well as collected errors during processing.
        """
        errors = []
        failed_stage: ProcessingStage | None = None
        normalised = self.step_1_normalise_table_structure(df, source_name=source_name)
        errors.extend(normalised.errors)
        if normalised.reject:
            failed_stage = "normalise"
            if self._params.strict and failed_stage is not None:
                return ProcessingFailure(
                    normalised=normalised.data,
                    coerced=None,
                    prepared=None,
                    validated=None,
                    filtered=None,
                    refined=None,
                    data=None,
                    errors=errors,
                    failed_stage=failed_stage,
                )

        coerced = self.step_2_coerce_datatypes(normalised.data, source_name=source_name)
        errors.extend(coerced.errors)
        if coerced.reject:
            failed_stage = "coerce" if failed_stage is None else failed_stage
            if self._params.strict and failed_stage is not None:
                return ProcessingFailure(
                    normalised=normalised.data,
                    coerced=coerced.data,
                    prepared=None,
                    validated=None,
                    filtered=None,
                    refined=None,
                    data=None,
                    errors=errors,
                    failed_stage=failed_stage,
                )

        prepped = self.step_3_prepare_additional_columns(
            coerced.data, source_name=source_name
        )
        errors.extend(prepped.errors)
        if prepped.reject:
            failed_stage = "prepare" if failed_stage is None else failed_stage
            if self._params.strict and failed_stage is not None:
                return ProcessingFailure(
                    normalised=normalised.data,
                    coerced=coerced.data,
                    prepared=prepped.data,
                    validated=None,
                    filtered=None,
                    refined=None,
                    data=None,
                    errors=errors,
                    failed_stage=failed_stage,
                )

        valid = self.step_4_validate_columns(prepped.data, source_name=source_name)
        errors.extend(valid.errors)

        if valid.reject:
            failed_stage = "validate" if failed_stage is None else failed_stage
            if self._params.strict and failed_stage is not None:
                return ProcessingFailure(
                    normalised=normalised.data,
                    coerced=coerced.data,
                    prepared=prepped.data,
                    validated=valid.data,
                    filtered=None,
                    refined=None,
                    data=None,
                    errors=errors,
                    failed_stage=failed_stage,
                )

        filtered = self.step_5_validate_and_filter_table(
            valid.data, source_name=source_name
        )
        errors.extend(filtered.errors)

        if filtered.reject:
            failed_stage = "filter" if failed_stage is None else failed_stage
            if self._params.strict and failed_stage is not None:
                return ProcessingFailure(
                    normalised=normalised.data,
                    coerced=coerced.data,
                    prepared=prepped.data,
                    validated=valid.data,
                    filtered=filtered.data,
                    refined=None,
                    data=None,
                    errors=errors,
                    failed_stage=failed_stage,
                )

        refined = self.step_6_refine_structure(filtered.data, source_name=source_name)
        errors.extend(refined.errors)

        if filtered.reject or failed_stage is not None:
            return ProcessingFailure(
                normalised=normalised.data,
                coerced=coerced.data,
                prepared=prepped.data,
                validated=valid.data,
                filtered=filtered.data,
                refined=refined.data,
                data=None,
                errors=errors,
                failed_stage="refine" if failed_stage is None else failed_stage,
            )
        else:
            # If we get here, the data is valid
            return ProcessingSuccess(
                normalised=normalised.data,
                coerced=coerced.data,
                prepared=prepped.data,
                validated=valid.data,
                filtered=filtered.data,
                refined=refined.data,
                data=refined.data,
                errors=errors,
            )

    def _replace(self, **kwargs):
        if "registry" not in kwargs:
            stage = kwargs.get("stage", self._params.stage)
            name = kwargs.get("name", self._params.name)
            kwargs["registry"] = ColumnRegistry(
                [
                    replace(n, stage=stage, schema=name)
                    for n in self._params.registry.nodes()
                ]
            )

        new_params = replace(self._params, **kwargs)
        return TableSchema(name=new_params.name).__set_params(new_params)

    def __set_params(self, params: _SchemaParams) -> "TableSchema":
        self._params = params
        return self


def _cols_to_nodes(
    schema: str, stage: str | None = None, columns: List[Col] | None = None
) -> List[ColumnNode]:
    nodes = []
    if columns is None:
        return nodes

    for c in columns:
        if not isinstance(c, Col):
            raise SchemaConfigurationError(
                f"All columns must be a Column Schema definition - {c}"
            )
        if c.ref.base_name is None:
            raise SchemaConfigurationError("""
        All Columns must have a name, either:
          - directly on creation, e.g. z.col("name")
          - assigning after creation, e.g. z.col().with_name("name")
          - defined through a keyword arg on schema.columns e.g. x.columns( name = z.col() )
          - defined through a dict key on schema.columns e.g. x.columns({ "name": z.col() })
        """)
        nodes.extend(c.get_nodes(schema, stage))

    return nodes


def _cols_to_sources(
    columns: List[Col] | None, schema_name: str | None = None
) -> dict[str, SourceColDef]:
    sources = {}
    variants = {}
    if columns is None:
        return sources
    for c in columns:
        if c.has_expression:
            # if a column has an expression, it is not a source column
            continue

        ref = c.ref

        if ref.name in sources:
            raise DuplicateColumnError(
                f"Duplicate source column name: {ref.name}",
                column_name=ref.name,
                schema_name=schema_name,
            )
        else:
            col_variants = {sanitise_column_name(a) for a in c.get_variants}
            col_variants.add(sanitise_column_name(ref.name))

            # Check if the alias is already in use
            for a in col_variants:
                if a in variants:
                    raise DuplicateColumnError(
                        f"Duplicate column alias: The sanitised alias `{a}` for column `{ref.name}` already used for `{variants[a]}`",
                        column_name=ref.name,
                        duplicate_of=variants[a],
                        schema_name=schema_name,
                    )
                else:
                    variants[a] = ref.name

            sources[ref.name] = SourceColDef(
                name=ref.name,
                variants=col_variants,
                if_missing=c.if_missing,
                is_meta=c.ref.is_meta,
                dtype=c.params.dtype,
                coerce=c.params.coerce if c.params.dtype is not None else None,
            )

    return sources


def _cols_to_refined_targets(nodes: List[ColumnNode] | None):
    targets = {}
    counts = {}
    for c in nodes:
        if c.is_temporary:
            continue
        if c.alias is not None:
            if c.alias not in counts:
                counts[c.alias] = 1
                targets[c.alias] = c.id
            else:
                index = counts[c.alias] + 1
                counts[c.alias] = index
                targets[f"{c.alias}_{index}"] = c.id

    return targets


def _reset_registry(nodes: List[ColumnNode], **kwargs):
    return ColumnRegistry([replace(n, **kwargs) for n in nodes])


def _parse_columns_into_list(
    *args: Col | Iterable[Col] | dict[str, Col],
    **kwargs: Col,
) -> List[Col]:
    cols = []
    # Process positional arguments
    for arg in args:
        if arg is None:
            continue
        if isinstance(arg, dict):
            # Handle dict input like {a: z.col, b: z.col}
            cols.extend(c.with_name(k) for k, c in arg.items())
        elif isinstance(arg, list):
            # Handle list input like [z.col("a"), z.col("b")]
            cols.extend(arg)
        else:
            # Handle single ColumnSchema like z.col("a")
            cols.append(arg)

    # Process keyword arguments
    cols.extend(c.with_name(k) for k, c in kwargs.items())

    return cols
