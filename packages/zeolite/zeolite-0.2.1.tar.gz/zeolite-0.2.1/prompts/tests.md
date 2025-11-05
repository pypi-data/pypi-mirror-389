# Comprehensive Test Implementation Plan for Zeolite

## Overview
Based on my analysis, the current test suite has **good coverage for validation logic** but is **missing critical end-to-end and integration tests**. This plan will fill those gaps and ensure all components work correctly with real datasets.

## Current State
- ✅ Validation variants well tested (444 lines)
- ✅ Registry system tested (372 lines)
- ✅ Column name parsing tested (307 lines)
- ✅ BaseCheck configuration tested (214 lines)
- ❌ **Zero end-to-end pipeline tests**
- ❌ **Zero data cleaning tests**
- ❌ **Zero schema application tests**
- ❌ **Zero normalisation/coercion tests**
- ❌ **Zero table-level validation tests**

## Implementation Plan

### Phase 1: Core Integration Tests (Priority 1)

#### Test File 1: `tests/integration/test_full_pipeline.py`
**Purpose**: Test the complete 6-stage pipeline end-to-end

**Test Cases**:
1. `test_successful_pipeline_simple_schema()`
   - Clean data passing all stages
   - Verify ProcessingSuccess returned
   - Check all stage snapshots populated
   - Validate final data structure

2. `test_pipeline_failure_at_normalise_stage()`
   - Missing required column
   - Verify ProcessingFailure with failed_stage="normalise"
   - Check error messages

3. `test_pipeline_failure_at_coerce_stage()`
   - Invalid data type that can't be coerced
   - Verify failure at coerce stage
   - Check intermediate results available

4. `test_pipeline_failure_at_validate_stage()`
   - Data failing validation with reject threshold
   - Verify validation errors captured
   - Check rejected rows identified

5. `test_pipeline_failure_at_filter_stage()`
   - Table validation failing (e.g., too many rows removed)
   - Verify table-level errors

6. `test_strict_vs_non_strict_mode()`
   - Same schema/data in both modes
   - Verify strict aborts on first reject
   - Verify non-strict continues and collects all errors

7. `test_error_accumulation_across_stages()`
   - Multiple warnings/errors at different stages
   - Verify all collected in final result

8. `test_stage_snapshots_accessible()`
   - Access normalised, coerced, prepared, validated, filtered, refined DataFrames
   - Verify each has expected transformations

**Fixtures Needed**:
- `simple_valid_df`: Clean DataFrame
- `simple_schema`: Basic schema matching the DataFrame
- `invalid_type_df`: Data with type mismatches
- `validation_failing_df`: Data failing validation thresholds

---

#### Test File 2: `tests/integration/test_data_cleaning.py`
**Purpose**: Test all cleaning variants with realistic data

**Test Cases**:

1. **ID Cleaning**:
   - `test_clean_id_with_prefix()` - Add prefix to IDs
   - `test_clean_id_handles_nulls()` - Null values preserved
   - `test_clean_id_with_existing_prefix()` - Deduplicate prefix

2. **Date Cleaning**:
   - `test_clean_date_iso_format()` - "2023-01-01"
   - `test_clean_date_excel_serial()` - Excel dates like "44927"
   - `test_clean_date_various_formats()` - Multiple format parsing
   - `test_clean_date_invalid_values()` - "invalid", nulls
   - `test_clean_date_with_timezone()` - ISO with timezone

3. **Enum Cleaning**:
   - `test_clean_enum_exact_match()` - Direct enum_map matches
   - `test_clean_enum_case_variations()` - "Male", "male", "MALE"
   - `test_clean_enum_with_sanitise()` - Trim/lowercase before mapping
   - `test_clean_enum_unknown_values()` - Values not in enum_map
   - `test_clean_enum_null_handling()` - Null preservation

4. **Boolean Cleaning**:
   - `test_clean_boolean_true_values()` - "yes", "active", "true", "1", True
   - `test_clean_boolean_false_values()` - "no", "inactive", "false", "0", False
   - `test_clean_boolean_invalid_values()` - Unknown strings -> null

