# %%
from dataclasses import dataclass, field, KW_ONLY, fields, replace
from typing import List, Literal, Optional
from polars import Expr, DataType, when, lit

from ..validation._utils.data_checks import (
    ROW_VALIDATION_SUCCESS_VALUE,
    ROW_VALIDATION_REJECT_VALUE,
    ROW_VALIDATION_FAILURE_VALUE,
)
from ..._utils.data_type import get_polars_type, get_data_type_label
from ...ref import ColumnRef
from ...types import ColumnNode, CoerceOption
from ...types.sensitivity import Sensitivity
from ...types.data_type import ColumnDataType
from ...types.validation.threshold import CheckLevel, ThresholdLevel
from ..._utils.args import flatten_args
from ...exceptions import ColumnConfigurationError
from .._clean import (
    CleanStage,
    CleanColumn,
)
from ..validation import (
    ColumnCheckType,
    BaseCheck,
    ThresholdType,
    create_validation_rule,
)

# %%

type _RequiredLevel = CheckLevel | bool | None


@dataclass(frozen=True)
class _ColumnParams:
    ref: ColumnRef
    _: KW_ONLY
    type_label: str = field(default="unknown")
    dtype: Optional[DataType] = field(default=None)
    coerce: CoerceOption = field(default="default")
    sensitivity: Sensitivity = field(default=Sensitivity.UNKNOWN)
    variants: set[str] = field(default_factory=set)
    if_missing: ThresholdLevel = field(default=ThresholdLevel.REJECT)
    validations: List[ColumnCheckType] = field(default_factory=list)
    clean: Optional[CleanStage] = field(default=None)
    expression: Optional[Expr] = field(default=None)
    custom_validation: dict[str, str | ThresholdType] | None = field(default=None)
    is_temporary: bool = field(default=False)


def _verify_validations(validations: List[ColumnCheckType] | None):
    if validations is not None:
        for v in validations:
            if not isinstance(v, BaseCheck):
                raise ColumnConfigurationError(
                    f"Expected {v} to be a Column Validation Check"
                )


