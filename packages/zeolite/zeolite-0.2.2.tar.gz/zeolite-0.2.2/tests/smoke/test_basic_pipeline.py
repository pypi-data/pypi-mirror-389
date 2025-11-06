"""
Basic smoke tests for schema pipeline.

Tests that the pipeline works with simple, valid data and no transformations.
These are minimal sanity checks to ensure the pipeline doesn't crash.
"""

import polars as pl
import zeolite as z
from zeolite.types import ProcessingSuccess


class TestBasicPipeline:
    """Basic smoke tests for pipeline functionality."""

    def test_single_row_passthrough(self):
        """Test processing single row with no transformations."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001"],
                "name": ["Alice"],
                "age": [25],
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
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df.shape[0] == 1
        # Verify data integrity
        assert final_df["id"][0] == "001"
        assert final_df["name"][0] == "Alice"
        assert final_df["age"][0] == 25

    def test_multiple_rows_passthrough(self):
        """Test processing multiple rows with no transformations."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "category": ["A", "A", "A"],
                "value": [10, 20, 30],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("category"),
            z.col.int("value"),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df.shape[0] == 3
        # Verify data passes through unchanged
        assert final_df["id"].to_list() == ["001", "002", "003"]
        assert final_df["category"].to_list() == ["A", "A", "A"]
        assert final_df["value"].to_list() == [10, 20, 30]

    def test_multiple_datatypes_passthrough(self):
        """Test processing various data types with no transformations."""
        # Arrange
        df = pl.DataFrame(
            {
                "str_col": ["a", "b", "c"],
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "bool_col": [True, False, True],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("str_col"),
            z.col.int("int_col"),
            z.col.float("float_col"),
            z.col.bool("bool_col"),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df.shape[0] == 3
        # Verify all columns present
        assert "str_col" in final_df.columns
        assert "int_col" in final_df.columns
        assert "float_col" in final_df.columns
        assert "bool_col" in final_df.columns