5. **String Cleaning**:
   - `test_clean_string_full_sanitise()` - Trim + lowercase + remove special chars
   - `test_clean_string_lowercase_only()` - Just lowercase
   - `test_clean_string_trim_only()` - Just trim whitespace
   - `test_clean_string_preserve_case()` - No transformation
   - `test_clean_string_unicode()` - Handle unicode characters

6. **Number Cleaning**:
   - `test_clean_number_from_string()` - "123" -> 123
   - `test_clean_number_with_commas()` - "1,234.56" -> 1234.56
   - `test_clean_number_invalid()` - "abc" -> null

7. **Alias Behavior**:
   - `test_clean_with_alias()` - Cleaned column uses alias
   - `test_clean_without_alias()` - Replaces original column

**Dataset**: Create realistic messy data for each cleaning type

---

#### Test File 3: `tests/integration/test_realistic_scenarios.py`
**Purpose**: Test complete workflows matching README examples and real use cases

**Test Cases**:

1. `test_readme_example_individual_data()`
   - Exact example from README.md
   - Verify all transformations work
   - Check derived columns computed correctly
   - Validate row removal works

2. `test_messy_csv_import_scenario()`
   - Simulated CSV with:
     - Extra whitespace in headers
     - Case variations in column names
     - Mixed date formats
     - Empty strings vs nulls
     - Special characters
   - Verify normalization handles all cases
   - Check cleaning produces consistent output

3. `test_multiple_validation_failures()`
   - Dataset with various quality issues:
     - Some duplicates
     - Some nulls
     - Some out of range
     - Some invalid formats
   - Verify thresholds evaluated correctly
   - Check different severity levels assigned

4. `test_derived_column_dependencies()`
   - Column A derived from source
   - Column B derived from cleaned A
   - Column C derived from A + B
   - Verify execution order correct
   - Check all computed values accurate

5. `test_custom_check_validations()`
   - Custom validation expressions
   - Multi-column validation logic
   - Verify thresholds work on custom checks

6. `test_remove_rows_workflow()`
   - Some validations with remove_row_on_fail=True
   - Verify rows removed during filter stage
   - Check final dataset excludes failed rows
   - Validate table checks see removed rows

**Datasets**: Real-world-like data with multiple issues

---

### Phase 2: Unit Tests for Coverage Gaps (Priority 2)

#### Test File 4: `tests/unit/schema/test_schema_operations.py`
**Purpose**: Test TableSchema class methods

**Test Cases**:
1. `test_schema_creation()` - Basic instantiation
2. `test_add_columns_merge()` - .columns() with merge
3. `test_add_columns_replace()` - .columns() with replace
4. `test_optional_flag()` - .optional() method
5. `test_strict_mode()` - .strict() method
6. `test_coerce_override()` - .coerce() method
7. `test_table_validation_config()` - .table_validation() method
8. `test_duplicate_column_names()` - Error handling

---

#### Test File 5: `tests/unit/schema/test_normalisation.py`
**Purpose**: Test step_1_normalise_table_structure

**Test Cases**:
1. `test_normalise_exact_match()` - Headers match schema exactly
2. `test_normalise_case_insensitive()` - "Name" matches "name"
3. `test_normalise_with_variants()` - "full_name" matches "name" via variants
4. `test_normalise_missing_required()` - Error when required column missing
5. `test_normalise_missing_optional()` - No error for optional
6. `test_normalise_extra_columns_strict()` - Extra columns dropped in strict mode
7. `test_normalise_adds_missing_columns()` - Missing columns added as null

---

#### Test File 6: `tests/unit/schema/test_coercion.py`
**Purpose**: Test step_2_coerce_datatypes

**Test Cases**:
1. `test_coerce_string_to_int()` - "123" -> 123
2. `test_coerce_string_to_float()` - "123.45" -> 123.45
3. `test_coerce_string_to_bool()` - Various string -> bool
4. `test_coerce_string_to_date()` - Various formats -> date
5. `test_coerce_with_override_true()` - Force coercion
6. `test_coerce_with_override_false()` - Skip coercion
7. `test_coerce_with_default()` - Default behavior per type
8. `test_coerce_failures()` - Invalid data handling

