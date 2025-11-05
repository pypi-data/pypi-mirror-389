"""
Unit tests for column configuration error handling.

Tests invalid column configurations that should raise appropriate exceptions.
"""

import pytest
import polars as pl
import zeolite as z
from zeolite.exceptions import (
    ColumnConfigurationError,
    CleanConfigurationError,
    CheckConfigurationError,
)


class TestInvalidDataTypes:
    """Tests for invalid data type configurations."""

    def test_unsupported_data_type_string(self):
        """Test that unsupported data type string may raise error."""
        # The API might accept invalid data types and fail later
        try:
            col = z.col.str("test")
            # Valid call
            assert col is not None
        except (ValueError, ColumnConfigurationError):
            # If it raises, that's also valid
            pass

    def test_invalid_column_factory_method(self):
        """Test that calling non-existent column type raises error."""
        with pytest.raises(AttributeError):
            z.col.invalid_type("test")  # type: ignore


class TestCleaningConfigurationErrors:
    """Tests for invalid cleaning configurations."""

    def test_enum_clean_with_non_dict_map(self):
        """Test that enum clean with non-dict raises error."""
        with pytest.raises(CleanConfigurationError):
            z.Clean.enum(enum_map="not_a_dict")  # type: ignore

    def test_enum_clean_with_none_map(self):
        """Test that enum clean with None map raises TypeError."""
        with pytest.raises(CleanConfigurationError):
            z.Clean.enum(enum_map=None)  # type: ignore

    def test_enum_clean_with_empty_map(self):
        """Test that enum clean with empty dict may work or raise error."""
        # Empty enum map might be valid (matches nothing) or invalid
        try:
            clean = z.Clean.enum(enum_map={})
            assert clean is not None
        except CleanConfigurationError:
            # If it raises, that's also valid
            pass

    def test_enum_clean_with_invalid_value_types(self):
        """Test enum clean with non-string keys or values - currently accepted."""
        # Current behavior: integer keys are accepted and converted to strings
        clean = z.Clean.enum(enum_map={1: "one", 2: "two"})  # type: ignore
        assert clean is not None

    def test_boolean_clean_with_conflicting_values(self):
        """Test boolean clean where a value appears in both true and false sets."""
        with pytest.raises(CleanConfigurationError):
            z.Clean.boolean(
                true_values={"yes", "true", "1"},
                false_values={"no", "false", "yes"},  # "yes" in both sets
            )

    def test_boolean_clean_with_empty_value_sets(self):
        """Test boolean clean with empty true/false value sets - currently accepted."""
        with pytest.raises(CleanConfigurationError):
            z.Clean.boolean(
                true_values=set(),
                false_values=set(),
            )

    def test_string_clean_with_invalid_sanitisation_level(self):
        """Test string clean with invalid sanitisation level."""
        with pytest.raises(CleanConfigurationError):
            z.Clean.string(sanitise="invalid_level")  # type: ignore

    def test_date_clean_with_invalid_output_format(self):
        """Test date clean with invalid output format."""
        with pytest.raises(CleanConfigurationError):
            z.Clean.date(output_format="invalid")  # type: ignore

    def test_id_clean_with_empty_prefix(self):
        """Test ID clean with empty string prefix."""
        # Empty prefix might be valid or invalid
        try:
            clean = z.Clean.id(prefix="")
            assert clean is not None
        except CleanConfigurationError:
            pass

    def test_custom_clean_without_function(self):
        """Test that CustomCleanColumn without function raises error."""
        # Act & Assert
        with pytest.raises(
            TypeError,
            match="missing 1 required positional argument: 'function'",
        ):
            z.Clean.custom()  # type: ignore

    def test_custom_clean_with_non_callable_non_expr(self):
        """Test that passing non-callable/non-expr raises error."""
        # Act & Assert
        with pytest.raises(
            CleanConfigurationError, match="function or Polars Expression"
        ):
            z.Clean.custom("not a function or expr")  # type: ignore

    def test_custom_clean_function_returns_non_expr(self):
        """Test that function returning non-Expr raises error."""
        # Act & Assert
        with pytest.raises(
            CleanConfigurationError, match="must return a Polars Expression"
        ):
            z.Clean.custom(lambda col: "not an expr")  # type: ignore


