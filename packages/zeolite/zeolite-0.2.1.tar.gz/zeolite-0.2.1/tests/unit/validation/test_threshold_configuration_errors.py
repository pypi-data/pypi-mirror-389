"""
Unit tests for threshold configuration error handling.

Tests invalid threshold configurations that should raise appropriate exceptions.
"""

import pytest
import zeolite as z
from zeolite.types.validation.threshold import Threshold, _parse_threshold_value
from zeolite.exceptions import InvalidThresholdError


class TestThresholdValueValidation:
    """Tests for individual threshold value validation."""

    def test_invalid_threshold_values(self):
        """Test that invalid threshold values raise error."""
        # Negative values
        with pytest.raises(InvalidThresholdError):
            Threshold(warning=-0.5)

        # Ambiguous value of 1 (use True or "all" instead)
        with pytest.raises(InvalidThresholdError):
            Threshold(warning=1)

        # Invalid string values
        with pytest.raises(InvalidThresholdError):
            Threshold(warning="invalid_value")  # type: ignore

    def test_valid_threshold_values(self):
        """Test that various valid threshold value formats work."""
        # Boolean values
        threshold = Threshold(warning=True, error=False)
        assert threshold.warning is True
        assert threshold.error is False

        # String literals
        threshold = Threshold(warning="any", error="all")
        assert threshold.warning == "any"
        assert threshold.error == "all"

        # Zero (equivalent to "any")
        threshold = Threshold(warning=0)
        assert threshold.warning == 0

        # Fractions (0 < value < 1)
        threshold = Threshold(warning=0.5, error=0.75)
        assert threshold.warning == 0.5
        assert threshold.error == 0.75

        # Counts (value > 1)
        threshold = Threshold(warning=10, error=20)
        assert threshold.warning == 10
        assert threshold.error == 20


class TestThresholdInitialization:
    """Tests for Threshold initialization errors."""

    def test_threshold_requires_at_least_one_value(self):
        """Test that Threshold requires at least one non-None/False value."""
        # No values
        with pytest.raises(InvalidThresholdError):
            Threshold()

        # All None
        with pytest.raises(InvalidThresholdError):
            Threshold(debug=None, warning=None, error=None, reject=None)

        # All False
        with pytest.raises(InvalidThresholdError):
            Threshold(debug=False, warning=False, error=False, reject=False)

    def test_threshold_initialization_variations(self):
        """Test that Threshold can be initialized with various value combinations."""
        # Single value
        threshold = Threshold(warning="any")
        assert threshold.warning == "any"

        # Multiple values across severity levels
        threshold = Threshold(debug=True, warning=0.1, error=0.5, reject=0.9)
        assert threshold.debug is True
        assert threshold.warning == 0.1
        assert threshold.error == 0.5
        assert threshold.reject == 0.9


class TestThresholdValueParsing:
    """Tests for _parse_threshold_value function."""

    def test_parse_threshold_value_valid_formats(self):
        """Test parsing various valid threshold value formats."""
        # String literals
        fraction, count = _parse_threshold_value("any", "test")
        assert fraction == 0 and count == 1

        fraction, count = _parse_threshold_value("all", "test")
        assert fraction == 1 and count is None

        # Boolean values
        fraction, count = _parse_threshold_value(True, "test")
        assert fraction == 0 and count == 1

        # Zero (equivalent to "any")
        fraction, count = _parse_threshold_value(0, "test")
        assert fraction == 0 and count == 1

        # Fractions (0 < value < 1)
        fraction, count = _parse_threshold_value(0.5, "test")
        assert fraction == 0.5 and count is None

        # Counts (value > 1)
        fraction, count = _parse_threshold_value(10, "test")
        assert fraction is None and count == 10

        # Disabled thresholds
        fraction, count = _parse_threshold_value(None, "test")
        assert fraction is None and count is None

        fraction, count = _parse_threshold_value(False, "test")
        assert fraction is None and count is None

    def test_parse_threshold_value_invalid_formats(self):
        """Test that invalid threshold values raise appropriate errors."""
        # Negative values
        with pytest.raises(InvalidThresholdError):
            _parse_threshold_value(-0.5, "test")

        # Ambiguous value of 1
        with pytest.raises(InvalidThresholdError):
            _parse_threshold_value(1, "test")

        # Invalid string
        with pytest.raises(InvalidThresholdError):
            _parse_threshold_value("invalid", "test")  # type: ignore


