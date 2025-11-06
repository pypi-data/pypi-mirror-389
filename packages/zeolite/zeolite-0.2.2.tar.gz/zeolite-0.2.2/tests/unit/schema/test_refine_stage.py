"""
Unit tests for schema refinement stage (step 6).

Tests temporary column exclusion, alias handling, and final output structure.
"""

import polars as pl
import zeolite as z
from zeolite.types import ProcessingSuccess


class TestRefinedExclusions:
    """Tests for"""

    def test_temporary_excludes_source_column(self):
        """Temporary source column excluded from output."""
        df = pl.DataFrame({"keep": ["a"], "temp": ["b"]})
        schema = z.schema("test").columns(
            z.col.str("keep"),
            z.col.str("temp").temporary(),
        )
        result = schema.apply(df)

        assert isinstance(result, ProcessingSuccess)
        assert list(result.data.collect().columns) == ["keep"]

    def test_temp_alias_method(self):
        """Test .temp() works as alias for .temporary()."""
        df = pl.DataFrame({"keep": ["a"], "temp": ["b"]})
        schema = z.schema("test").columns(
            z.col.str("keep"),
            z.col.str("temp").temp(),
        )
        result = schema.apply(df)

        assert list(result.data.collect().columns) == ["keep"]

    def test_temporary_derived_column(self):
        """Temporary derived column excluded but still usable in expressions."""
        df = pl.DataFrame({"price": [100], "quantity": [2]})
        intermediate = z.col.derived(
            "calc", function=pl.col("price") * pl.col("quantity")
        ).temporary()

        schema = z.schema("test").columns(
            z.col.int("price"),
            z.col.int("quantity"),
            intermediate,
            z.col.derived("final", function=intermediate.ref.col * 1.1),
        )
        result = schema.apply(df)

        assert isinstance(result, ProcessingSuccess)
        cols = result.data.collect().columns
        assert "final" in cols
        assert "calc" not in cols

    def test_temporary_with_cleaning(self):
        """Temporary flag preserved through cleaning."""
        df = pl.DataFrame({"keep": ["a"], "temp": ["  b  "]})
        schema = z.schema("test").columns(
            z.col.str("keep"),
            z.col.str("temp").temporary().clean(z.Clean.string(sanitise="full")),
        )
        result = schema.apply(df)

        assert list(result.data.collect().columns) == ["keep"]

    def test_validation_check_temporary_by_default(self):
        """Validation checks without alias are temporary by default."""
        df = pl.DataFrame({"name": ["Alice", ""]})
        schema = z.schema("test").columns(
            z.col.str("name").validations(z.Check.not_empty().warning(0.5)),
        )
        result = schema.apply(df)

        assert isinstance(result, ProcessingSuccess)
        assert list(result.data.collect().columns) == ["name"]

    def test_validation_check_with_alias_not_temporary(self):
        """Validation checks with alias are included in output."""
        df = pl.DataFrame({"name": ["Alice", ""]})
        schema = z.schema("test").columns(
            z.col.str("name").validations(
                z.Check.not_empty().warning(0.5).alias("name_check")
            ),
        )
        result = schema.apply(df)

        assert isinstance(result, ProcessingSuccess)
        cols = result.data.collect().columns
        assert "name" in cols
        assert "name_check" in cols

    def test_temporary_false_includes_column(self):
        """Explicit .temporary(False) includes column."""
        df = pl.DataFrame({"col": ["a"]})
        schema = z.schema("test").columns(
            z.col.str("col").temporary(False),
        )
        result = schema.apply(df)

        assert "col" in result.data.collect().columns

    def test_temporary_exists_in_prepared_not_refined(self):
        """Temporary columns exist in prepared stage but not refined."""
        df = pl.DataFrame({"keep": ["a"], "temp": ["b"]})
        schema = z.schema("test").columns(
            z.col.str("keep"),
            z.col.str("temp").temporary(),
        )
        result = schema.apply(df)

        assert isinstance(result, ProcessingSuccess)
        assert "temp" in result.prepared.collect().columns
        assert "temp" not in result.data.collect().columns