---

#### Test File 7: `tests/unit/schema/test_table_validations.py`
**Purpose**: Test table-level validation checks

**Test Cases**:
1. `test_removed_rows_under_threshold()` - Pass when under threshold
2. `test_removed_rows_at_warning()` - Warning level triggered
3. `test_removed_rows_at_error()` - Error level triggered
4. `test_removed_rows_at_reject()` - Reject level triggered
5. `test_min_rows_pass()` - Sufficient rows present
6. `test_min_rows_fail()` - Too few rows, reject
7. `test_multiple_table_checks()` - Combined checks
8. `test_table_check_with_no_removals()` - Edge case: no rows removed

---

#### Test File 8: `tests/unit/column/test_derived_columns.py`
**Purpose**: Test derived column functionality

**Test Cases**:
1. `test_simple_derived_column()` - Basic expression
2. `test_derived_from_cleaned()` - Use .clean() ref
3. `test_derived_with_multiple_sources()` - Multi-column expression
4. `test_custom_check_column()` - Custom validation expression
5. `test_derived_dependency_chain()` - A -> B -> C dependencies
6. `test_derived_execution_order()` - Verify correct stage order

---

#### Test File 9: `tests/unit/column/test_cleaning_variants.py`
**Purpose**: Individual cleaning variant unit tests

**Test Cases**: (Similar to integration but more focused)
- Test each Clean variant in isolation
- Edge cases (nulls, empty, invalid)
- Output data types
- Alias functionality

---

#### Test File 10: `tests/unit/ref/test_column_references.py`
**Purpose**: Test column reference system

**Test Cases**:
1. `test_ref_creation()` - Basic ref()
2. `test_ref_clean_chaining()` - ref().clean()
3. `test_ref_col_property()` - ref().col for expressions
4. `test_ref_resolution_in_registry()` - Resolve to ColumnNode
5. `test_ref_meta()` - Meta column refs
6. `test_ref_derived()` - Derived column refs
7. `test_ref_custom_check()` - Custom check refs
8. `test_ref_in_expressions()` - Usage in pl.Expr

---

### Phase 3: Test Fixtures & Utilities (Priority 3)

#### File: `tests/fixtures/datasets.py`
**Purpose**: Reusable test datasets

**Contents**:
```python
# Clean, valid datasets
VALID_INDIVIDUALS_DF
VALID_SIMPLE_DF

# Messy datasets
MESSY_HEADERS_DF  # Case variations, whitespace
MESSY_DATA_DF     # Type issues, nulls, duplicates
MIXED_DATES_DF    # Various date formats

# Edge cases
EMPTY_DF
SINGLE_ROW_DF
ALL_NULLS_DF
ALL_DUPLICATES_DF
LARGE_DF  # 10k+ rows

# Specific scenarios
EXCEL_DATES_DF
UNICODE_DATA_DF
SPECIAL_CHARS_DF
```

---

#### File: `tests/fixtures/schemas.py`
**Purpose**: Reusable schema definitions

**Contents**:
```python
# Simple schemas
SIMPLE_SCHEMA
INDIVIDUAL_SCHEMA  # From README

# Feature-specific schemas
CLEANING_SCHEMA  # All cleaning variants
VALIDATION_SCHEMA  # All validation variants
DERIVED_SCHEMA  # Derived columns
TABLE_VALIDATION_SCHEMA  # Table checks

# Edge case schemas
STRICT_SCHEMA
NON_STRICT_SCHEMA
ALL_OPTIONAL_SCHEMA
```

---

#### File: `tests/conftest.py` (enhance existing)
**Purpose**: Shared fixtures and utilities

**Add**:
- Parameterized threshold fixtures
- Dataset generators
- Assertion helpers for ValidationResult
- Polars DataFrame comparison utilities

---

### Phase 4: Performance & Edge Case Tests (Priority 4)

