"""
Edge case tests for unusual scenarios.

Tests edge cases: empty data, all nulls, circular dependencies, etc.
"""

import polars as pl
import zeolite as z
from zeolite.types import ProcessingSuccess, ProcessingFailure


class TestEmptyData:
    """Tests for empty DataFrames."""

    def test_empty_dataframe(self):
        """Test processing completely empty DataFrame."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": [],
                "name": [],
                "age": [],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),
            z.col.int("age"),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # Empty data should trigger rejection
        assert isinstance(result, ProcessingFailure)
        assert result.failed_stage == "normalise"


class TestSingleRowEdgeCases:
    """Tests for edge cases with single-row datasets."""

    def test_single_row_with_validation_failure(self):
        """Test that validations work correctly with only one row (100% failure rate)."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001"],
                "age": [150],  # Invalid age
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("age").validations(
                z.Check.in_range(min_value=0, max_value=120, reject=0.5)
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # 100% failure rate should trigger rejection
        assert isinstance(result, ProcessingFailure)

    def test_single_row_with_cleaning(self):
        """Test that cleaning operations work correctly with single row."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["P001"],
                "name": ["  ALICE  "],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").clean(z.Clean.id(prefix="ORG")),
            z.col.str("name").clean(z.Clean.string(sanitise="full")),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df["id"][0] == "ORG::P001"
        assert final_df["name"][0] == "alice"

    def test_single_row_with_derived_column(self):
        """Test derived columns work with single row."""
        # Arrange
        df = pl.DataFrame(
            {
                "price": [100],
                "quantity": [2],
            }
        )

        schema = z.schema("test").columns(
            z.col.int("price"),
            z.col.int("quantity"),
            z.col.derived("total", function=pl.col("price") * pl.col("quantity")),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df["total"][0] == 200


class TestRepeatedValuesEdgeCases:
    """Tests for edge cases with repeated/identical values."""

    def test_all_duplicate_ids_with_unique_check(self):
        """Test unique validation on column with all identical values."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "001", "001"],  # All duplicates
                "name": ["Alice", "Bob", "Charlie"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(z.Check.unique(reject="any")),
            z.col.str("name"),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # Should reject due to duplicate IDs
        assert isinstance(result, ProcessingFailure)

    def test_all_same_values_with_cleaning(self):
        """Test cleaning operations on column with all identical values."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "status": ["ACTIVE", "ACTIVE", "ACTIVE"],  # All same
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("status").clean(z.Clean.string(sanitise="lowercase")),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # All values should be cleaned to lowercase
        assert all(status == "active" for status in final_df["status"])

    def test_zero_variance_column_with_validation(self):
        """Test validations work on column with zero variance (all same value)."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "score": [50, 50, 50],  # All same, all valid
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("score").validations(
                z.Check.in_range(min_value=0, max_value=100, warning=0.1)
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # All values should pass validation
        assert all(score == 50 for score in final_df["score"])


class TestAllNulls:
    """Tests for columns with all null values."""

    def test_all_nulls_dataframe(self):
        """Test DataFrame with all null values."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": [None, None, None],
                "name": [None, None, None],
                "age": [None, None, None],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").optional(),
            z.col.str("name").optional(),
            z.col.int("age").optional(),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # All nulls should be treated as empty data
        assert isinstance(result, ProcessingFailure)

    def test_single_column_all_nulls(self):
        """Test single column with all nulls."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "name": [None, None, None],
                "age": [25, 30, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name").optional(),
            z.col.int("age"),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)


class TestAllDuplicates:
    """Tests for duplicate values."""

    def test_all_duplicates_dataframe(self):
        """Test DataFrame with all duplicate rows."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "001", "001", "001"],
                "name": ["Alice", "Alice", "Alice", "Alice"],
                "age": [25, 25, 25, 25],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(z.Check.unique(reject="any")),
            z.col.str("name"),
            z.col.int("age"),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # All duplicates should trigger rejection
        assert isinstance(result, ProcessingFailure)


class TestValidationFailures:
    """Tests for extreme validation failure scenarios."""

    def test_100_percent_validation_failures(self):
        """Test when all rows fail validation."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003", "004"],
                "age": [-5, -10, -15, -20],  # All invalid
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("age").validations(
                z.Check.in_range(min_value=0, max_value=120, reject=0.5)
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # 100% failure should trigger rejection
        assert isinstance(result, ProcessingFailure)


class TestInvalidConfigurations:
    """Tests for invalid schema configurations."""

    def test_missing_required_columns(self):
        """Test schema with required columns missing from data."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),  # Required but missing
            z.col.int("age"),  # Required but missing
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingFailure)
        assert result.failed_stage == "normalise"


class TestSpecialCharacters:
    """Tests for special characters in data."""

    def test_unicode_characters(self):
        """Test handling unicode characters."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "name": ["Müller", "François", "北京"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df["name"][0] == "Müller"
        assert final_df["name"][1] == "François"
        assert final_df["name"][2] == "北京"

    def test_special_characters_in_strings(self):
        """Test special characters like quotes, newlines."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "text": [
                    "Line1\nLine2",
                    "Text with 'quotes'",
                    'Text with "double quotes"',
                ],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("text"),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)


class TestMixedTypes:
    """Tests for mixed data types in columns."""

    def test_mixed_types_with_coercion(self):
        """Test mixed types that can be coerced."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "value": ["123", "456", "789"],  # Strings that look like numbers
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("value", coerce="strict"),  # Expects int, will coerce
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df["value"].dtype == pl.Int64
