"""
Performance tests for large datasets.

Tests processing performance with large datasets.
"""

import polars as pl
import zeolite as z
from zeolite.types import ProcessingSuccess


class TestLargeDatasets:
    """Tests for performance with large datasets."""

    def test_100k_rows_simple_schema(self):
        """Test processing 100k rows with simple schema."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": [f"ID_{i:06d}" for i in range(100000)],
                "value": list(range(100000)),
                "category": [f"cat_{i % 10}" for i in range(100000)],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(z.Check.not_empty(), z.Check.unique()),
            z.col.int("value"),
            z.col.str("category"),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        assert result.data.collect().shape[0] == 100000

    def test_wide_dataset_100_columns(self):
        """Test processing dataset with many columns."""
        # Arrange
        data = {f"col_{i}": list(range(1000)) for i in range(100)}
        df = pl.DataFrame(data)

        columns = [z.col.int(f"col_{i}") for i in range(100)]
        schema = z.schema("test").columns(*columns)

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        assert result.data.collect().shape == (1000, 100)

    def test_complex_derived_chains(self):
        """Test performance with deep dependency trees."""
        # Arrange
        df = pl.DataFrame(
            {
                "base": list(range(10000)),
            }
        )

        schema = z.schema("test").columns(
            z.col.int("base"),
            z.col.derived("step1", function=pl.col("base") * 2),
            z.col.derived("step2", function=z.ref_derived("step1").col * 2),
            z.col.derived("step3", function=z.ref_derived("step2").col * 2),
            z.col.derived("step4", function=z.ref_derived("step3").col * 2),
            z.col.derived("step5", function=z.ref_derived("step4").col * 2),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        # step5 should be base * 32
        final_df = result.data.collect()
        assert final_df["step5"][0] == 0
        assert final_df["step5"][1] == 32


class TestMemoryEfficiency:
    """Tests for memory efficiency with LazyFrames."""

    def test_lazyframe_efficiency(self):
        """Test that LazyFrame evaluation is efficient."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": [f"ID_{i:06d}" for i in range(50000)],
                "value": list(range(50000)),
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.int("value"),
            z.col.derived("doubled", function=pl.col("value") * 2),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # Result should contain LazyFrames until collected
        assert result.data is not None
        # Collecting should work without memory issues
        final_df = result.data.collect()
        assert final_df.shape[0] == 50000
