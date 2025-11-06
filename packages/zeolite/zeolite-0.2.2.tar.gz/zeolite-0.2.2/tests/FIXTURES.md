# Using Pytest Fixtures in Zeolite Tests

## Overview

All test fixtures are defined in `conftest.py` and are **automatically available** to all tests without importing them. Simply add the fixture name as a parameter to your test function.

## Benefits of Using Fixtures

### Before (without fixtures):
```python
def test_row_removal(self):
    """Test that rows failing validations are removed."""
    # Arrange - 40+ lines of setup
    df = pl.DataFrame({
        "id": ["001", "002", "003", "004", "005", "006", "007", "008", "009", "010"],
        "age": [25, -5, 30, 150, 35, 28, 200, 22, 27, 33],
        "score": [85, 92, 78, 88, 95, 82, 90, 88, 91, 87],
    })

    schema = (
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

    # Act
    result = schema.apply(df)

    # Assert - actual test logic
    assert isinstance(result, ProcessingSuccess)
    assert result.data.collect().shape[0] == 7
    ...
```

### After (with fixtures):
```python
def test_row_removal(row_removal_df, row_removal_schema):
    """Test that rows failing validations are removed."""
    # Act
    result = row_removal_schema.apply(row_removal_df)

    # Assert - focuses on what matters
    assert isinstance(result, ProcessingSuccess)
    assert result.data.collect().shape[0] == 7
    ...
```

**Result**: 64 lines → 23 lines (64% reduction)

## Available Fixtures

### Dataset Fixtures

#### Clean Data
- `valid_simple_df` - Clean 4-row dataset with id, name, age, enrollment_date
- `valid_individuals_df` - Clean person data matching README example

#### Messy Data
- `messy_headers_df` - Column headers with whitespace, case variations, spaces
- `messy_data_df` - Duplicates, nulls, type mismatches, invalid dates

#### Edge Cases
- `empty_df` - DataFrame with columns but zero rows
- `single_row_df` - DataFrame with exactly one row
- `all_nulls_df` - All values are null
- `all_duplicates_df` - All rows are identical

#### Validation Scenarios
- `validation_failing_df` - Multiple validation failures (duplicates, nulls, out-of-range)
- `row_removal_df` - 10 rows with 3 invalid ages (30% failure rate)

### Schema Fixtures

#### Basic Schemas
- `simple_schema` - Basic schema with validation (id unique/not empty, name, age, date)
- `minimal_schema` - Minimal schema with no validations

#### Feature Schemas
- `validation_schema` - Tests various validation rules (not_empty, unique, in_range, str_matches)
- `cleaning_schema` - Tests cleaning operations (id, date, enum, boolean, string)
- `row_removal_schema` - Schema with remove_row_on_fail and table validation
- `individual_schema` - README example schema for individual person data

### Legacy Fixtures (for backwards compatibility)
- `sample_df` - Generic sample DataFrame
- `sample_threshold` - Sample Threshold configuration
- `sample_column_node` - Sample ColumnNode
- `sample_error_levels` - Error level constants

## Usage Examples

### Example 1: Simple Test
```python
def test_validation_with_clean_data(valid_simple_df, validation_schema):
    """Test validation passes with clean data."""
    result = validation_schema.apply(valid_simple_df)
    assert isinstance(result, ProcessingSuccess)
```

### Example 2: Multiple Fixtures
```python
def test_compare_schemas(valid_simple_df, simple_schema, minimal_schema):
    """Compare results from different schemas."""
    result1 = simple_schema.apply(valid_simple_df)
    result2 = minimal_schema.apply(valid_simple_df)

    assert isinstance(result1, ProcessingSuccess)
    assert isinstance(result2, ProcessingSuccess)
```

### Example 3: Parameterized Testing
```python
@pytest.mark.parametrize("df_fixture", [
    "valid_simple_df",
    "messy_data_df",
    "single_row_df",
])
def test_schema_handles_various_data(df_fixture, simple_schema, request):
    """Test schema handles different data scenarios."""
    df = request.getfixturevalue(df_fixture)
    result = simple_schema.apply(df)
    assert result is not None  # Should not crash
```

### Example 4: Test Only What Matters
```python
# Before: Had to define both data and schema
def test_old_way(self):
    df = pl.DataFrame({...})  # 20 lines
    schema = z.schema(...).columns(...)  # 30 lines
    result = schema.apply(df)
    assert result.data.collect().shape[0] == expected  # THE ACTUAL TEST

# After: Just test the logic
def test_new_way(validation_failing_df, validation_schema):
    result = validation_schema.apply(validation_failing_df)
    # Focus on assertions, not setup
    assert isinstance(result, ProcessingFailure)
    assert "duplicate" in str(result.errors)
```

## When to Create New Fixtures

### DO create a fixture when:
- ✅ The same data/schema is used in 3+ tests
- ✅ The setup is complex (>10 lines)
- ✅ Multiple tests need slight variations of the same data
- ✅ You want to parameterize tests with different datasets

### DON'T create a fixture when:
- ❌ It's only used in one test
- ❌ The data is trivial (1-2 lines)
- ❌ The test needs to modify the data (unless you use scope='function')

## Adding New Fixtures

Add fixtures to `tests/conftest.py`:

```python
@pytest.fixture
def my_new_dataset():
    """Description of what this dataset represents."""
    return pl.DataFrame({
        "col1": [1, 2, 3],
        "col2": ["a", "b", "c"],
    })

@pytest.fixture
def my_new_schema():
    """Description of what this schema tests."""
    return z.schema("my_schema").columns(
        z.col.int("col1"),
        z.col.str("col2"),
    )
```

## Fixture Scopes

```python
@pytest.fixture(scope="function")  # Default - fresh for each test
def mutable_df():
    return pl.DataFrame({...})

@pytest.fixture(scope="module")  # Created once per test file
def expensive_df():
    # Expensive to create, but tests don't modify it
    return pl.DataFrame({...large dataset...})

@pytest.fixture(scope="session")  # Created once for entire test session
def very_expensive_schema():
    # Use sparingly - shared across ALL tests
    return z.schema(...complex schema...)
```

## Tips & Tricks

### 1. Composing Fixtures
```python
@pytest.fixture
def base_df():
    return pl.DataFrame({"id": ["001", "002"]})

@pytest.fixture
def enriched_df(base_df):
    # Build on top of another fixture
    return base_df.with_columns(name=["Alice", "Bob"])
```

### 2. Fixture with Parameters
```python
@pytest.fixture(params=[5, 10, 100])
def various_sizes(request):
    n = request.param
    return pl.DataFrame({"id": list(range(n))})

# This test runs 3 times automatically!
def test_with_various_sizes(various_sizes):
    assert various_sizes.shape[0] in [5, 10, 100]
```

### 3. Conditional Fixtures
```python
@pytest.fixture
def df_with_nulls(request):
    if request.config.getoption("--strict"):
        return pl.DataFrame({...no nulls...})
    return pl.DataFrame({...with nulls...})
```

## Migration Guide

To migrate existing tests to use fixtures:

1. **Identify repeated code**: Look for DataFrames/schemas defined multiple times
2. **Check if fixture exists**: Search `conftest.py` for existing fixtures
3. **Add parameter**: Add fixture name to test function parameters
4. **Remove setup code**: Delete the DataFrame/schema creation code
5. **Run tests**: Verify everything still works

## Questions?

- See pytest fixtures documentation: https://docs.pytest.org/en/stable/fixture.html
- Check `tests/conftest.py` for all available fixtures
- Look at `tests/integration/test_realistic_scenarios.py::TestRowRemoval::test_remove_rows_workflow` for an example
