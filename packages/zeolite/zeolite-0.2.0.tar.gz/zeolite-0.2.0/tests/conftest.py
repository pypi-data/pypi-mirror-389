"""
Pytest fixtures for Zeolite tests.

All fixtures are automatically available to all tests without needing to import them.
Simply add the fixture name as a parameter to your test function.

Example:
    def test_validation(messy_data_df, validation_schema):
        result = validation_schema.apply(messy_data_df)
        ...

Organization:
    - Basic fixtures: Simple test data and configurations
    - Dataset fixtures: Realistic test datasets from fixtures/datasets.py
    - Schema fixtures: Reusable schema definitions from fixtures/schemas.py
"""

import pytest
import polars as pl
import zeolite as z
from zeolite.types import ColumnNode, Sensitivity
from zeolite.types.validation.threshold import Threshold, ThresholdLevel


# =============================================================================
# Basic fixtures (legacy - kept for backwards compatibility)
# =============================================================================


@pytest.fixture
def sample_df():
    """Sample DataFrame for testing"""
    return pl.DataFrame(
        {
            "string_col": ["value1", None, "", "value2"],
            "number_col": [1, 2, None, 4],
            "boolean_col": ["yes", "no", "true", "invalid"],
        }
    )


@pytest.fixture
def sample_threshold():
    """Sample threshold configuration"""
    return Threshold(
        warning=0.1,  # 10% threshold
        error=0.5,  # 50% threshold
        reject=0.8,  # 80% threshold
    )


@pytest.fixture
def sample_column_node():
    """Sample column node for testing"""
    return ColumnNode(
        id="test::sample",
        name="sample",
        data_type="string",
        column_type="source",
        sensitivity=Sensitivity.NON_SENSITIVE,
        schema="test",
        stage=None,
        expression=None,
        validation_rule=None,
    )


@pytest.fixture
def sample_error_levels():
    """Sample error levels for testing"""
    return {
        "debug": ThresholdLevel.DEBUG.level,
        "warning": ThresholdLevel.WARNING.level,
        "error": ThresholdLevel.ERROR.level,
        "reject": ThresholdLevel.REJECT.level,
    }


# =============================================================================
# Dataset fixtures - Clean, valid data
# =============================================================================


@pytest.fixture
def valid_simple_df():
    """Clean, valid simple dataset with 4 rows."""
    return pl.DataFrame(
        {
            "id": ["001", "002", "003", "004"],
            "name": ["Alice", "Bob", "Charlie", "Diana"],
            "age": [25, 30, 35, 28],
            "enrollment_date": ["2023-01-15", "2023-02-20", "2023-03-10", "2023-04-05"],
        }
    )


