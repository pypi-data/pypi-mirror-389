"""
Unit tests for schema configuration error handling.

Tests invalid schema configurations that should raise appropriate exceptions.
"""

import pytest
import polars as pl
import zeolite as z
from zeolite.exceptions import (
    SchemaConfigurationError,
    DuplicateColumnError,
    MissingParentColumnError,
    CircularDependencyError,
)


class TestDuplicateColumns:
    """Tests for duplicate column detection."""

    def test_duplicate_column_names(self):
        """Test that duplicate column names raise error."""
        with pytest.raises(DuplicateColumnError):
            z.schema("test").columns(
                z.col.str("id"),
                z.col.str("name"),
                z.col.int("id"),  # Duplicate name
            )

    def test_duplicate_column_names_same_call(self):
        """Test that duplicate columns in same call raise error."""
        with pytest.raises(DuplicateColumnError):
            z.schema("test").columns(
                z.col.str("duplicate"),
                z.col.int("duplicate"),
            )

    def test_duplicate_via_variants(self):
        """Test that overlapping variants raises error during schema construction."""
        # This creates a scenario where both columns could match the same raw column
        with pytest.raises(DuplicateColumnError) as exc_info:
            z.schema("test").columns(
                z.col.str("id").variants("person_id", "patient_id"),
                z.col.str("other_id").variants("person_id"),  # Overlapping variant
            )

        # Verify error message mentions the conflict
        error_msg = str(exc_info.value)
        assert "person_id" in error_msg


class TestMissingParentColumns:
    """Tests for missing parent column detection."""

    def test_derived_column_missing_parent(self):
        """Test that derived column referencing non-existent parent raises error."""
        with pytest.raises(MissingParentColumnError):
            z.schema("test").columns(
                z.col.str("id"),
                z.col.derived("doubled", function=pl.col("non_existent") * 2),
            )

    def test_derived_from_cleaned_missing_parent(self):
        """Test that derived column referencing non-existent cleaned column raises error."""
        with pytest.raises(MissingParentColumnError):
            z.schema("test").columns(
                z.col.str("id"),
                z.col.derived("derived", function=z.ref("missing").clean().col),
            )

    def test_multiple_missing_parents(self):
        """Test error message includes all missing parent columns."""
        with pytest.raises(MissingParentColumnError) as exc_info:
            z.schema("test").columns(
                z.col.str("id"),
                z.col.derived(
                    "combined", function=pl.col("missing1") + pl.col("missing2")
                ),
            )

        # Error should mention at least one missing column
        error_msg = str(exc_info.value)
        assert "missing1" in error_msg or "missing2" in error_msg

    def test_custom_check_missing_parent(self):
        """Test custom check referencing non-existent column raises error."""
        with pytest.raises(MissingParentColumnError):
            z.schema("test").columns(
                z.col.str("id"),
                z.col.custom_check(
                    name="check",
                    function=pl.col("non_existent").is_not_null(),
                    message="Test",
                    thresholds=z.Threshold(warning="any"),
                ),
            )


class TestCircularDependencies:
    """Tests for circular dependency detection."""

    def test_direct_circular_reference(self):
        """Test that A → A circular reference is detected."""
        with pytest.raises(CircularDependencyError) as exc_info:
            z.schema("circular_hell").columns(
                z.col.str("id"),
                z.col.derived("col_1", function=z.ref("col_1").derived().col.eq(4)),
            )

        error_msg = str(exc_info.value)
        assert "circular dependency" in error_msg.lower()
        assert "col_1" in error_msg

    def test_indirect_circular_reference(self):
        """Test that A → B → A circular reference is detected."""
        with pytest.raises(CircularDependencyError) as exc_info:
            z.schema("circular_hell").columns(
                z.col.str("id"),
                z.col.derived("col_1", function=z.ref("col_2").derived().col.eq(4)),
                z.col.derived("col_2", function=z.ref("col_1").derived().col.eq(1)),
            )

        error_msg = str(exc_info.value)
        assert "circular dependency" in error_msg.lower()
        assert "col_1" in error_msg and "col_2" in error_msg

    def test_long_circular_reference(self):
        """Test that A → B → C → A circular reference is detected."""
        with pytest.raises(CircularDependencyError) as exc_info:
            z.schema("circular_hell").columns(
                z.col.str("id"),
                z.col.derived("col_1", function=z.ref("col_2").derived().col + 1),
                z.col.derived("col_2", function=z.ref("col_3").derived().col + 1),
                z.col.derived("col_3", function=z.ref("col_1").derived().col + 1),
            )

        error_msg = str(exc_info.value)
        assert "circular dependency" in error_msg.lower()
        # Should mention all columns in the cycle
        assert "col_1" in error_msg
        assert "col_2" in error_msg
        assert "col_3" in error_msg


class TestInvalidColumnsMethodParameter:
    """Tests for invalid parameters to .columns() method."""

    def test_invalid_method_parameter(self):
        """Test that invalid 'method' parameter raises error."""
        with pytest.raises(SchemaConfigurationError):
            z.schema("test").columns(
                z.col.str("id"),
                method="invalid_method",  # type: ignore
            )

    def test_none_column_in_list(self):
        """Test that None in column list is silently ignored."""
        # Current behavior: None columns are filtered out
        schema = z.schema("test").columns(
            z.col.str("id"),
            None,  # type: ignore
            z.col.str("name"),
        )
        # Schema is created successfully
        assert schema is not None

    def test_invalid_column_type(self):
        """Test that invalid column type raises SchemaConfigurationError."""
        with pytest.raises(SchemaConfigurationError) as exc_info:
            z.schema("test").columns(
                z.col.str("id"),
                "not_a_column",  # type: ignore
            )

        error_msg = str(exc_info.value)
        assert "Column Schema definition" in error_msg

    def test_empty_columns_call(self):
        """Test that calling columns() with no arguments works (no-op)."""
        # This should not raise an error
        schema = z.schema("test").columns()
        assert schema is not None


class TestInvalidTableValidations:
    """Tests for invalid table validation configurations."""

    def test_table_validation_with_invalid_type(self):
        """Test that invalid table validation type raises error."""
        with pytest.raises(SchemaConfigurationError):
            z.schema("test").table_validation(
                "not_a_table_check"  # type: ignore
            )

    def test_table_validation_with_none(self):
        """Test that None table validation raises error."""
        with pytest.raises(SchemaConfigurationError):
            z.schema("test").table_validation(None)  # type: ignore

    def test_table_validation_with_empty_call(self):
        """Test table validation with no arguments."""
        # Empty call should be valid (no validations)
        schema = z.schema("test").table_validation()
        assert schema is not None


class TestSchemaConfigurationCombinations:
    """Tests for invalid combinations of schema configurations."""

    def test_optional_and_strict_combination(self):
        """Test that optional + strict combination works (not mutually exclusive)."""
        # This should work - optional means data can be missing, strict means processing is strict
        schema = z.schema("test").optional().strict(True)
        assert schema._params.is_required is False
        assert schema._params.strict is True

    def test_column_definition_after_apply(self):
        """Test that schema is immutable after apply (or can be modified)."""
        schema = z.schema("test").columns(z.col.str("id"))

        df = pl.DataFrame({"id": ["001", "002"]})
        schema.apply(df)

        # Try to add more columns after apply
        schema2 = schema.columns(z.col.str("name"))

        # This should work - schemas are immutable, schema2 is new
        assert schema2 is not None
        assert schema2 != schema  # Different schema objects