#### File: `tests/performance/test_large_datasets.py`
**Test Cases**:
1. `test_100k_rows_simple_schema()` - Performance baseline
2. `test_wide_dataset_100_columns()` - Many columns
3. `test_complex_derived_chains()` - Deep dependency trees
4. `test_memory_usage()` - LazyFrame memory efficiency

---

#### File: `tests/edge_cases/test_edge_cases.py`
**Test Cases**:
1. Empty DataFrames
2. Single value columns
3. All nulls scenarios
4. 100% validation failures
5. Circular dependencies (should error)
6. Invalid schema configurations

---

## Implementation Schedule

**Week 1: Foundation**
- Day 1-2: `test_full_pipeline.py` (8 tests)
- Day 3-4: `test_data_cleaning.py` (ID, Date, Enum - 10 tests)
- Day 5: `test_data_cleaning.py` (Boolean, String, Number - 8 tests)

**Week 2: Realistic Scenarios**
- Day 1-2: `test_realistic_scenarios.py` (6 tests)
- Day 3: `test_schema_operations.py` (8 tests)
- Day 4: `test_normalisation.py` (7 tests)
- Day 5: `test_coercion.py` (8 tests)

**Week 3: Remaining Coverage**
- Day 1: `test_table_validations.py` (8 tests)
- Day 2: `test_derived_columns.py` (6 tests)
- Day 3: `test_cleaning_variants.py` (focused unit tests)
- Day 4: `test_column_references.py` (8 tests)
- Day 5: Fixtures (datasets.py, schemas.py)

**Week 4: Quality & Performance**
- Day 1-2: Performance tests
- Day 3: Edge case tests
- Day 4: Documentation and test organization
- Day 5: Code coverage analysis and fill remaining gaps

---

## Success Metrics

-  90%+ code coverage
-  All 6 pipeline stages tested end-to-end
-  All cleaning variants tested with real data
-  All validation variants tested (already done)
-  Table validations tested
-  README examples have corresponding tests
-  Performance baselines established
-  Edge cases documented

---

## Testing Guidelines

1. **Use realistic data** - Not just [1,2,3], use actual messy CSV-like data
2. **Test the happy path AND failures** - Both pass and fail scenarios
3. **Check intermediate results** - Don't just test final output, verify stage snapshots
4. **Use parametrize for variants** - When testing similar cases with different inputs
5. **Clear assertions** - Check specific values, not just "assert result"
6. **Document edge cases** - Comment why certain edge cases exist
7. **Keep tests focused** - One test should verify one behavior

---

## File Structure After Implementation

```
tests/
├── conftest.py (enhanced)
├── fixtures/
│   ├── __init__.py
│   ├── datasets.py
│   └── schemas.py
├── integration/
│   ├── __init__.py
│   ├── test_full_pipeline.py ⭐ NEW
│   ├── test_data_cleaning.py ⭐ NEW
│   └── test_realistic_scenarios.py ⭐ NEW
├── unit/
│   ├── column/
│   │   ├── test_appending_check_columns.py ✅ EXISTS
│   │   ├── test_column_validation.py ✅ EXISTS
│   │   ├── test_cleaning_variants.py ⭐ NEW
│   │   └── test_derived_columns.py ⭐ NEW
│   ├── ref/
│   │   ├── test_column_name_parsing.py ✅ EXISTS
│   │   └── test_column_references.py ⭐ NEW
│   ├── registry/
│   │   └── test_registry.py ✅ EXISTS
│   └── schema/
│       ├── __init__.py ⭐ NEW
│       ├── test_schema_operations.py ⭐ NEW
│       ├── test_normalisation.py ⭐ NEW
│       ├── test_coercion.py ⭐ NEW
│       └── test_table_validations.py ⭐ NEW
├── performance/
│   ├── __init__.py ⭐ NEW
│   └── test_large_datasets.py ⭐ NEW
└── edge_cases/
    ├── __init__.py ⭐ NEW
    └── test_edge_cases.py ⭐ NEW
```

Total: **~15 new test files, ~120 new test cases**