@pytest.fixture
def valid_individuals_df():
    """Clean individual person data (matches README example)."""
    return pl.DataFrame(
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


# =============================================================================
# Dataset fixtures - Messy data
# =============================================================================


@pytest.fixture
def messy_headers_df():
    """Dataset with messy column headers (whitespace, case variations)."""
    return pl.DataFrame(
        {
            "  ID  ": ["001", "002", "003"],  # Extra whitespace
            "Full_Name": ["Alice", "Bob", "Charlie"],  # Case variation
            "AGE": [25, 30, 35],  # All caps
            "enrollment DATE": ["2023-01-15", "2023-02-20", "2023-03-10"],  # Space
        }
    )


@pytest.fixture
def messy_data_df():
    """Dataset with various data quality issues."""
    return pl.DataFrame(
        {
            "id": ["001", "002", "002", None],  # Duplicate and null
            "name": ["  Alice  ", "", "Charlie", None],  # Whitespace, empty, null
            "age": ["25", "not a number", "35", "28"],  # Type mismatch
            "enrollment_date": ["2023-01-15", "invalid", "", None],  # Invalid dates
            "is_active": ["yes", "no", "maybe", "true"],  # Mixed boolean values
        }
    )


# =============================================================================
# Dataset fixtures - Edge cases
# =============================================================================


@pytest.fixture
def empty_df():
    """Empty DataFrame with columns but no rows."""
    return pl.DataFrame(
        {
            "id": [],
            "name": [],
            "age": [],
        }
    )


@pytest.fixture
def single_row_df():
    """DataFrame with only one row."""
    return pl.DataFrame(
        {
            "id": ["001"],
            "name": ["Alice"],
            "age": [25],
        }
    )


@pytest.fixture
def all_nulls_df():
    """DataFrame where all values are null."""
    return pl.DataFrame(
        {
            "id": [None, None, None],
            "name": [None, None, None],
            "age": [None, None, None],
        }
    )


@pytest.fixture
def all_duplicates_df():
    """DataFrame where all rows are identical."""
    return pl.DataFrame(
        {
            "id": ["001", "001", "001", "001"],
            "name": ["Alice", "Alice", "Alice", "Alice"],
            "age": [25, 25, 25, 25],
        }
    )


# =============================================================================
# Dataset fixtures - Validation scenarios
# =============================================================================


@pytest.fixture
def validation_failing_df():
    """Dataset with multiple validation failures."""
    return pl.DataFrame(
        {
            "id": ["001", "002", "002", None, "004"],  # Duplicate and null
            "age": [25, 150, -5, 30, 200],  # Out of range
            "email": ["valid@email.com", "invalid", "another@valid.com", None, "bad"],
            "score": [85, 92, 78, 88, 95],
        }
    )


@pytest.fixture
def row_removal_df():
    """Dataset for testing row removal (30% invalid ages)."""
    return pl.DataFrame(
        {
            "id": [
                "001",
                "002",
                "003",
                "004",
                "005",
                "006",
                "007",
                "008",
                "009",
                "010",
            ],
            "age": [25, -5, 30, 150, 35, 28, 200, 22, 27, 33],  # 3 out of range
            "score": [85, 92, 78, 88, 95, 82, 90, 88, 91, 87],
        }
    )


# =============================================================================
# Schema fixtures - Basic schemas
# =============================================================================


@pytest.fixture
def simple_schema():
    """Simple schema with basic validation."""
    return z.schema("simple").columns(
        z.col.str("id").validations(z.Check.not_empty(), z.Check.unique()),
        z.col.str("name"),
        z.col.int("age"),
        z.col.date("enrollment_date"),
    )


@pytest.fixture
def minimal_schema():
    """Minimal schema with no validations."""
    return z.schema("minimal").columns(
        z.col.str("id"),
        z.col.str("name"),
    )


# =============================================================================
# Schema fixtures - Feature-specific schemas
# =============================================================================


@pytest.fixture
def validation_schema():
    """Schema testing various validation rules."""
    return z.schema("validation").columns(
        z.col.str("id").validations(
            z.Check.not_empty(warning=0.1, error=0.3, reject=0.5),
            z.Check.unique(error="any"),
        ),
        z.col.int("age").validations(
            z.Check.not_empty(),
            z.Check.in_range(min_value=0, max_value=120, reject=0.2),
        ),
        z.col.str("email").validations(
            z.Check.not_empty(),
            z.Check.str_matches(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$", reject=0.3),
        ),
        z.col.int("score"),
    )


@pytest.fixture
def cleaning_schema():
    """Schema testing various cleaning operations."""
    return z.schema("cleaning").columns(
        z.col.str("id").clean(z.Clean.id(prefix="ORG_X")),
        z.col.str("date_str").clean(z.Clean.date()),
        z.col.str("gender").clean(
            z.Clean.enum(
                enum_map={
                    "m": "Male",
                    "f": "Female",
                    "male": "Male",
                    "female": "Female",
                }
            )
        ),
        z.col.str("is_active").clean(
            z.Clean.boolean(
                true_values={"yes", "active", "true", "1"},
                false_values={"no", "inactive", "false", "0"},
            )
        ),
        z.col.str("name").clean(z.Clean.string(sanitise="full")),
    )


@pytest.fixture
def row_removal_schema():
    """Schema with row removal validation."""
    return (
        z.schema("row_removal")
        .columns(
            z.col.str("id"),
            z.col.int("age").validations(
                z.Check.in_range(
                    min_value=0,
                    max_value=120,
                    warning=0.1,
                    error=0.2,
                    reject=0.5,
                    remove_row_on_fail=True,
                )
            ),
            z.col.int("score"),
        )
        .table_validation(
            z.TableCheck.removed_rows(warning=0.2, error=0.4, reject=0.6),
        )
    )


@pytest.fixture
def individual_schema():
    """Schema from README example for individual person data."""
    return z.schema("individual").columns(
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