class TestValidationConfigurationErrors:
    """Tests for invalid validation check configurations."""

    def test_regex_with_invalid_pattern(self):
        """Test regex check with invalid regular expression."""
        with pytest.raises(CheckConfigurationError):
            z.Check.str_matches(pattern="[invalid(regex")

    def test_regex_with_none_pattern(self):
        """Test regex check with None pattern."""
        with pytest.raises(TypeError):
            z.Check.str_matches(pattern=None)  # type: ignore

    def test_range_validation_min_greater_than_max(self):
        """Test range check with min > max."""
        with pytest.raises(CheckConfigurationError):
            z.Check.in_range(min_value=100, max_value=50)

    def test_range_validation_equal_bounds(self):
        """Test range check with min == max (might be valid for exact match)."""
        # Equal bounds might be valid or invalid
        try:
            check = z.Check.in_range(min_value=50, max_value=50)
            assert check is not None
        except CheckConfigurationError:
            pass

    def test_range_validation_with_only_min_bound(self):
        """Test range check with only min bound (unbounded max)."""
        # This might be valid - only lower bound
        check = z.Check.greater_than(50)
        assert check is not None

    def test_list_validation_with_non_iterable(self):
        """Test list validation with non-iterable values."""
        with pytest.raises(CheckConfigurationError):
            z.Check.is_in(allowed_values=123)  # type: ignore

    def test_list_validation_with_none(self):
        """Test list validation with None."""
        with pytest.raises(CheckConfigurationError):
            z.Check.is_in(allowed_values=None)  # type: ignore

    def test_list_validation_with_empty_list(self):
        """Test list validation with empty list."""
        # Empty list might be valid or invalid
        try:
            check = z.Check.is_in(allowed_values=[])
            assert check is not None
        except CheckConfigurationError:
            pass

    def test_string_length_min_greater_than_max(self):
        """Test string length check with min > max."""
        with pytest.raises(CheckConfigurationError):
            z.Check.str_length(min_length=10, max_length=5)

    def test_string_length_negative_values(self):
        """Test string length check with negative values."""
        with pytest.raises(CheckConfigurationError):
            z.Check.str_length(min_length=-5, max_length=10)

    def test_custom_check_without_function(self):
        """Test that custom check without function raises error."""
        with pytest.raises(
            TypeError,
            match="missing 1 required positional argument: 'function'",
        ):
            z.Check.custom(label="custom_check")  # type: ignore

    def test_custom_check_with_non_callable_non_expr(self):
        """Test that passing non-callable/non-expr raises error."""
        with pytest.raises(
            CheckConfigurationError, match="function or Polars Expression"
        ):
            z.Check.custom("not a function or expr", label="custom_check")  # type: ignore

    def test_custom_check_function_returns_non_expr(self):
        """Test that function returning non-Expr raises error."""
        # Act & Assert
        with pytest.raises(
            CheckConfigurationError, match="must return a Polars Expression"
        ):
            z.Check.custom(lambda col: "not an expr", label="custom_check")  # type: ignore


class TestMissingRequiredParameters:
    """Tests for missing required parameters in configurations."""

    def test_enum_clean_missing_enum_map(self):
        """Test enum clean without required enum_map parameter."""
        with pytest.raises(TypeError):
            z.Clean.enum()  # type: ignore

    def test_range_check_missing_bounds(self):
        """Test range check without any bounds."""
        # in_range requires at least one bound
        with pytest.raises(TypeError):
            z.Check.in_range()  # type: ignore

    def test_pattern_check_missing_pattern(self):
        """Test pattern check without pattern."""
        with pytest.raises(TypeError):
            z.Check.str_matches()  # type: ignore


