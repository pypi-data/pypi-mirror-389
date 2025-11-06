"""
Unit tests for table-level validation checks.

Tests TableCheck variants: removed_rows, min_rows
"""

import polars as pl
import zeolite as z
from zeolite.types import ProcessingSuccess, ProcessingFailure


class TestRemovedRowsCheck:
    """Tests for removed_rows table validation."""

    def test_removed_rows_under_threshold(self):
        """Test passing when removed rows under threshold."""
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
                "age": [25, -5, 30, 35, 28, 22, 27, 33, 29, 24],  # 1 invalid (10%)
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
                    warning=0.3, error=0.5, reject=0.7
                ),  # 10% < 30%
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        # 1 row should be removed
        assert result.data.collect().shape[0] == 9

    def test_removed_rows_at_warning(self):
        """Test warning level triggered at threshold."""
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
                z.TableCheck.removed_rows(
                    warning=0.15, error=0.5, reject=0.7
                ),  # 20% > 15%
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        # Should succeed but have warning
        assert isinstance(result, ProcessingSuccess)
        assert len(result.errors) > 0
        # Check for warning about removed rows
        error_messages = [str(e).lower() for e in result.errors]
        assert any("removed" in msg or "row" in msg for msg in error_messages)

    def test_removed_rows_at_error(self):
        """Test error level triggered."""
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
                    warning=0.1, error=0.25, reject=0.7
                ),  # 30% > 25%
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        # Should succeed but have error
        assert isinstance(result, ProcessingSuccess)
        assert len(result.errors) > 0

    def test_removed_rows_at_reject(self):
        """Test reject level triggered."""
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
                "age": [25, -5, 30, -10, 35, -15, 28, -20, 27, 33],  # 4 invalid (40%)
            }
        )

        schema = (
            z.schema("test")
            .strict()
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
                    warning=0.1, error=0.2, reject=0.35
                ),  # 40% > 35%
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingFailure)
        assert result.failed_stage == "filter"

    def test_table_check_with_no_removals(self):
        """Test edge case when no rows are removed."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003", "004", "005"],
                "age": [25, 30, 35, 28, 22],  # All valid
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
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        # No rows removed
        assert result.data.collect().shape[0] == 5


class TestMinRowsCheck:
    """Tests for min_rows table validation."""

    def test_min_rows_pass(self):
        """Test passing when sufficient rows present."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003", "004", "005"],
                "name": ["A", "B", "C", "D", "E"],
            }
        )

        schema = (
            z.schema("test")
            .columns(
                z.col.str("id"),
                z.col.str("name"),
            )
            .table_validation(
                z.TableCheck.min_rows(reject=3),  # Need at least 3, have 5
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)

    def test_min_rows_fail(self):
        """Test rejection when too few rows."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002"],
                "name": ["A", "B"],
            }
        )

        schema = (
            z.schema("test")
            .strict()
            .columns(
                z.col.str("id"),
                z.col.str("name"),
            )
            .table_validation(
                z.TableCheck.min_rows(reject=5),  # Need 5, only have 2
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingFailure)
        assert result.failed_stage == "filter"

    def test_min_rows_warning_level(self):
        """Test warning when below warning threshold."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "name": ["A", "B", "C"],
            }
        )

        schema = (
            z.schema("test")
            .columns(
                z.col.str("id"),
                z.col.str("name"),
            )
            .table_validation(
                z.TableCheck.min_rows(warning=5, reject=1),  # Warning at 5, reject at 1
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        # Should succeed with warning
        assert isinstance(result, ProcessingSuccess)
        assert len(result.errors) > 0


class TestMultipleTableChecks:
    """Tests for combined table checks."""

    def test_multiple_table_checks(self):
        """Test multiple table validations together."""
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
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        # Should have 4 rows after removal (passes min_rows check)
        assert result.data.collect().shape[0] == 4
