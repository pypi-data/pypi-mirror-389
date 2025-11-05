"""
Unit tests for validation stage (Stage 4).

Tests the step_4_validate_columns function which:
- Evaluates check columns against thresholds
- Generates validation errors at appropriate levels
- Does NOT remove rows (that's Stage 5)
"""

import polars as pl
import zeolite as z


class TestValidateEvaluatesChecks:
    """Tests for check column evaluation during validate stage."""

    def test_validate_evaluates_check_columns(self):
        """Test that validate stage evaluates all check columns."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": [25, 30, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(z.Check.not_empty(warning="any")),
            z.col.int("age").validations(
                z.Check.in_range(min_value=0, max_value=120, warning="any")
            ),
        )

        # Act - Run through all stages up to validate
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        # Validate should not reject since all data is valid
        assert validated.reject is False
        # All rows should still be present (validate doesn't remove rows)
        assert validated.data.collect().shape[0] == 3

    def test_validate_with_all_passing_checks(self):
        """Test validate stage when all checks pass."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": [25, 30, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(
                z.Check.not_empty(reject="any"), z.Check.unique(reject="any")
            ),
            z.col.int("age").validations(
                z.Check.in_range(min_value=0, max_value=120, reject="any")
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        assert validated.reject is False
        assert len(validated.errors) == 0  # No validation errors


class TestValidateThresholdTriggers:
    """Tests for threshold triggering during validate stage."""

    def test_validate_triggers_warning_level(self):
        """Test that warning-level validations are detected."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "002", "003"],  # 1 duplicate (25%)
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(
                z.Check.unique(warning=0.2, error=0.5, reject=0.8)  # 25% > 20% warning
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        # Should have warning but not reject
        assert validated.reject is False
        assert len(validated.errors) > 0
        # Errors are present (level details may be internal)

    def test_validate_triggers_error_level(self):
        """Test that error-level validations are detected."""
        # Arrange
        df = pl.DataFrame(
            {
                "age": [25, -5, 30, -10, 35],  # 2 invalid (40%)
            }
        )

        schema = z.schema("test").columns(
            z.col.int("age").validations(
                z.Check.in_range(
                    min_value=0, max_value=120, warning=0.1, error=0.3, reject=0.6
                )  # 40% > 30% error
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        # Should have error but not reject (40% < 60% reject)
        assert validated.reject is False
        assert len(validated.errors) > 0

    def test_validate_triggers_reject_level(self):
        """Test that reject-level validations cause rejection."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", None, "002", None, "003"],  # 2 null (40%)
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(
                z.Check.not_empty(
                    warning=0.1, error=0.2, reject=0.3
                )  # 40% > 30% reject
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        # Should trigger reject
        assert validated.reject is True
        assert len(validated.errors) > 0


class TestValidateMultipleChecks:
    """Tests for multiple validation checks on same column."""

    def test_validate_multiple_checks_same_column(self):
        """Test that multiple checks on same column are all evaluated."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "002", None],  # Both duplicate and null
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(
                z.Check.not_empty(warning="any"),
                z.Check.unique(warning="any"),
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        # Should have errors for both checks
        assert len(validated.errors) >= 2

    def test_validate_checks_on_cleaned_column(self):
        """Test that checks can run on cleaned columns."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["P001", "P002", "P002"],  # Duplicate after prefix
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id")
            .clean(z.Clean.id(prefix="ORG"))
            .validations(
                z.Check.unique(check_on_cleaned=True, reject="any")  # Check on cleaned
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        # Should detect duplicates in cleaned column
        assert validated.reject is True
        assert len(validated.errors) > 0


class TestValidateReturnsErrors:
    """Tests for validation error collection."""

    def test_validate_returns_errors_list(self):
        """Test that validate stage returns list of errors."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "002"],
                "age": [25, 150, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(z.Check.unique(warning="any")),
            z.col.int("age").validations(
                z.Check.in_range(min_value=0, max_value=120, warning="any")
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        assert isinstance(validated.errors, list)
        assert len(validated.errors) > 0

    def test_validate_error_messages_descriptive(self):
        """Test that validation errors have descriptive messages."""
        # Arrange
        df = pl.DataFrame(
            {
                "age": [25, -5, 30],
            }
        )

        schema = z.schema("test").columns(
            z.col.int("age").validations(
                z.Check.in_range(min_value=0, max_value=120, warning="any")
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        assert len(validated.errors) > 0
        error_msg = str(validated.errors[0])
        # Error should mention the column name
        assert "age" in error_msg.lower()


class TestValidateWithNoFailures:
    """Tests for validate stage with no validation failures."""

    def test_validate_with_no_failures(self):
        """Test validate stage when all validations pass."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(z.Check.not_empty(), z.Check.unique()),
            z.col.str("name").validations(z.Check.not_empty()),
            z.col.int("age").validations(z.Check.in_range(min_value=0, max_value=120)),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        assert validated.reject is False
        assert len(validated.errors) == 0
        # All rows still present
        assert validated.data.collect().shape[0] == 3


class TestValidateDoesNotRemoveRows:
    """Tests that validate stage does NOT remove rows."""

    def test_validate_does_not_remove_rows(self):
        """Test that validate stage keeps all rows even with failures."""
        # Arrange
        df = pl.DataFrame(
            {
                "age": [25, -5, 30, -10, 35],  # 2 invalid
            }
        )

        schema = z.schema("test").columns(
            z.col.int("age").validations(
                z.Check.in_range(
                    min_value=0,
                    max_value=120,
                    warning="any",
                    remove_row_on_fail=True,  # Even with this flag
                )
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)

        # Assert
        # Validate stage should NOT remove rows (that's Stage 5)
        assert validated.data.collect().shape[0] == 5
        # Should have generated errors for validation failures
        assert len(validated.errors) > 0
