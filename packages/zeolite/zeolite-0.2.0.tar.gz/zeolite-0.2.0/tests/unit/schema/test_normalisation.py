"""
Unit tests for table structure normalisation.

Tests the step_1_normalise_table_structure function.
"""

import polars as pl
import zeolite as z


class TestNormaliseExactMatch:
    """Tests for exact header matching."""

    def test_normalise_exact_match(self):
        """Test when headers match schema exactly."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),
            z.col.int("age"),
        )

        # Act
        result = schema.step_1_normalise_table_structure(df)

        # Assert
        assert not result.reject
        normalised_df = result.data.collect()
        assert set(normalised_df.columns) == {"id", "name", "age"}


class TestNormaliseCaseInsensitive:
    """Tests for case-insensitive matching."""

    def test_normalise_case_insensitive(self):
        """Test that 'Name' matches 'name' case-insensitively."""
        # Arrange
        df = pl.DataFrame(
            {
                "ID": ["001", "002", "003"],
                "Name": ["Alice", "Bob", "Charlie"],
                "AGE": [25, 30, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),
            z.col.int("age"),
        )

        # Act
        result = schema.step_1_normalise_table_structure(df)

        # Assert
        assert not result.reject
        normalised_df = result.data.collect()
        # Should be renamed to lowercase
        assert "id" in normalised_df.columns
        assert "name" in normalised_df.columns
        assert "age" in normalised_df.columns


class TestNormaliseWithVariants:
    """Tests for column variants matching."""

    def test_normalise_with_variants(self):
        """Test that 'full_name' matches 'name' via variants."""
        # Arrange
        df = pl.DataFrame(
            {
                "person_id": ["001", "002", "003"],
                "full_name": ["Alice Smith", "Bob Jones", "Charlie Brown"],
                "years": [25, 30, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").variants("person_id", "patient_id"),
            z.col.str("name").variants("full_name", "person_name"),
            z.col.int("age").variants("years"),
        )

        # Act
        result = schema.step_1_normalise_table_structure(df)

        # Assert
        assert not result.reject
        normalised_df = result.data.collect()
        # Variants should be renamed to canonical names
        assert "id" in normalised_df.columns
        assert "name" in normalised_df.columns
        assert "age" in normalised_df.columns
        # Original variant names should be renamed
        assert "person_id" not in normalised_df.columns
        assert "full_name" not in normalised_df.columns
        assert "years" not in normalised_df.columns


class TestNormaliseMissingColumns:
    """Tests for missing column handling."""

    def test_normalise_missing_required(self):
        """Test error when required column is missing."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "name": ["Alice", "Bob", "Charlie"],
                # Missing required "age" column
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),
            z.col.int("age"),  # Required by default
        )

        # Act
        result = schema.step_1_normalise_table_structure(df)

        # Assert
        assert result.reject is True
        # Should have error about missing column
        assert len(result.errors) > 0
        error_messages = [str(e) for e in result.errors]
        assert any("age" in msg.lower() for msg in error_messages)

    def test_normalise_missing_optional(self):
        """Test no error for optional missing column."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "name": ["Alice", "Bob", "Charlie"],
                # Missing optional "age" column
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),
            z.col.int("age").optional(),  # Optional column
        )

        # Act
        result = schema.step_1_normalise_table_structure(df)

        # Assert
        assert result.reject is False
        # May have debug/warning about missing column but shouldn't reject
        normalised_df = result.data.collect()
        # Missing optional column should be added as null
        assert "age" in normalised_df.columns


class TestNormaliseExtraColumns:
    """Tests for extra column handling."""

    def test_normalise_extra_columns_strict(self):
        """Test that extra columns are dropped in strict mode."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
                "extra_col": ["x", "y", "z"],  # Extra column not in schema
            }
        )

        schema = (
            z.schema("test")
            .strict()
            .columns(
                z.col.str("id"),
                z.col.str("name"),
                z.col.int("age"),
            )
        )

        # Act
        result = schema.step_1_normalise_table_structure(df)

        # Assert
        normalised_df = result.data.collect()
        # Extra column should be dropped
        assert "extra_col" not in normalised_df.columns
        assert set(normalised_df.columns) == {"id", "name", "age"}
        # Should have debug message about extra column
        assert len(result.errors) > 0

    def test_normalise_adds_missing_columns(self):
        """Test that missing columns are added as null."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                # Missing "name" and "age"
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name").optional(),
            z.col.int("age").optional(),
        )

        # Act
        result = schema.step_1_normalise_table_structure(df)

        # Assert
        normalised_df = result.data.collect()
        # Missing columns should be added
        assert "name" in normalised_df.columns
        assert "age" in normalised_df.columns
        # Values should be null
        assert all(v is None for v in normalised_df["name"])
        assert all(v is None for v in normalised_df["age"])


class TestNormaliseWhitespace:
    """Tests for whitespace handling in column names."""

    def test_normalise_whitespace_in_headers(self):
        """Test that whitespace in headers is handled."""
        # Arrange
        df = pl.DataFrame(
            {
                "  id  ": ["001", "002", "003"],
                " name ": ["Alice", "Bob", "Charlie"],
                "age  ": [25, 30, 35],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),
            z.col.int("age"),
        )

        # Act
        result = schema.step_1_normalise_table_structure(df)

        # Assert
        assert not result.reject
        normalised_df = result.data.collect()
        # Whitespace should be sanitized
        assert "id" in normalised_df.columns
        assert "name" in normalised_df.columns
        assert "age" in normalised_df.columns


class TestNormaliseEmptyData:
    """Tests for empty data handling."""

    def test_normalise_empty_dataframe(self):
        """Test that empty DataFrame is detected."""
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
        result = schema.step_1_normalise_table_structure(df)

        # Assert
        # Empty data should trigger reject
        assert result.reject is True
        error_messages = [str(e) for e in result.errors]
        assert any(
            "empty" in msg.lower() or "no data" in msg.lower() for msg in error_messages
        )


class TestNormaliseDuplicateMapping:
    """Tests for duplicate column mapping."""

    def test_normalise_duplicate_variant_mapping(self):
        """Test error when multiple columns map to same target."""
        # Arrange - both "id" and "person_id" present, both map to "id"
        df = pl.DataFrame(
            {
                "id": ["001", "002", "003"],
                "person_id": ["P001", "P002", "P003"],
                "name": ["Alice", "Bob", "Charlie"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("id").variants("person_id"),  # Both columns map to "id"
            z.col.str("name"),
        )

        # Act
        result = schema.step_1_normalise_table_structure(df)

        # Assert
        # Should have error about duplicate mapping
        assert len(result.errors) > 0
        # Implementation may reject or handle differently
        error_messages = [str(e) for e in result.errors]
        assert any(
            "duplicate" in msg.lower() or "assigned" in msg.lower()
            for msg in error_messages
        )
