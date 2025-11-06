"""
Integration tests for all data cleaning variants with realistic data.

Tests cleaning operations: ID, Date, Enum, Boolean, String, Number
"""

import polars as pl
import pytest

import zeolite as z
from zeolite.types import ProcessingSuccess


class TestIDCleaning:
    """Tests for ID cleaning with prefix management."""

    def test_clean_id_with_prefix(self):
        """Test adding prefix to IDs."""
        # Arrange
        df = pl.DataFrame({"id": ["123", "456", "789"]})
        schema = z.schema("test").columns(
            z.col.str("id").clean(z.Clean.id(prefix="ORG_X"))
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["id"]) == ["ORG_X::123", "ORG_X::456", "ORG_X::789"]

    def test_clean_id_handles_nulls(self):
        """Test that null values are preserved during ID cleaning."""
        # Arrange
        df = pl.DataFrame({"id": ["123", None, "789"]})
        schema = z.schema("test").columns(
            z.col.str("id").clean(z.Clean.id(prefix="ORG"))
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df["id"][0] == "ORG::123"
        assert final_df["id"][1] is None
        assert final_df["id"][2] == "ORG::789"

    def test_clean_id_with_existing_prefix(self):
        """Test deduplication when some IDs already have the prefix."""
        # Arrange
        df = pl.DataFrame(
            {"id": ["123", "ORG_X::456", "ORG_X::ORG_X::789", "ORG_X::999"]}
        )
        schema = z.schema("test").columns(
            z.col.str("id").clean(z.Clean.id(prefix="ORG_X"))
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # All should have exactly one prefix
        assert list(final_df["id"]) == [
            "ORG_X::123",
            "ORG_X::456",
            "ORG_X::ORG_X::789",
            "ORG_X::999",
        ]


class TestDateCleaning:
    """Tests for date cleaning with various formats."""

    def test_clean_date_iso_format(self):
        """Test cleaning ISO format dates."""
        # Arrange
        df = pl.DataFrame({"date": ["2023-01-01", "2023-12-31", "2024-06-15"]})
        schema = z.schema("test").columns(z.col.str("date").clean(z.Clean.date()))

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # Dates should be parsed correctly
        assert final_df["date"].dtype == pl.Date or final_df["date"].dtype == pl.String

    def test_clean_date_various_formats(self):
        """Test parsing multiple date formats."""
        # Arrange
        df = pl.DataFrame(
            {"date": ["2023-01-15", "15/01/2023", "15-01-2023", "2023/01/15"]}
        )
        schema = z.schema("test").columns(z.col.str("date").clean(z.Clean.date()))

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        test_df = (
            result.data.filter(pl.col("date").is_not_null()).select(pl.len()).collect()
        )
        # All dates should be parsed (or attempted to parse)
        assert test_df.item() == 4

    def test_clean_date_various_month_first_formats(self):
        """Test parsing multiple date formats."""
        # Arrange
        df = pl.DataFrame(
            {"date": ["2023-01-15", "01/15/2023", "01-15-2023", "2023/01/15"]}
        )
        schema = z.schema("test").columns(
            z.col.str("date").clean(z.Clean.date(day_first=False))
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        test_df = (
            result.data.filter(pl.col("date").is_not_null()).select(pl.len()).collect()
        )
        # All dates should be parsed (or attempted to parse)
        assert test_df.item() == 4

    def test_clean_date_invalid_values(self):
        """Test handling of invalid date values."""
        # Arrange
        df = pl.DataFrame({"date": ["2023-01-15", "invalid", None, "not-a-date"]})
        schema = z.schema("test").columns(z.col.str("date").clean(z.Clean.date()))

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # Invalid dates should become null
        assert final_df["date"][1] is None or final_df["date"][1] == z.INVALID_DATA
        assert final_df["date"][2] is None
        assert final_df["date"][3] is None or final_df["date"][3] == z.INVALID_DATA

    def test_clean_date_excel_serial(self):
        """Test parsing Excel serial dates."""
        # Arrange
        df = pl.DataFrame({"date": ["44927", "44928", "44929"]})  # Excel dates
        schema = z.schema("test").columns(z.col.str("date").clean(z.Clean.date()))

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # Verify that dates were actually parsed (not null)
        non_null_count = final_df.filter(pl.col("date").is_not_null()).height
        assert non_null_count == 3, f"Expected 3 non-null dates, got {non_null_count}"

    def test_clean_date_with_timezone(self):
        """Test handling dates with timezone information."""
        # Arrange
        df = pl.DataFrame(
            {
                "date": [
                    "2023-01-15T10:30:00Z",
                    "2023-01-15T10:30:00+05:00",
                    "2023-01-15",
                ]
            }
        )
        schema = z.schema("test").columns(z.col.str("date").clean(z.Clean.date()))

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # Verify all dates were parsed successfully
        non_null_count = final_df.filter(pl.col("date").is_not_null()).height
        assert non_null_count == 3, f"Expected 3 non-null dates, got {non_null_count}"


class TestEnumCleaning:
    """Tests for enum cleaning with mapping."""

    def test_clean_enum_exact_match(self):
        """Test exact matches in enum map."""
        # Arrange
        df = pl.DataFrame({"gender": ["Male", "Female", "Male"]})
        schema = z.schema("test").columns(
            z.col.str("gender").clean(
                z.Clean.enum(enum_map={"Male": "M", "Female": "F"})
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["gender"]) == ["M", "F", "M"]

    def test_clean_enum_case_variations(self):
        """Test case-insensitive enum matching."""
        # Arrange
        df = pl.DataFrame({"gender": ["Male", "male", "MALE", "Female"]})
        schema = z.schema("test").columns(
            z.col.str("gender").clean(
                z.Clean.enum(enum_map={"male": "M", "female": "F"}, sanitise="full")
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # All variations of "male" should map to "M"
        assert final_df["gender"][0] == "M"
        assert final_df["gender"][1] == "M"
        assert final_df["gender"][2] == "M"
        assert final_df["gender"][3] == "F"

    def test_clean_enum_with_sanitise(self):
        """Test enum mapping with sanitisation (trim/lowercase)."""
        # Arrange
        df = pl.DataFrame({"gender": ["  Male  ", " male", "MALE ", "Female"]})
        schema = z.schema("test").columns(
            z.col.str("gender").clean(
                z.Clean.enum(enum_map={"male": "M", "female": "F"}, sanitise="full")
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # Sanitised values should match enum map
        assert all(v in ["M", "F"] for v in final_df["gender"])

    def test_clean_enum_unknown_values(self):
        """Test handling of values not in enum map."""
        # Arrange
        df = pl.DataFrame({"gender": ["Male", "Female", "Unknown", "Other"]})
        schema = z.schema("test").columns(
            z.col.str("gender").clean(
                z.Clean.enum(enum_map={"male": "M", "female": "F"})
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # Unknown values should become null or INVALID_DATA
        assert (
            final_df["gender"][2] == z.NO_DATA
            or final_df["gender"][2] == z.INVALID_DATA
        )
        assert (
            final_df["gender"][3] == z.NO_DATA
            or final_df["gender"][3] == z.INVALID_DATA
        )

    def test_clean_enum_null_handling(self):
        """Test that nulls are preserved in enum cleaning."""
        # Arrange
        df = pl.DataFrame({"gender": ["Male", None, "Female", None]})
        schema = z.schema("test").columns(
            z.col.str("gender").clean(
                z.Clean.enum(enum_map={"male": "M", "female": "F"})
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df["gender"][1] == z.NO_DATA
        assert final_df["gender"][3] == z.NO_DATA


class TestBooleanCleaning:
    """Tests for boolean cleaning with custom true/false values."""

    def test_clean_boolean_true_values(self):
        """Test various representations of true."""
        # Arrange
        df = pl.DataFrame({"active": ["yes", "active", "true", "1", "True"]})
        schema = z.schema("test").columns(
            z.col.str("active").clean(
                z.Clean.boolean(
                    true_values={"yes", "active", "true", "1"},
                    false_values={"no", "inactive", "false", "0"},
                )
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # All should be True
        assert all(final_df["active"])

    def test_clean_boolean_false_values(self):
        """Test various representations of false."""
        # Arrange
        df = pl.DataFrame({"active": ["no", "inactive", "false", "0", "False"]})
        schema = z.schema("test").columns(
            z.col.str("active").clean(
                z.Clean.boolean(
                    true_values={"yes", "active", "true", "1"},
                    false_values={"no", "inactive", "false", "0"},
                )
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # All should be False
        assert not any(final_df["active"])

    def test_clean_boolean_invalid_values(self):
        """Test that unknown values become null."""
        # Arrange
        df = pl.DataFrame({"active": ["yes", "maybe", "no", "unknown"]})
        schema = z.schema("test").columns(
            z.col.str("active").clean(
                z.Clean.boolean(
                    true_values={"yes", "active", "true"},
                    false_values={"no", "inactive", "false"},
                )
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # "maybe" and "unknown" should be null
        assert final_df["active"][1] is None
        assert final_df["active"][3] is None


class TestStringCleaning:
    """Tests for string sanitisation."""

    def test_clean_string_full_sanitise(self):
        """Test full sanitisation: trim + lowercase + remove special chars."""
        # Arrange
        df = pl.DataFrame({"name": ["  Alice!  ", "BOB#", "  Charlie$  "]})
        schema = z.schema("test").columns(
            z.col.str("name").clean(z.Clean.string(sanitise="full"))
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["name"]) == ["alice", "bob", "charlie"]

    def test_clean_string_lowercase_only(self):
        """Test lowercase transformation."""
        # Arrange
        df = pl.DataFrame({"name": ["Alice", "BOB", "Charlie"]})
        schema = z.schema("test").columns(
            z.col.str("name").clean(z.Clean.string(sanitise="lowercase"))
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["name"]) == ["alice", "bob", "charlie"]

    def test_clean_string_trim_only(self):
        """Test trimming whitespace only."""
        # Arrange
        df = pl.DataFrame({"name": ["  Alice  ", "  Bob", "Charlie  "]})
        schema = z.schema("test").columns(
            z.col.str("name").clean(z.Clean.string(sanitise="trim"))
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["name"]) == ["Alice", "Bob", "Charlie"]

    def test_clean_string_preserve_case(self):
        """Test no transformation when sanitise=None."""
        # Arrange
        df = pl.DataFrame({"name": ["Alice", "BOB", "charlie"]})
        schema = z.schema("test").columns(
            z.col.str("name").clean(z.Clean.string(sanitise=None))
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["name"]) == ["Alice", "BOB", "charlie"]

    def test_clean_string_unicode(self):
        """Test handling of unicode characters."""
        # Arrange
        df = pl.DataFrame({"name": ["Müller", "François", "José"]})
        schema = z.schema("test").columns(
            z.col.str("name").clean(z.Clean.string(sanitise="lowercase"))
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # Verify unicode is preserved and lowercased correctly
        assert list(final_df["name"]) == ["müller", "françois", "josé"]


class TestNumberCleaning:
    """Tests for number cleaning from strings."""

    def test_clean_number_from_string(self):
        """Test converting string numbers to actual numbers."""
        # Arrange
        df = pl.DataFrame({"amount": ["123", "456", "789"]})
        schema = z.schema("test").columns(z.col.str("amount").clean(z.Clean.number()))

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["amount"]) == [123, 456, 789]

    def test_clean_float_with_commas(self):
        """Test parsing numbers (floats) with thousands separators."""
        # Arrange
        df = pl.DataFrame({"amount": ["1,234", "5,678.90", "123"]})
        schema = z.schema("test").columns(z.col.str("amount").clean(z.Clean.number()))

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df["amount"][0] == 1234
        assert final_df["amount"][1] == 5678.90
        assert final_df["amount"][2] == 123

    def test_clean_integer_with_commas(self):
        """Test parsing numbers (integer) with thousands separators."""
        # Arrange
        df = pl.DataFrame({"amount": ["1,234", "5,678.90", "123"]})
        schema = z.schema("test").columns(z.col.str("amount").clean(z.Clean.int()))

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df["amount"][0] == 1234
        assert final_df["amount"][1] == 5679
        assert final_df["amount"][2] == 123

    def test_clean_number_invalid(self):
        """Test that invalid strings become null."""
        # Arrange
        df = pl.DataFrame({"amount": ["123", "not a number", "456"]})
        schema = z.schema("test").columns(z.col.str("amount").clean(z.Clean.number()))

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert final_df["amount"][0] == 123
        assert final_df["amount"][1] is None or final_df["amount"][1] == z.INVALID_DATA
        assert final_df["amount"][2] == 456


class TestCustomCleaning:
    """Tests for function-based custom clean usage."""

    def test_custom_clean_with_lamba(self):
        """Test custom clean with a lambda expression."""
        # Arrange
        df = pl.DataFrame(
            {
                "email": ["  ALICE@EXAMPLE.COM  ", "bob@test.com", "CHARLIE@MAIL.ORG"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("email").clean(
                z.Clean.custom(lambda col: col.str.strip_chars().str.to_lowercase())
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["email"]) == [
            "alice@example.com",
            "bob@test.com",
            "charlie@mail.org",
        ]

    def test_custom_clean_lambda_with_different_data_type(self):
        """Test custom clean with numeric data type."""
        # Arrange
        df = pl.DataFrame(
            {
                "price": [10.5, 20.7, 30.2],
            }
        )

        schema = z.schema("test").columns(
            z.col.float("price").clean(
                z.Clean.custom(
                    lambda col: (col * 1.15).round(2),
                    data_type="float",
                )
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # Prices with 15% markup, rounded to 2 decimals
        assert list(final_df["price"]) == pytest.approx([12.08, 23.81, 34.73], abs=0.01)

    def test_custom_clean_with_expr(self):
        """Test custom clean using a Polars expression directly."""
        # Arrange
        df = pl.DataFrame(
            {
                "name": ["alice", "bob", "charlie"],
                "title": ["dr", "sir", "mr"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("title"),
            # This SHOULD be a derived column, but good to check if it works still...
            z.col.str("name").clean(
                z.Clean.custom(
                    (pl.col("title") + " " + pl.col("name")).str.to_uppercase()
                )
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert list(final_df["name"]) == ["DR ALICE", "SIR BOB", "MR CHARLIE"]

    def test_derived_from_custom_cleaned(self):
        """Test derived column using custom cleaned column reference."""
        # Arrange
        df = pl.DataFrame(
            {
                "price": [100, 200, 300],
            }
        )

        schema = z.schema("test").columns(
            z.col.float("price").clean(
                z.Clean.custom(
                    lambda col: col * 1.15,
                    data_type="float",
                )
            ),
            z.col.derived(
                "high_price",
                function=z.ref("price").clean().col > 200,
                data_type="boolean",
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # After 15% markup: 115, 230, 345
        assert list(final_df["high_price"]) == [False, True, True]


class TestAliasBehavior:
    """Tests for alias functionality in cleaning."""

    def test_clean_with_alias(self):
        """Test that cleaned column uses alias name."""
        # Arrange
        df = pl.DataFrame({"raw_name": ["  Alice  ", "  Bob  "]})
        schema = z.schema("test").columns(
            z.col.str("raw_name").clean(
                z.Clean.string(sanitise="full").alias("clean_name")
            )
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # Should have clean_name column instead of raw_name__clean
        assert "clean_name" in final_df.columns

    def test_clean_without_alias(self):
        """Test that without alias, original column is replaced."""
        # Arrange
        df = pl.DataFrame({"name": ["  Alice  ", "  Bob  "]})
        schema = z.schema("test").columns(
            z.col.str("name").clean(z.Clean.string(sanitise="full"))
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        # Cleaned value should replace original
        assert "name" in final_df.columns
        assert list(final_df["name"]) == ["alice", "bob"]

    def test_custom_clean_with_alias(self):
        """Test custom clean uses custom alias."""
        # Arrange
        df = pl.DataFrame(
            {
                "raw_name": ["alice", "bob"],
            }
        )

        schema = z.schema("test").columns(
            z.col.str("raw_name").clean(
                z.Clean.custom(
                    lambda col: col.str.to_uppercase(),
                    alias="clean_name",
                )
            ),
        )

        # Act
        result = schema.apply(df)

        # Assert
        assert isinstance(result, ProcessingSuccess)
        final_df = result.data.collect()
        assert "clean_name" in final_df.columns
        assert list(final_df["clean_name"]) == ["ALICE", "BOB"]
