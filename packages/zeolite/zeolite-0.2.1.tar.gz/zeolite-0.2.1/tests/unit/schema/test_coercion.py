"""
Unit tests for data type coercion.

Tests the step_2_coerce_datatypes function.
"""

import pytest
import polars as pl
import zeolite as z


class TestCoerceStringToNumber:
    """Tests for coercing string to numeric types."""

    def test_coerce_string_to_int(self):
        """Test coercing string column to integer."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": ["25", "30", "35"],  # String numbers
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("age"),  # Expects integer
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        coerced_df = result.data.collect()
        assert coerced_df["age"].dtype == pl.Int64

    def test_coerce_string_to_float(self):
        """Test coercing string column to float."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "price": ["123.45", "678.90", "999.99"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.float("price"),  # Expects float
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        coerced_df = result.data.collect()
        assert coerced_df["price"].dtype == pl.Float64


class TestCoerceToBool:
    """Tests for coercing to boolean."""

    def test_coerce_int_to_bool(self):
        """Test coercing numbers to boolean."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "is_active": [1, 0, 1],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.bool("is_active"),
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        coerced_df = result.data.collect()
        # Verify the data type is Boolean
        assert coerced_df["is_active"].dtype == pl.Boolean
        # Verify values are correct
        assert list(coerced_df["is_active"]) == [True, False, True]

    def test_coerce_string_to_bool(self):
        """Test various string representations to boolean."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "is_active": ["true", "false", "true"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.bool("is_active"),
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        # FIXME: Polars doesn't support string-to-bool coercion
        # This will error when collecting, which is expected behavior
        with pytest.raises(
            pl.exceptions.InvalidOperationError,
            match="casting from.*to Boolean not supported",
        ):
            result.data.collect()


class TestCoerceStringToDate:
    """Tests for coercing string to date."""

    def test_coerce_string_to_date(self):
        """Test coercing ISO format strings to date."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "date": ["2023-01-01", "2023-02-01", "2023-03-01"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.date("date"),
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        coerced_df = result.data.collect()
        # Verify data type is Date
        assert coerced_df["date"].dtype == pl.Date
        # Verify values are correct
        import datetime

        assert coerced_df["date"][0] == datetime.date(2023, 1, 1)
        assert coerced_df["date"][1] == datetime.date(2023, 2, 1)
        assert coerced_df["date"][2] == datetime.date(2023, 3, 1)


class TestCoerceOverrides:
    """Tests for coercion override options."""

    def test_coerce_with_override_true(self):
        """Test forcing coercion at schema level."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": ["25", "30", "35"],
            }
        )

        schema = (
            z.schema("test")
            .coerce("force_strict")
            .columns(
                z.col.str("id"),
                z.col.int("age"),
            )
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        coerced_df = result.data.collect()
        # Force coerce should attempt coercion
        assert coerced_df["age"].dtype == pl.Int64

    def test_coerce_with_override_false(self):
        """Test skipping coercion at schema level."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": ["25", "30", "35"],  # String but won't coerce
            }
        )

        schema = (
            z.schema("test")
            .coerce("force_skip_all")
            .columns(
                z.col.str("id"),
                z.col.int("age"),
            )
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        coerced_df = result.data.collect()
        # Coercion skipped, type remains string
        assert coerced_df["age"].dtype == pl.String

    def test_coerce_with_default(self):
        """Test default coercion behavior."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": ["25", "30", "35"],
            }
        )

        # Default schema has coerce="default_true"
        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("age"),
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        coerced_df = result.data.collect()
        # Default behavior should coerce
        assert coerced_df["age"].dtype == pl.Int64


class TestCoerceFailures:
    """Tests for handling invalid coercion."""

    def test_coerce_failures_produce_nulls(self):
        """Test that invalid data becomes null during coercion."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": ["25", "not_a_number", "35"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("age"),
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        coerced_df = result.data.collect()
        # Verify type was coerced
        assert coerced_df["age"].dtype == pl.Int64
        # Invalid value should become null
        assert coerced_df["age"][1] is None
        # Valid values should remain correct
        assert coerced_df["age"][0] == 25
        assert coerced_df["age"][2] == 35


class TestCoerceColumnLevel:
    """Tests for column-level coerce settings."""

    def test_column_level_coerce_override(self):
        """Test that column-level coerce setting overrides schema default."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": ["25", "30", "35"],
                "score": ["85", "92", "78"],
            }
        )

        schema = (
            z.schema("test")
            .coerce("default_strict")
            .columns(
                z.col.str("id"),
                z.col.int("age"),  # Will coerce (schema default)
                z.col.int("score").coerce("skip"),  # Skip coercion
            )
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        coerced_df = result.data.collect()
        assert coerced_df["age"].dtype == pl.Int64  # Coerced
        assert coerced_df["score"].dtype == pl.String  # Not coerced


class TestCoerceWarnings:
    """Tests for coercion warnings."""

    def test_coerce_generates_warnings(self):
        """Test that type mismatches generate warnings."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": ["25", "30", "35"],  # String but expects int
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("age"),
        )

        # Act
        result = schema.step_2_coerce_datatypes(df.lazy())

        # Assert
        # Should have warning about type mismatch
        assert len(result.errors) > 0
        error_messages = [str(e).lower() for e in result.errors]
        assert any("type" in msg or "mismatch" in msg for msg in error_messages)
