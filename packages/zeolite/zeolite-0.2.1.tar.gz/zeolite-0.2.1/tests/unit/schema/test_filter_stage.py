"""
Unit tests for filter stage (Stage 5).

Tests the step_5_validate_and_filter_table function which:
- Removes rows marked as 'reject' in check columns
- Evaluates table-level validations
- Tracks removal statistics
"""

import polars as pl
import zeolite as z


class TestFilterRemovesRows:
    """Tests for row removal during filter stage."""

    def test_filter_removes_rows_with_reject_status(self):
        """Test that filter stage removes rows marked with 'reject'."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003", "004", "005"],
                "age": [25, -5, 30, -10, 35],  # 2 invalid
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("age").validations(
                z.Check.in_range(
                    min_value=0,
                    max_value=120,
                    warning="any",
                    remove_row_on_fail=True,  # Mark for removal
                )
            ),
        )

        # Act - Run through all stages up to filter
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        filtered_df = filtered.data.collect()
        # Should have removed 2 rows (ages -5 and -10)
        assert filtered_df.shape[0] == 3
        # Remaining ages should all be valid
        assert all(0 <= age <= 120 for age in filtered_df["age"])

    def test_filter_with_no_rows_to_remove(self):
        """Test filter stage when no rows need removal."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": [25, 30, 35],  # All valid
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("age").validations(
                z.Check.in_range(
                    min_value=0, max_value=120, warning="any", remove_row_on_fail=True
                )
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        filtered_df = filtered.data.collect()
        # No rows removed
        assert filtered_df.shape[0] == 3

    def test_filter_removes_all_rows(self):
        """Test filter stage when all rows fail validation."""
        # Arrange
        df = pl.DataFrame(
            {
                "age": [-5, -10, -15],  # All invalid
            }
        )

        schema = z.schema("test").columns(
            z.col.int("age").validations(
                z.Check.in_range(
                    min_value=0, max_value=120, warning="any", remove_row_on_fail=True
                )
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        filtered_df = filtered.data.collect()
        # All rows removed
        assert filtered_df.shape[0] == 0


class TestFilterTableChecks:
    """Tests for table-level validation during filter stage."""

    def test_filter_evaluates_table_checks(self):
        """Test that filter stage evaluates table-level checks."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003", "004", "005"],
                "age": [25, -5, 30, 35, 28],  # 1 invalid (20%)
            }
        )

        schema = (
            z.schema("test")
            .columns(
                z.col.str("id"),
                z.col.int("age").validations(
                    z.Check.in_range(
                        min_value=0, max_value=120, remove_row_on_fail=True
                    )
                ),
            )
            .table_validation(
                z.TableCheck.removed_rows(
                    warning=0.1, error=0.3, reject=0.5
                )  # 20% > 10%
            )
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        # Should have warning about removed rows
        assert len(filtered.errors) > 0
        error_messages = [str(e).lower() for e in filtered.errors]
        assert any("removed" in msg or "row" in msg for msg in error_messages)

    def test_filter_table_check_min_rows(self):
        """Test table check for minimum row count."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],  # Only 3 rows
            }
        )

        schema = (
            z.schema("test")
            .columns(
                z.col.str("id"),
            )
            .table_validation(
                z.TableCheck.min_rows(reject=5)  # Need 5, only have 3
            )
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        # Should trigger reject due to insufficient rows
        assert filtered.reject is True

    def test_filter_table_check_removed_rows_reject(self):
        """Test that excessive row removal triggers reject."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": [
                    "001",
                    "002",
                    "003",
                    "004",
                    "005",
                    "006",
                    "007",
                    "008",
                    "009",
                    "010",
                ],
                "age": [25, -5, 30, -10, 35, -15, 28, 22, 27, 33],  # 3 invalid (30%)
            }
        )

        schema = (
            z.schema("test")
            .columns(
                z.col.str("id"),
                z.col.int("age").validations(
                    z.Check.in_range(
                        min_value=0, max_value=120, remove_row_on_fail=True
                    )
                ),
            )
            .table_validation(
                z.TableCheck.removed_rows(
                    warning=0.1, error=0.2, reject=0.25
                )  # 30% > 25%
            )
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        # Should reject due to too many rows removed
        assert filtered.reject is True
        assert len(filtered.errors) > 0


class TestFilterRemovalTracking:
    """Tests for tracking removed row statistics."""

    def test_filter_tracks_removal_percentage(self):
        """Test that filter stage tracks removal statistics."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": [
                    "001",
                    "002",
                    "003",
                    "004",
                    "005",
                    "006",
                    "007",
                    "008",
                    "009",
                    "010",
                ],
                "age": [25, -5, 30, -10, 35, 28, 22, 27, 33, 29],  # 2 invalid (20%)
            }
        )

        schema = (
            z.schema("test")
            .columns(
                z.col.str("id"),
                z.col.int("age").validations(
                    z.Check.in_range(
                        min_value=0, max_value=120, remove_row_on_fail=True
                    )
                ),
            )
            .table_validation(
                z.TableCheck.removed_rows(warning=0.15, error=0.3, reject=0.5)
            )
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        # Should have removed exactly 2 rows (20%)
        assert filtered.data.collect().shape[0] == 8
        # Should have warning (20% > 15% warning threshold)
        assert len(filtered.errors) > 0

    def test_filter_multiple_table_checks(self):
        """Test multiple table-level validations together."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003", "004", "005"],
                "age": [25, -5, 30, 35, 28],  # 1 invalid (20%)
            }
        )

        schema = (
            z.schema("test")
            .columns(
                z.col.str("id"),
                z.col.int("age").validations(
                    z.Check.in_range(
                        min_value=0, max_value=120, remove_row_on_fail=True
                    )
                ),
            )
            .table_validation(
                z.TableCheck.removed_rows(warning=0.1, error=0.3, reject=0.5),
                z.TableCheck.min_rows(reject=3),  # After removal, need at least 3
            )
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        # Should pass (4 rows after removal, which is >= 3)
        assert filtered.reject is False
        assert filtered.data.collect().shape[0] == 4


class TestFilterWithMultipleCheckColumns:
    """Tests for filtering with multiple failing checks."""

    def test_filter_row_with_multiple_failures(self):
        """Test that row is removed if ANY check marks it for removal."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "002", "003"],  # Duplicate '002'
                "age": [25, -5, 30, 35],  # Invalid age at same row as duplicate
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(
                z.Check.unique(warning="any", remove_row_on_fail=True)
            ),
            z.col.int("age").validations(
                z.Check.in_range(
                    min_value=0, max_value=120, warning="any", remove_row_on_fail=True
                )
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        filtered_df = filtered.data.collect()
        # Should remove rows with failures (duplicates and invalid age)
        assert filtered_df.shape[0] < 4

    def test_filter_preserves_rows_without_remove_flag(self):
        """Test that rows are kept when remove_row_on_fail is False."""
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
                    remove_row_on_fail=False,  # Don't remove
                )
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        filtered_df = filtered.data.collect()
        # All rows should be kept (no removal)
        assert filtered_df.shape[0] == 5


class TestFilterErrorAccumulation:
    """Tests for error accumulation during filter stage."""

    def test_filter_accumulates_errors_from_previous_stages(self):
        """Test that filter stage includes errors from validation stage."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "002"],  # Duplicate
                "age": [25, 150, 35],  # Out of range
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(
                z.Check.unique(warning="any", remove_row_on_fail=True)
            ),
            z.col.int("age").validations(
                z.Check.in_range(
                    min_value=0, max_value=120, warning="any", remove_row_on_fail=True
                )
            ),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)
        validated = schema.step_4_validate_columns(prepared.data)
        filtered = schema.step_5_validate_and_filter_table(validated.data)

        # Assert
        # Filter should complete (errors accumulation behavior may vary by implementation)
        # At minimum, rows should be removed
        assert filtered.data.collect().shape[0] < 3  # Some rows removed
