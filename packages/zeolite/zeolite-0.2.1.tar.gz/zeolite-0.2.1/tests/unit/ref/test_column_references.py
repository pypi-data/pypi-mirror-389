"""
Unit tests for column reference system.

Tests ref() functionality and column reference resolution.
"""

import polars as pl
import zeolite as z
from zeolite.ref._reference import ColumnRef


class TestRefCreation:
    """Tests for basic ref() creation."""

    def test_ref_creation(self):
        """Test basic ref() creation."""
        # Act
        col_ref = z.ref("test_column")

        # Assert
        assert isinstance(col_ref, ColumnRef)
        assert col_ref.name == "test_column"

    def test_ref_clean_chaining(self):
        """Test ref().clean() chaining."""
        # Act
        col_ref = z.ref("test_column").clean()

        # Assert
        assert isinstance(col_ref, ColumnRef)
        assert col_ref.is_clean is True

    def test_ref_col_property(self):
        """Test ref().col for use in expressions."""
        # Act
        col_ref = z.ref("test_column")
        expr = col_ref.col

        # Assert
        # col property should return Polars expression
        assert isinstance(expr, pl.Expr)


class TestRefTypes:
    """Tests for different ref types."""

    def test_ref_meta(self):
        """Test meta column reference."""
        # Act
        meta_ref = z.ref_meta("test_meta")

        # Assert
        assert isinstance(meta_ref, ColumnRef)
        assert meta_ref.is_meta is True

    def test_ref_derived(self):
        """Test derived column reference."""
        # Act
        derived_ref = z.ref_derived("test_derived")

        # Assert
        assert isinstance(derived_ref, ColumnRef)
        assert derived_ref.is_derived is True

    def test_ref_custom_check(self):
        """Test custom check column reference."""
        # Act
        check_ref = z.ref_custom_check("test_check")

        # Assert
        assert isinstance(check_ref, ColumnRef)
        # Custom check references have specific properties


class TestRefInExpressions:
    """Tests for using refs in Polars expressions."""

    def test_ref_in_expression(self):
        """Test using ref in a Polars expression."""
        # Arrange
        df = pl.DataFrame(
            {
                "value": [10, 20, 30],
            }
        )

        schema = z.schema("test").columns(
            z.col.int("value"),
            z.col.derived("doubled", function=z.ref("value").col * 2),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert result.data.collect()["doubled"].to_list() == [20, 40, 60]

    def test_ref_clean_in_expression(self):
        """Test using ref().clean() in expression."""
        # Arrange
        df = pl.DataFrame(
            {
                "name": ["  Alice  ", "  Bob  ", "  Charlie  "],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("name").clean(z.Clean.string(sanitise="full")),
            z.col.derived(
                "name_length",
                function=z.ref("name").clean().col.str.len_chars(),
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        final_df = result.data.collect()
        assert final_df["name_length"].to_list() == [5, 3, 7]  # alice, bob, charlie


class TestRefResolution:
    """Tests for ref resolution in registry."""

    def test_ref_resolves_to_column_node(self):
        """Test that refs resolve to ColumnNode in registry."""
        # Arrange
        schema = z.schema("test").columns(
            z.col.str("test_column"),
        )

        # Assert
        # Registry should have entry for test_column
        registry = schema._params.registry
        assert any("test_column" in node_id for node_id in registry.by_id.keys())


class TestRefMethods:
    """Tests for ref method chaining."""

    def test_ref_chaining_methods(self):
        """Test chaining multiple ref methods."""
        # Act
        col_ref = z.ref("test").clean()

        # Assert
        assert col_ref.is_clean is True
        assert col_ref.name == "test___clean"

    def test_ref_with_check_name(self):
        """Test ref with check name specified."""
        # This tests the internal API for check column references
        # Arrange & Act
        col_ref = z.ref("test_column")

        # Assert
        # Basic ref shouldn't have check_name
        assert col_ref.check_name is None