class TestThresholdResolution:
    """Tests for threshold resolution logic."""

    def test_threshold_resolve_with_zero_total_rows(self):
        """Test threshold resolution with zero total rows."""
        threshold = Threshold(warning="any")
        result = threshold.resolve(failed_rows=0, total_rows=0)

        assert result.level == "pass"

    def test_threshold_resolve_with_zero_failed_rows(self):
        """Test threshold resolution with zero failed rows."""
        threshold = Threshold(warning="any", error=0.5)
        result = threshold.resolve(failed_rows=0, total_rows=100)

        assert result.level == "pass"

    def test_threshold_resolve_any_threshold(self):
        """Test threshold resolution with 'any' threshold."""
        threshold = Threshold(warning="any")

        # Even 1 failure should trigger warning
        result = threshold.resolve(failed_rows=1, total_rows=100)
        assert result.level == "warning"
        assert result.count_failed == 1
        assert result.fraction_failed == 0.01

    def test_threshold_resolve_all_threshold(self):
        """Test threshold resolution with 'all' threshold."""
        threshold = Threshold(warning="all")

        # Only triggers when all rows fail
        result1 = threshold.resolve(failed_rows=99, total_rows=100)
        assert result1.level == "pass"

        result2 = threshold.resolve(failed_rows=100, total_rows=100)
        assert result2.level == "warning"

    def test_threshold_resolve_fraction_threshold(self):
        """Test threshold resolution with fraction threshold."""
        threshold = Threshold(warning=0.5)

        # 49% should pass
        result1 = threshold.resolve(failed_rows=49, total_rows=100)
        assert result1.level == "pass"

        # 50% should trigger warning
        result2 = threshold.resolve(failed_rows=50, total_rows=100)
        assert result2.level == "warning"

    def test_threshold_resolve_count_threshold(self):
        """Test threshold resolution with count threshold."""
        threshold = Threshold(warning=10)

        # 9 failures should pass
        result1 = threshold.resolve(failed_rows=9, total_rows=100)
        assert result1.level == "pass"

        # 10 failures should trigger warning
        result2 = threshold.resolve(failed_rows=10, total_rows=100)
        assert result2.level == "warning"

    def test_threshold_resolve_priority_order(self):
        """Test that higher severity levels take priority."""
        threshold = Threshold(warning=0.1, error=0.3, reject=0.5)

        # 40% failure rate should trigger error, not warning
        result = threshold.resolve(failed_rows=40, total_rows=100)
        assert result.level == "error"

        # 60% failure rate should trigger reject, not error
        result2 = threshold.resolve(failed_rows=60, total_rows=100)
        assert result2.level == "reject"


class TestThresholdEdgeCases:
    """Tests for edge cases in threshold configuration."""

    def test_threshold_mixed_fraction_and_count(self):
        """Test threshold with mix of fraction and count values across severity levels."""
        threshold = Threshold(
            warning=10,  # Count: 10 failures
            error=0.5,  # Fraction: 50%
            reject=100,  # Count: 100 failures
        )

        # 20 failures out of 100 = 20%
        result = threshold.resolve(failed_rows=20, total_rows=100)
        assert result.level == "warning"  # Count threshold (10) triggered

    def test_threshold_boundary_conditions(self):
        """Test threshold resolution at exact boundary values."""
        threshold = Threshold(warning=0.5)

        # Exactly 50% should trigger
        result = threshold.resolve(failed_rows=50, total_rows=100)
        assert result.level == "warning"

        # Just under 50% should not trigger
        result2 = threshold.resolve(failed_rows=49, total_rows=100)
        assert result2.level == "pass"


class TestThresholdTypeErrors:
    """Tests for threshold type errors."""

    def test_threshold_with_invalid_types(self):
        """Test that invalid types as threshold values raise error."""
        # List
        with pytest.raises(InvalidThresholdError):
            Threshold(warning=[0.5])  # type: ignore

        # Dict
        with pytest.raises(InvalidThresholdError):
            Threshold(warning={"value": 0.5})  # type: ignore

        # Arbitrary object
        with pytest.raises(InvalidThresholdError):
            Threshold(warning=object())  # type: ignore

        # String number (should be numeric)
        with pytest.raises(InvalidThresholdError):
            Threshold(warning="0.5")  # type: ignore


class TestThresholdInCheckConfigurations:
    """Tests for threshold configurations in validation checks."""

    def test_check_with_invalid_thresholds(self):
        """Test that checks properly reject invalid threshold values."""
        # Invalid warning threshold
        with pytest.raises(InvalidThresholdError):
            z.Check.not_empty(warning=-0.5)

        # Invalid error threshold
        with pytest.raises(InvalidThresholdError):
            z.Check.not_empty(error="invalid")  # type: ignore

    def test_check_with_valid_thresholds(self):
        """Test check with various valid threshold configurations."""
        # Multiple thresholds across severity levels
        check = z.Check.not_empty(debug=True, warning=0.1, error=0.5, reject="all")
        assert check is not None

        # Non-ordered thresholds (priority determines which triggers)
        check = z.Check.not_empty(
            warning=0.9,  # High warning
            error=0.1,  # Low error
            reject=0.5,  # Medium reject
        )
        assert check is not None


class TestThresholdConfigurationCombinations:
    """Tests for various threshold configuration combinations."""

    def test_threshold_level_combinations(self):
        """Test various combinations of threshold severity levels."""
        # Single level - debug only
        threshold = Threshold(debug=True)
        assert threshold.debug is True

        # Single level - reject only
        threshold = Threshold(reject="all")
        assert threshold.reject == "all"

        # Skip intermediate levels
        threshold = Threshold(error=0.5, reject="all")
        assert threshold.warning is None
        assert threshold.error == 0.5

        # All levels configured
        threshold = Threshold(debug=0.01, warning=0.1, error=0.3, reject=0.5)
        assert threshold.debug == 0.01
        assert threshold.warning == 0.1
        assert threshold.error == 0.3
        assert threshold.reject == 0.5
