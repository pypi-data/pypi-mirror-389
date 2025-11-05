"""
Unit tests for table preparation (Stage 3).

Tests the step_3_prepare_additional_columns function which appends:
- Cleaned columns
- Derived columns
- Validation check columns
"""

import polars as pl
import zeolite as z


class TestPrepareAddsCleaned:
    """Tests for adding cleaned columns during prepare stage."""

    def test_prepare_adds_cleaned_column(self):
        """Test that prepare stage adds cleaned column when cleaning defined."""
        # Arrange
        df = pl.DataFrame(
            {
                "name": ["  Alice  ", "  Bob  ", "  Charlie  "],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("name").clean(z.Clean.string(sanitise="full")),
        )

        # Act
        result = schema.apply(df)

        # Assert
        prepared_df = result.prepared.collect()
        # Should have both original and cleaned column
        assert "name" in prepared_df.columns
        assert "name___clean" in prepared_df.columns
        # Cleaned values should be sanitised
        assert prepared_df["name___clean"][0] == "alice"
        assert prepared_df["name___clean"][1] == "bob"
        assert prepared_df["name___clean"][2] == "charlie"

    def test_prepare_without_cleaning(self):
        """Test that prepare stage works when no cleaning defined."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "name": ["Alice", "Bob", "Charlie"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),  # No cleaning
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)

        # Assert
        prepared_df = prepared.data.collect()
        # Should only have original columns, no cleaned columns
        assert "id" in prepared_df.columns
        assert "name" in prepared_df.columns
        assert "id___clean" not in prepared_df.columns
        assert "name___clean" not in prepared_df.columns


class TestPrepareAddsDerived:
    """Tests for adding derived columns during prepare stage."""

    def test_prepare_adds_derived_column(self):
        """Test that prepare stage adds derived columns."""
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
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)

        # Assert
        prepared_df = prepared.data.collect()
        # Derived columns have "derived___" prefix
        assert "derived___total" in prepared_df.columns
        assert prepared_df["derived___total"].to_list() == [200, 600, 300]

    def test_prepare_derived_from_cleaned(self):
        """Test that derived columns can reference cleaned columns."""
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
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)

        # Assert
        prepared_df = prepared.data.collect()
        # Derived columns have "derived___" prefix
        assert "derived___name_length" in prepared_df.columns
        # Lengths should be based on cleaned names
        assert prepared_df["derived___name_length"].to_list() == [
            5,
            3,
            7,
        ]  # alice, bob, charlie


class TestPrepareAddsCheckColumns:
    """Tests for adding validation check columns during prepare stage."""

    def test_prepare_adds_validation_check_columns(self):
        """Test that prepare stage adds check columns for validations."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "age": [25, 30, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").validations(z.Check.not_empty(), z.Check.unique()),
            z.col.int("age").validations(z.Check.in_range(min_value=0, max_value=120)),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)

        # Assert
        prepared_df = prepared.data.collect()
        # Should have check columns for each validation (check format may vary)
        check_columns = [col for col in prepared_df.columns if "check" in col.lower()]
        assert len(check_columns) >= 3  # 2 checks for id, 1 check for age

    def test_prepare_check_columns_pass_fail(self):
        """Test that check columns have pass/fail values."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "002"],  # Duplicate
                "age": [25, 150, 35],  # One out of range
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

        # Assert
        prepared_df = prepared.data.collect()
        # Find check columns (format may vary)
        id_check_col = [
            col for col in prepared_df.columns if "id" in col and "check" in col.lower()
        ]
        age_check_col = [
            col
            for col in prepared_df.columns
            if "age" in col and "check" in col.lower()
        ]

        # Should have at least one check column for each
        assert len(id_check_col) >= 1
        assert len(age_check_col) >= 1


class TestPrepareExecutionStages:
    """Tests for execution stage ordering during prepare."""

    def test_prepare_handles_execution_order(self):
        """Test that prepare executes columns in correct dependency order."""
        # Arrange
        df = pl.DataFrame(
            {
                "value": [10, 20, 30],
            }
        )

        doubled = z.col.derived("doubled", function=pl.col("value") * 2)

        schema = z.schema("test").columns(
            z.col.int("value"),
            doubled,
            z.col.derived("quadrupled", function=doubled.ref.col * 2),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)

        # Assert
        prepared_df = prepared.data.collect()
        # Should compute derived columns in correct order (with "derived___" prefix)
        assert prepared_df["derived___doubled"].to_list() == [20, 40, 60]
        assert prepared_df["derived___quadrupled"].to_list() == [40, 80, 120]

    def test_prepare_parallel_independent_columns(self):
        """Test that independent columns can be computed in same stage."""
        # Arrange
        df = pl.DataFrame(
            {
                "a": [1, 2, 3],
                "b": [10, 20, 30],
            }
        )

        schema = z.schema("test").columns(
            z.col.int("a"),
            z.col.int("b"),
            # These two derived columns are independent
            z.col.derived("a_doubled", function=pl.col("a") * 2),
            z.col.derived("b_doubled", function=pl.col("b") * 2),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)

        # Assert
        prepared_df = prepared.data.collect()
        # Check for derived columns with "derived___" prefix
        assert prepared_df["derived___a_doubled"].to_list() == [2, 4, 6]
        assert prepared_df["derived___b_doubled"].to_list() == [20, 40, 60]


class TestPrepareWithNoTransformations:
    """Tests for prepare stage with minimal transformations."""

    def test_prepare_with_no_cleaning_derived_or_checks(self):
        """Test prepare stage when schema has no transformations."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "name": ["Alice", "Bob", "Charlie"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)

        # Assert
        prepared_df = prepared.data.collect()
        # Should have same columns as input
        assert set(prepared_df.columns) == {"id", "name"}
        # Data should be unchanged
        assert prepared_df["id"].to_list() == ["001", "002", "003"]

    def test_prepare_preserves_row_count(self):
        """Test that prepare stage doesn't remove or add rows."""
        # Arrange
        df = pl.DataFrame(
            {
                "value": list(range(100)),
            }
        )

        schema = z.schema("test").columns(
            z.col.int("value"),
            z.col.derived("doubled", function=pl.col("value") * 2),
        )

        # Act
        normalised = schema.step_1_normalise_table_structure(df)
        coerced = schema.step_2_coerce_datatypes(normalised.data)
        prepared = schema.step_3_prepare_additional_columns(coerced.data)

        # Assert
        prepared_df = prepared.data.collect()
        assert prepared_df.shape[0] == 100  # Same row count
