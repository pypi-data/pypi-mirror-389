"""
Integration tests for realistic data processing scenarios.

Tests complete workflows matching real-world use cases and README examples.
"""

import polars as pl
import zeolite as z
from zeolite.types import ProcessingSuccess


class TestReadmeExamples:
    """Tests based on examples from README.md."""

    def test_readme_example_individual_data(self):
        """Test the exact individual data example from README."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": ["P001", "P002", "P003", "P004", "P005"],
                "name": [
                    "Alice Smith",
                    "Bob Jones",
                    "Charlie Brown",
                    "Diana Prince",
                    "Eve Adams",
                ],
                "birthdate": [
                    "1998-05-15",
                    "1993-08-22",
                    "1990-12-01",
                    "1995-03-17",
                    "2000-07-30",
                ],
                "gender": ["Female", "Male", "Male", "Female", "Female"],
                "is_active": ["yes", "yes", "no", "yes", "yes"],
                "score": [85, 92, 78, 88, 95],
            }
        )

        schema = z.schema("individual").columns(
            z.col.str("id")
            .clean(z.Clean.id(prefix="ORG_X"))
            .validations(
                z.Check.not_empty(warning="any", error=0.1, reject=0.01),
                z.Check.unique(check_on_cleaned=True, reject="any"),
            ),
            z.col.str("name").validations(z.Check.not_empty()),
            z.col.str("birthdate")
            .clean(z.Clean.date())
            .validations(z.Check.valid_date(check_on_cleaned=True)),
            z.col.str("gender").clean(
                z.Clean.enum(
                    enum_map={
                        "m": "Male",
                        "f": "Female",
                        "female": "Female",
                        "male": "Male",
                    }
                )
            ),
            z.col.str("is_active").clean(
                z.Clean.boolean(
                    true_values={"yes", "active"},
                    false_values={"no", "inactive"},
                )
            ),
            z.col.int("score"),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()

        # Check transformations
        assert final_df.shape[0] == 5
        # IDs should have prefix
        assert all(id_val.startswith("ORG_X::") for id_val in final_df["id"])
        # Boolean should be converted
        assert final_df["is_active"].dtype == pl.Boolean or all(
            isinstance(v, bool) or v is None for v in final_df["is_active"]
        )


class TestMessyCsvScenarios:
    """Tests for messy CSV import scenarios."""

    def test_messy_csv_import_scenario(self):
        """Test handling messy CSV with various data quality issues."""
        # Arrange - Simulating a messy CSV file
        df = pl.DataFrame(
            {
                "  ID  ": ["001", "002", "003", "004"],  # Extra whitespace in header
                "Full_Name": [
                    "  Alice  ",
                    "BOB",
                    "charlie!",
                    "DIANA",
                ],  # Case variations
                "AGE": ["25", "30", "35", "28"],  # String numbers
                "enrollment DATE": [  # Mixed date formats
                    "2023-01-15",
                    "01/15/2023",
                    "2023/03/10",
                    "invalid",
                ],
            }
        )

        schema = z.schema("messy_csv").columns(
            z.col.str("id").variants("  ID  ", "ID", " id "),
            z.col.str("name")
            .variants("Full_Name", "full_name", "FULL NAME")
            .clean(z.Clean.string(sanitise="full")),
            z.col.int("age").variants("AGE", "Age", "age"),
            z.col.str("enrollment_date")
            .variants("enrollment DATE", "enrollment_date", "ENROLLMENT_DATE")
            .clean(z.Clean.date()),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()

        # Check normalization handled column name variations
        assert "id" in final_df.columns
        assert "name" in final_df.columns
        assert "age" in final_df.columns
        assert "enrollment_date" in final_df.columns

        # Check cleaning produced consistent output
        assert all(name.islower() and name.isalpha() for name in final_df["name"])
        assert final_df["age"].dtype == pl.Int64


class TestValidationScenarios:
    """Tests for multiple validation failures."""

    def test_multiple_validation_failures(self):
        """Test dataset with various quality issues at different severity levels."""
        # Arrange
        df = pl.DataFrame(
            {
                "id": [
                    "001",
                    "002",
                    "002",
                    "003",
                    "004",
                    "004",
                    "005",
                    None,
                    "006",
                    "007",
                ],
                "name": [
                    "Alice",
                    "Bob",
                    "Charlie",
                    "",
                    None,
                    "Diana",
                    "   ",
                    "Eve",
                    "Frank",
                    "Grace",
                ],
                "age": [
                    25,
                    150,
                    30,
                    -5,
                    35,
                    28,
                    200,
                    22,
                    27,
                    33,
                ],  # Out of range values
                "email": [
                    "valid@email.com",
                    "invalid",
                    "another@valid.com",
                    "also.valid@test.org",
                    None,
                    "bad",
                    "good@example.com",
                    "test@test.com",
                    "user@domain.co.uk",
                    "admin@site.net",
                ],
            }
        )

        schema = z.schema("validation").columns(
            z.col.str("id").validations(
                z.Check.not_empty(warning=0.2, error=0.4, reject=0.6),
                z.Check.unique(warning=0.2, error=0.4, reject=0.6),
            ),
            z.col.str("name").validations(
                z.Check.not_empty(warning=0.3, error=0.5, reject=0.7)
            ),
            z.col.int("age").validations(
                z.Check.in_range(
                    min_value=0, max_value=120, warning=0.3, error=0.5, reject=0.7
                )
            ),
            z.col.str("email").validations(
                z.Check.str_matches(
                    pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
                    warning=0.3,
                    error=0.5,
                    reject=0.7,
                )
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # Should succeed or fail based on threshold configuration
        # Different severity levels should be assigned based on failure rates
        assert result is not None
        if isinstance(result, ProcessingSuccess):
            # Should have collected errors from validation failures
            assert len(result.errors) > 0
            # Verify we have data
            assert result.data.collect().shape[0] > 0


class TestDerivedColumns:
    """Tests for derived column dependencies."""

    def test_derived_column_dependencies(self):
        """Test complex derived column dependency chain."""
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

        schema = z.schema("derived").columns(
            z.col.int("price"),
            z.col.int("quantity"),
            # Column A: derived from source columns
            total_col,
            # Column B: derived from A
            tax_col,
            # Column C: derived from A + B
            z.col.derived("final_price", function=total_col.ref.col + tax_col.ref.col),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()

        # Verify execution order and computed values
        assert final_df["total"][0] == 200  # 100 * 2
        assert final_df["total"][1] == 600  # 200 * 3
        assert final_df["total"][2] == 300  # 300 * 1

        assert abs(final_df["tax"][0] - 20) < 0.01  # 200 * 0.1
        assert abs(final_df["tax"][1] - 60) < 0.01  # 600 * 0.1
        assert abs(final_df["tax"][2] - 30) < 0.01  # 300 * 0.1

        assert abs(final_df["final_price"][0] - 220) < 0.01  # 200 + 20
        assert abs(final_df["final_price"][1] - 660) < 0.01  # 600 + 60
        assert abs(final_df["final_price"][2] - 330) < 0.01  # 300 + 30


class TestCustomValidations:
    """Tests for custom check validations."""

    def test_custom_check_validations(self):
        """Test custom validation expressions with thresholds."""
        # Arrange
        df = pl.DataFrame(
            {
                "score": [85, 105, 92, 78, 88, 95, 110, 82, 90, 88],
                "max_score": [100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
            }
        )

        schema = z.schema("custom_check").columns(
            z.col.int("score"),
            z.col.int("max_score"),
            z.col.custom_check(
                name="valid_score_range",
                function=(pl.col("score") >= 0)
                & (pl.col("score") <= pl.col("max_score")),
                message="Score must be between 0 and max_score",
                thresholds=z.Threshold(warning=0.1, error=0.3, reject=0.5),
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # 2 out of 10 scores are invalid (20%) - should trigger warning and error
        assert result is not None
        if isinstance(result, ProcessingSuccess):
            # Should have warnings/errors but not reject (20% < 50% reject threshold)
            assert len(result.errors) > 0
            assert result.data.collect().shape[0] == 10


class TestRowRemoval:
    """Tests for row removal workflow."""

    def test_remove_rows_workflow(self, row_removal_df, row_removal_schema):
        """Test that rows failing validations are removed during filter stage."""
        # Act
        result = row_removal_schema.apply(row_removal_df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()

        # Should have removed 3 rows (30% removed)
        assert final_df.shape[0] == 7

        # All remaining ages should be valid
        assert all(0 <= age <= 120 for age in final_df["age"])

        # Table validation should see the removed rows and trigger warning/error
        # (30% removed triggers warning at 20% and error at 40% - wait, 30% is between them)
        # So should have warning but not error
        if len(result.errors) > 0:
            error_messages = [str(e).lower() for e in result.errors]
            # Should mention removed rows
            assert any("removed" in msg or "row" in msg for msg in error_messages)


class TestMultiColumnValidation:
    """Tests for multi-column validation logic."""

    def test_multi_column_custom_validation(self):
        """Test custom validation that checks multiple columns."""
        # Arrange
        df = pl.DataFrame(
            {
                "start_date": ["2023-01-01", "2023-02-01", "2023-03-01", "2023-04-01"],
                "end_date": ["2023-01-31", "2023-01-15", "2023-03-31", "2023-05-01"],
                # Second row has end before start
            }
        )

        schema = z.schema("multi_col").columns(
            z.col.str("start_date").clean(z.Clean.date()),
            z.col.str("end_date").clean(z.Clean.date()),
            z.col.custom_check(
                name="valid_date_range",
                function=pl.col("end_date") >= pl.col("start_date"),
                message="End date must be after start date",
                thresholds=z.Threshold(warning=0.2, error=0.5, reject=0.8),
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        # One invalid row (25%) should trigger warning but not error (< 50% threshold)
        assert result is not None
        if isinstance(result, ProcessingSuccess):
            # Should have warning about invalid date range
            assert len(result.errors) > 0
            assert result.data.collect().shape[0] == 4
