"""
Unit tests for derived column functionality.

Tests derived columns and custom check columns.
"""

import polars as pl
import zeolite as z
from zeolite.types import ProcessingSuccess


class TestSimpleDerivedColumns:
    """Tests for basic derived columns."""

    def test_simple_derived_column(self):
        """Test basic derived column from expression."""
        # Arrange
        df = pl.DataFrame(
            {
                "first_name": ["Alice", "Bob", "Charlie"],
                "last_name": ["Smith", "Jones", "Brown"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("first_name"),
            z.col.str("last_name"),
            z.col.derived(
                "full_name",
                function=pl.concat_str(
                    [pl.col("first_name"), pl.lit(" "), pl.col("last_name")]
                ),
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert "full_name" in final_df.columns
        assert list(final_df["full_name"]) == [
            "Alice Smith",
            "Bob Jones",
            "Charlie Brown",
        ]

    def test_derived_from_cleaned(self):
        """Test derived column using cleaned column reference."""
        # Arrange
        df = pl.DataFrame(
            {
                "raw_name": ["  ALICE  ", "  BOB  ", "  CHARLIE  "],
                "age": [25, 30, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("raw_name").clean(z.Clean.string(sanitise="full")),
            z.col.int("age"),
            z.col.derived(
                "name_length",
                function=z.ref("raw_name").clean().col.str.len_chars(),
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert "name_length" in final_df.columns
        # Lengths of cleaned names
        assert list(final_df["name_length"]) == [5, 3, 7]  # alice, bob, charlie

    def test_derived_with_multiple_sources(self):
        """Test derived column using multiple source columns."""
        # Arrange
        df = pl.DataFrame(
            {
                "price": [100, 200, 300],
                "quantity": [2, 3, 1],
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
        assert list(final_df["total"]) == [200, 600, 300]


class TestCustomCheckColumns:
    """Tests for custom validation check columns."""

    def test_custom_check_column(self):
        """Test custom validation expression."""
        # Arrange
        df = pl.DataFrame(
            {
                "score": [85, 105, 92, 78, 88],
                "max_score": [100, 100, 100, 100, 100],
            }
        )

        schema = z.schema("test").columns(
            z.col.int("score"),
            z.col.int("max_score"),
            z.col.custom_check(
                name="valid_score",
                function=(
                    pl.col("score").ge(0) & pl.col("score").le(pl.col("max_score"))
                ),
                message="Score must be between 0 and max_score",
                thresholds=z.Threshold(reject=0.5),
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # 1 out of 5 scores invalid (20% < 50% reject threshold)
        assert isinstance(result, ProcessingSuccess)


class TestDerivedDependencies:
    """Tests for derived column dependency chains."""

    def test_derived_dependency_chain(self):
        """Test A -> B -> C dependency chain."""
        # Arrange
        df = pl.DataFrame(
            {
                "price": [100, 200, 300],
                "quantity": [2, 3, 1],
            }
        )

        total_col = z.col.derived(
            "total", function=pl.col("price") * pl.col("quantity")
        )
        tax_col = z.col.derived("tax", function=total_col.ref.col * 0.1)

        schema = z.schema("test").columns(
            z.col.int("price"),
            z.col.int("quantity"),
            # Column A: total
            total_col,
            # Column B: tax (depends on A)
            tax_col,
            # Column C: final_price (depends on A + B)
            z.col.derived("final_price", function=total_col.ref.col + tax_col.ref.col),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()

        # Verify dependency chain computed correctly
        assert final_df["total"][0] == 200
        assert abs(final_df["tax"][0] - 20) < 0.01
        assert abs(final_df["final_price"][0] - 220) < 0.01

    def test_derived_execution_order(self):
        """Test that derived columns execute in correct order."""
        # Arrange
        df = pl.DataFrame(
            {
                "value": [10, 20, 30],
            }
        )

        doubled = z.col.derived("doubled", function=pl.col("value") * 2)

        schema = z.schema("test").columns(
            z.col.int("value"),
            # These should execute in dependency order
            doubled,
            z.col.derived("tripled", function=doubled.ref.col * 1.5),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # value * 2 * 1.5 = value * 3
        assert list(final_df["tripled"]) == [30, 60, 90]


class TestDerivedWithCleaning:
    """Tests for derived columns combined with cleaning."""

    def test_derived_from_cleaned_enum(self):
        """Test derived column from cleaned enum."""
        # Arrange
        df = pl.DataFrame(
            {
                "gender": ["male", "female", "MALE", "Female"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("gender").clean(
                z.Clean.enum(enum_map={"male": "M", "female": "F"}, sanitise="full")
            ),
            z.col.derived(
                "is_male",
                function=z.ref("gender").clean().col.eq("M"),
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["is_male"]) == [True, False, True, False]


class TestMultiColumnDerived:
    """Tests for derived columns using multiple columns."""

    def test_multi_column_boolean_logic(self):
        """Test derived column with boolean logic across columns."""
        # Arrange
        df = pl.DataFrame(
            {
                "ethnicity_1": ["maori", "european", "maori"],
                "ethnicity_2": ["european", "asian", "pacific"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("ethnicity_1").clean(z.Clean.string(sanitise="full")),
            z.col.str("ethnicity_2").clean(z.Clean.string(sanitise="full")),
            z.col.derived(
                "is_maori",
                function=(
                    z.ref("ethnicity_1").clean().col.eq("maori")
                    | z.ref("ethnicity_2").clean().col.eq("maori")
                ),
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["is_maori"]) == [True, False, True]
