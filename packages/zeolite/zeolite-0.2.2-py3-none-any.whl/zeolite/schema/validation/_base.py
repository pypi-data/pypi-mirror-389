from dataclasses import dataclass, replace, asdict
from typing import TYPE_CHECKING, Optional, TypeVar

from ...types.validation.threshold import Threshold, CheckThreshold
from ...exceptions import InvalidThresholdError, TableCheckConfigurationError

if TYPE_CHECKING:
    from polars import LazyFrame
    from ...types.error import DataValidationError


type ThresholdType = Threshold | dict[str, CheckThreshold] | None


@dataclass(frozen=True, kw_only=True)
class _TableCheckParams:
    label: str
    thresholds: Threshold
    message: str = ""


_T = TypeVar("_T", bound="_TableCheckParams")


def _get_threshold(
    *,
    thresholds: ThresholdType = None,
    debug: Optional[CheckThreshold] = None,
    warning: Optional[CheckThreshold] = None,
    error: Optional[CheckThreshold] = None,
    reject: Optional[CheckThreshold] = None,
) -> Threshold:
    """Create a Threshold object from various input formats"""
    if thresholds is not None:
        if isinstance(thresholds, Threshold):
            return thresholds
        elif isinstance(thresholds, dict):
            return Threshold(**thresholds)
        else:
            raise InvalidThresholdError(f"Invalid thresholds type: {type(thresholds)}")
    else:
        # Create from individual parameters
        kwargs = {}
        if debug is not None:
            kwargs["debug"] = debug
        if warning is not None:
            kwargs["warning"] = warning
        if error is not None:
            kwargs["error"] = error
        if reject is not None:
            kwargs["reject"] = reject

        if not kwargs:
            raise InvalidThresholdError(
                "At least one of `thresholds`, `debug`, `warning`, `error`, or `reject` must be provided"
            )

        return Threshold(**kwargs)


class BaseTableCheck:
    """Base class for table-level validation checks"""

    _required_args: set[str] = set()

    def __init__(
        self,
        message: str = "",
        thresholds: ThresholdType = None,
        debug: Optional[CheckThreshold] = None,
        warning: Optional[CheckThreshold] = None,
        error: Optional[CheckThreshold] = None,
        reject: Optional[CheckThreshold] = None,
        label: Optional[str] = None,
    ):
        self._params = _TableCheckParams(
            message=message,
            thresholds=_get_threshold(
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
        """Unique identifier for this check type"""
        return "__table_check_base__"

    @property
    def params(self) -> _TableCheckParams:
        return self._params

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
            and (debug is None)
            and (warning is None)
            and (error is None)
            and (reject is None)
        ):
            raise InvalidThresholdError(
                "At least one of `thresholds`, `debug`, `warning`, `error`, or `reject` must be provided"
            )

        new_thresholds = _get_threshold(
            thresholds=thresholds,
            debug=debug,
            warning=warning,
            error=error,
            reject=reject,
        )

        return self._replace(
            thresholds=new_thresholds, message=message or self._params.message
        )

    def debug(self, level: CheckThreshold):
        return self._merge_thresholds(debug=level)

    def warning(self, level: CheckThreshold):
        return self._merge_thresholds(warning=level)

    def error(self, level: CheckThreshold):
        return self._merge_thresholds(error=level)

    def reject(self, level: CheckThreshold):
        return self._merge_thresholds(reject=level)

    def message(self, message: str):
        """Set a custom error message"""
        return self._replace(message=message)

    def validate(
        self,
        validated_lf: "LazyFrame",
        filtered_lf: "LazyFrame",
        *,
        schema_name: str,
        source: str | None = None,
    ) -> "DataValidationError | None":
        """
        Evaluate this check against table metrics.

        Args:
            validated_lf: The LazyFrame with validation column
            filtered_lf: The LazyFrame with the row filter applied
            schema_name: Name of the schema being validated
            source: Optional source name for error messages

        Returns:
            DataValidationError if check fails, None if passes
        """
        raise NotImplementedError("Must be implemented in subclass")

    def _merge_thresholds(self, **kwargs):
        if self._params.thresholds is not None:
            new_thresholds = replace(self._params.thresholds, **kwargs)
        else:
            new_thresholds = Threshold(**kwargs)
        return self._replace(thresholds=new_thresholds)

    def _replace(self, **kwargs):
        new_params = replace(self._params, **kwargs)

        args = {}
        for arg in self._required_args:
            if hasattr(new_params, arg):
                args[arg] = getattr(new_params, arg)
            elif hasattr(self, arg):
                args[arg] = getattr(self, arg)
            else:
                raise TableCheckConfigurationError(
                    f"Required argument '{arg}' not found in params or instance"
                )

        return self.__class__(**args)._set_params(new_params)

    def _set_params(self, params: _TableCheckParams) -> "BaseTableCheck":
        self._params = params
        return self

    def _create_extended_params(self, params_class: type[_T], **extra_params) -> _T:
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
