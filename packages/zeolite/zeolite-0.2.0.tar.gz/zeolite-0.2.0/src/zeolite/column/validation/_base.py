from dataclasses import dataclass, field, replace, asdict
from typing import TYPE_CHECKING, Literal, Optional, TypeVar

from polars import Expr

from ...types.validation.threshold import Threshold, CheckThreshold
from ...exceptions import InvalidThresholdError, CheckConfigurationError
from ._utils.validation_node import get_validation_node

if TYPE_CHECKING:
    from ...ref import ColumnRef
    from ...types import ColumnNode

type ThresholdType = Threshold | dict[str, CheckThreshold] | None

type CheckFailLevel = Literal["fail", "reject"]

T = TypeVar("T", bound="_CheckParams")


@dataclass(frozen=True, kw_only=True)
class _CheckParams:
    label: str
    remove_row_on_fail: bool = False
    alias: str | None = None
    check_on_cleaned: bool = False
    message: str = field(default="")
    thresholds: Threshold


class BaseCheck:
    """Configuration for a row check"""

    _required_args: set[str] = set()

    def __init__(
        self,
        remove_row_on_fail: bool = False,
        alias: str | None = None,
        check_on_cleaned: bool = False,
        message: str = "",
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        label: Optional[str] = None,
    ):
        self._params = _CheckParams(
            remove_row_on_fail=remove_row_on_fail,
            alias=alias,
            check_on_cleaned=check_on_cleaned,
            message=message,
            thresholds=_get_threshold(
                remove_row_on_fail=remove_row_on_fail,
                thresholds=thresholds,
                debug=debug,
                warning=warning,
                error=error,
                reject=reject,
            ),
            label=label or self.method_id(),
        )

    @classmethod
    def method_id(cls) -> str:
        return "__check_base__"

    def thresholds(
        self,
        *,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        thresholds: Optional[ThresholdType] = None,
        message: Optional[str] = None,
    ):
        """Configure thresholds for this check"""
        if (
            (thresholds is None)
            and (debug is None or debug is False)
            and (warning is None or warning is False)
            and (error is None or error is False)
            and (reject is None or reject is False)
        ):
            raise InvalidThresholdError(
                "At least one of `thresholds`, `debug`, `warning`, `error`, or `reject` must be provided"
            )

        new_thresholds = _get_threshold(
            remove_row_on_fail=self._params.remove_row_on_fail,
            thresholds=thresholds,
            debug=debug,
            warning=warning,
            error=error,
            reject=reject,
        )

        return self._replace(
            thresholds=new_thresholds, message=message or self._params.message
        )

    def _merge_thresholds(self, **kwargs):
        if self._params.thresholds is not None:
            new_thresholds = replace(self._params.thresholds, **kwargs)
        else:
            new_thresholds = Threshold(**kwargs)
        return self._replace(thresholds=new_thresholds)

    def debug(self, level: CheckThreshold):
        return self._merge_thresholds(debug=level)

    def warning(self, level: CheckThreshold):
        return self._merge_thresholds(warning=level)

    def error(self, level: CheckThreshold):
        return self._merge_thresholds(error=level)

    def reject(self, level: CheckThreshold):
        return self._merge_thresholds(reject=level)

    def remove_row_on_fail(self, remove: bool = True):
        new_thresholds = _get_threshold(
            remove_row_on_fail=remove,
            thresholds=self._params.thresholds,
        )
        return self._replace(remove_row_on_fail=remove, thresholds=new_thresholds)

    def alias(self, alias: str):
        return self._replace(alias=alias)

    def message(self, message: str):
        return self._replace(message=message)

    def check_on_cleaned(self, check_cleaned: bool = True):
        return self._replace(check_on_cleaned=check_cleaned)

    @property
    def params(self) -> _CheckParams:
        return self._params

    def get_validation_node(self, source_column: "ColumnRef") -> "ColumnNode":
        """Create a validation node for this check"""
        return get_validation_node(
            check=self,
            source_column=source_column,
        )

    def expression(
        self, source_column: str, alias: str, fail_value: CheckFailLevel
    ) -> Expr:
        """Check expression for this check"""
        raise NotImplementedError("Must be implemented in subclass")

    def _replace(self, **kwargs):
        new_params = replace(self._params, **kwargs)

        args = {}
        for arg in self._required_args:
            if hasattr(new_params, arg):
                args[arg] = getattr(new_params, arg)
            elif hasattr(self, arg):
                args[arg] = getattr(self, arg)
            else:
                raise CheckConfigurationError(
                    f"Required argument '{arg}' not found in params or instance"
                )

        return self.__class__(**args)._set_params(new_params)

    def _set_params(self, params: _CheckParams) -> "BaseCheck":
        self._params = params
        return self

    def _create_extended_params(self, params_class: type[T], **extra_params) -> T:
        """
        Helper method to create extended params while preserving the Threshold dataclass.
        """
        base_params = {
            k: v for k, v in asdict(self._params).items() if k != "thresholds"
        }
        return params_class(
            **{**base_params, **extra_params},
            thresholds=extra_params.get("thresholds", self._params.thresholds),
        )


def _get_threshold(
    thresholds: ThresholdType = None,
    debug: Optional[CheckThreshold] = None,
    warning: Optional[CheckThreshold] = None,
    error: Optional[CheckThreshold] = None,
    reject: Optional[CheckThreshold] = None,
    remove_row_on_fail: bool = False,
) -> Threshold | None:
    # If we are excluding the row, we want to reject when all rows fail
    default_reject: Literal["all"] | None = (
        "all" if remove_row_on_fail is True else None
    )

    # self.thresholds takes precedence over self.warning, self.error, self.reject
    if thresholds is None:
        if (
            debug is not None
            or warning is not None
            or error is not None
            or reject is not None
        ):
            return Threshold(
                debug=debug,
                warning=warning,
                error=error,
                reject=reject or default_reject,
            )

        if remove_row_on_fail is True:
            return Threshold(warning=True, reject=default_reject)
        else:
            return None

    elif isinstance(thresholds, Threshold):
        return Threshold(
            debug=thresholds.debug,
            warning=thresholds.warning,
            error=thresholds.error,
            reject=thresholds.reject or default_reject,
        )
    elif isinstance(thresholds, dict):
        return Threshold(
            debug=thresholds.get("debug", None),
            warning=thresholds.get("warning", None),
            error=thresholds.get("error", None),
            reject=thresholds.get("reject", default_reject),
        )
    else:
        raise InvalidThresholdError(f"Invalid type for thresholds: {type(thresholds)}")