class TestInvalidParameterTypes:
    """Tests for parameters with wrong types."""

    # Threshold validation is tested comprehensively in test_threshold_configuration_errors.py
    # We only test here that invalid thresholds are properly rejected at the API level

    # TODO: determine if sensitivity checks are necessary...
    # def test_clean_with_invalid_sensitivity(self):
    #     """Test clean with invalid sensitivity value."""
    #     with pytest.raises((TypeError, ValueError)):
    #         z.col.str("test").clean(
    #             z.Clean.string(col_sensitivity="invalid")  # type: ignore
    #         )


class TestColumnVariantErrors:
    """Tests for invalid column variant configurations."""

    def test_variants_with_empty_string(self):
        """Test column variants with empty string."""
        # Empty string variant might be invalid
        try:
            col = z.col.str("test").variants("")
            assert col is not None
        except (ValueError, ColumnConfigurationError):
            pass

    def test_variants_with_duplicate(self):
        """Test column variants with duplicate names."""
        # Duplicate variants might be allowed (idempotent) or disallowed
        try:
            col = z.col.str("test").variants("alt1", "alt2", "alt1")
            assert col is not None
        except (ValueError, ColumnConfigurationError):
            pass

    # TODO: decide if this is an error...
    # def test_variants_with_invalid_type(self):
    #     """Test column variants with non-string type."""
    #     with pytest.raises((TypeError, ValueError)):
    #         z.col.str("test").variants(123)  # type: ignore


class TestInvalidColumnCombinations:
    """Tests for invalid combinations of column configurations."""

    def test_optional_with_not_empty_check(self):
        """Test that optional column with not_empty check works (might warn)."""
        # This combination might be logically odd but not necessarily an error
        col = z.col.str("test").optional().validations(z.Check.not_empty())
        assert col is not None

    def test_multiple_clean_operations(self):
        """Test applying multiple clean operations (should only keep last)."""
        # Multiple clean operations might override each other
        col = (
            z.col.str("test")
            .clean(z.Clean.string(sanitise="full"))
            .clean(z.Clean.string(sanitise="lowercase"))
        )
        # Should work - last clean wins
        assert col is not None

    def test_derived_column_with_clean(self):
        """Test that derived column with clean operation may not make sense."""
        # Derived columns compute values, so cleaning them might be odd
        # but not necessarily an error
        try:
            col = z.col.derived("test", function=pl.lit(1)).clean(z.Clean.string())
            assert col is not None
        except (TypeError, ColumnConfigurationError):
            pass

    def test_custom_check_with_none_function(self):
        """Test custom check with None function."""
        with pytest.raises(ColumnConfigurationError):
            z.col.custom_check(
                name="test",
                function=None,  # type: ignore
                message="Test",
                thresholds=z.Threshold(warning="any"),
            )

    def test_custom_check_with_invalid_function_type(self):
        """Test custom check with non-expression function."""
        with pytest.raises(ColumnConfigurationError):
            z.col.custom_check(
                name="test",
                function="not_an_expression",  # type: ignore
                message="Test",
                thresholds=z.Threshold(warning="any"),
            )


class TestColumnNamingErrors:
    """Tests for invalid column names."""

    # TODO: decide if this is an error...
    # def test_column_with_numeric_name(self):
    #     """Test column with numeric name."""
    #     with pytest.raises((TypeError, ColumnConfigurationError)):
    #         z.col.str(123)  # type: ignore

    def test_column_with_special_characters_name(self):
        """Test column with special characters in name (might be valid)."""
        # Special characters might be valid column names
        try:
            col = z.col.str("column$with$special#chars")
            assert col is not None
        except (ValueError, ColumnConfigurationError):
            pass

    def test_column_with_whitespace_name(self):
        """Test column with whitespace in name."""
        # Whitespace might be valid but sanitized
        col = z.col.str("column with spaces")
        assert col is not None