class Col:
    """
    Defines a column in a table schema, including data type, sensitivity, validations, and cleaning steps.

    Parameters:
        col_ref (ColumnRef): Reference to the column.
        data_type (ColumnDataType): Data type of the column.
        sensitivity (Sensitivity): Sensitivity level.
        variants (set[str]): Variants for the column.
        validations (List[ColumnCheckType]): Validation checks.
        clean (CleanStage): Cleaning stage or type.
        temporary (bool): Whether the column is temporary.
    """

    def __init__(
        self,
        col_ref: ColumnRef,
        *,
        data_type: ColumnDataType = "unknown",
        coerce: CoerceOption = "default",
        sensitivity: Sensitivity = None,
        variants: set[str] = None,
        optional: CheckLevel | bool = False,
        validations: List[ColumnCheckType] = None,
        clean: CleanStage | None = None,
        temporary: bool = False,
    ):
        _verify_validations(validations)
        if clean is not None and not isinstance(clean, CleanColumn):
            raise ColumnConfigurationError("clean must be a Clean variant")

        if isinstance(optional, bool):
            optional: CheckLevel = "pass" if optional else "reject"

        self._params = _ColumnParams(
            ref=col_ref,
            type_label=get_data_type_label(data_type),
            dtype=get_polars_type(data_type),
            coerce=coerce,
            sensitivity=sensitivity if sensitivity is not None else Sensitivity.UNKNOWN,
            variants=variants if variants is not None else set(),
            validations=validations if validations is not None else [],
            clean=clean,
            if_missing=_get_missing_level(optional),
            is_temporary=temporary,
        )

    def sensitivity(self, sensitivity: Sensitivity) -> "Col":
        return self._replace(sensitivity=sensitivity)

    def data_type(
        self, data_type: ColumnDataType, *, coerce: CoerceOption = "default"
    ) -> "Col":
        return self._replace(
            type_label=get_data_type_label(data_type),
            dtype=get_polars_type(data_type),
            coerce=coerce,
        )

    def variants(self, *args: str | list[str], merge: bool = False) -> "Col":
        if args is None or args == (None,):
            args = set()
        variants = set(flatten_args(args))
        if merge:
            variants = variants | self._params.variants
        return self._replace(variants=variants)

    def validations(
        self, *args: ColumnCheckType | list[ColumnCheckType], merge: bool = False
    ) -> "Col":
        validations = flatten_args(args)
        _verify_validations(validations)
        if merge:
            validations = validations + self._params.validations

        return self._replace(validations=validations)

    def clean(self, clean: CleanStage) -> "Col":
        if not isinstance(clean, CleanColumn):
            raise ColumnConfigurationError("Must be a Clean variant")
        return self._replace(clean=clean)

    def optional(self, optional: bool | CheckLevel = True) -> "Col":
        if isinstance(optional, bool):
            optional: CheckLevel = "pass" if optional else "reject"

        return self._replace(if_missing=_get_missing_level(optional))

    def coerce(self, option: CoerceOption = "strict"):
        return self._replace(coerce=option)

    def temporary(self, is_temp: bool = True) -> "Col":
        """Marks this column as temporary, excluding it from the final refined output"""
        return self._replace(is_temporary=is_temp)

    def temp(self, is_temp: bool = True) -> "Col":
        """Alias for temporary(). Mark this column as temporary, excluding it from the final refined output"""
        return self.temporary(is_temp)

    def get_alias(self):
        p = self._params
        ref = p.ref
        name = ref.base_name if ref.is_derived else ref.name

        if p.clean is not None and p.clean.get_alias(ref) == name:
            return None

        return name

    def get_nodes(self, schema: str, stage: str | None = None) -> List[ColumnNode]:
        p = self._params
        ref = p.ref.with_schema(schema, stage)

        column_type = _get_col_type(ref)
        validation_rule = (
            create_validation_rule(
                check_method_id="custom_validation",
                message=p.custom_validation["message"],
                source_column=", ".join(p.expression.meta.root_names()),
                check_col_name=ref.name,
                schema=ref.schema,
                thresholds=p.custom_validation["thresholds"],
                remove_row_on_fail=p.custom_validation["remove_row_on_fail"] or False,
            )
            if ref.is_custom_check
            else None
        )
        if ref.is_custom_check:
            expr = (
                when(self.expr)
                .then(lit(ROW_VALIDATION_SUCCESS_VALUE))
                .otherwise(
                    lit(
                        ROW_VALIDATION_REJECT_VALUE
                        if p.custom_validation["remove_row_on_fail"]
                        else ROW_VALIDATION_FAILURE_VALUE
                    )
                )
            ).alias(ref.name)
        else:
            expr = self.expr

        nodes: list[ColumnNode] = [
            ColumnNode(
                id=ref.id,
                name=ref.name,
                data_type=p.type_label,
                column_type=column_type,
                schema=ref.schema,
                stage=ref.stage,
                sensitivity=p.sensitivity,
                expression=expr,
                validation_rule=validation_rule,
                alias=self.get_alias(),
                is_temporary=p.is_temporary,
            )
        ]
        if p.clean is not None:
            clean_expr = p.clean.apply(ref)
            clean_params = p.clean.params
            nodes.append(
                ColumnNode(
                    id=ref.clean().id,
                    name=clean_expr.meta.output_name(),
                    data_type=get_data_type_label(clean_params.data_type),
                    column_type="cleaned",
                    schema=ref.schema,
                    stage=ref.stage,
                    sensitivity=clean_params.col_sensitivity
                    if clean_params.col_sensitivity is not None
                    else p.sensitivity,
                    expression=clean_expr,
                    validation_rule=None,
                    alias=p.clean.get_alias(ref),
                    is_temporary=p.is_temporary,
                )
            )
        for v in p.validations:
            nodes.append(v.get_validation_node(ref))

        return nodes

    @property
    def ref(self) -> ColumnRef:
        """Get the column reference"""
        return self._params.ref

    @property
    def name(self) -> str:
        """Get the name of the column"""
        return self._params.ref.name

    @property
    def params(self) -> _ColumnParams | None:
        """Get the params of the column"""
        return self._params

    @property
    def get_variants(self) -> set[str]:
        """Get the variants of the column"""
        return self._params.variants

    @property
    def if_missing(self) -> ThresholdLevel:
        """Get the threshold level for the column if missing"""
        return self._params.if_missing

    @property
    def has_expression(self) -> bool:
        """Check if the column is/has an expression"""
        return self._params.expression is not None

    @property
    def expr(self) -> Expr | None:
        return (
            self._params.expression.alias(self._params.ref.name)
            if self.has_expression
            else None
        )

    def with_name(self, name: str):
        return self._replace(ref=self._params.ref.with_base_name(name))

    def derived(self, expr: Expr) -> "Col":
        return self._replace(ref=self._params.ref.derived(), expression=expr)

    def custom_check(
        self,
        expr: Expr,
        thresholds: ThresholdType,
        message: str,
        remove_row_on_fail: bool = False,
    ) -> "Col":
        print(isinstance(expr, Expr), expr)
        if not isinstance(expr, Expr):
            raise ColumnConfigurationError(
                "custom_check.function must be a Polars Expression"
            )

        return self._replace(
            ref=self._params.ref.custom_check(),
            expression=expr,
            custom_validation={
                "message": message,
                "thresholds": thresholds,
                "remove_row_on_fail": remove_row_on_fail,
            },
        )

    def _replace(self, **kwargs):
        new_params = replace(self._params, **kwargs)
        # initiate an empty column reference & manually apply the new params
        # we do it this way to set properties not allowed in the constructor
        return Col(col_ref=new_params.ref).__set_params(new_params)

    def __set_params(self, params: _ColumnParams) -> "Col":
        self._params = params
        return self

    def __repr__(self):
        """Return a string representation of the instance."""
        param_strs = []
        for field_name in [f.name for f in fields(_ColumnParams)]:
            value = getattr(self._params, field_name)
            if value is not None and (not isinstance(value, list) or value):
                param_strs.append(f"{field_name}={repr(value)}")
        return f"{self.__class__.__name__}({', '.join(param_strs)})"


# %%
def _get_col_type(
    ref: ColumnRef,
) -> Literal["source", "cleaned", "validation", "meta", "derived", "custom_validation"]:
    if ref.is_meta:
        return "meta"
    if ref.is_derived:
        return "custom_validation"
    elif ref.is_derived:
        return "derived"
    else:
        return "source"


def _get_missing_level(level: CheckLevel) -> ThresholdLevel:
    if level == "debug":
        return ThresholdLevel.DEBUG
    elif level == "warning":
        return ThresholdLevel.WARNING
    elif level == "error":
        return ThresholdLevel.ERROR
    elif level == "reject":
        return ThresholdLevel.REJECT
    else:
        return ThresholdLevel.PASS


# %%
