# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Zeolite is a Python library that uses a configuration-based approach to define table/schema structures for normalizing, cleaning, and validating raw data in a performant and standardized way. Built on top of Polars for high-performance data processing.

## Development Commands

### Package Management
This project uses `uv` for package management. Always use `uv` commands instead of `pip`:

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --dev

# Add a new dependency
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Run commands in the project environment
uv run <command>
```

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/column/test_column_validation.py

# Run tests matching a pattern
uv run pytest -k "test_pattern"

# Run tests with coverage
uv run pytest --cov=zeolite --cov-report=term-missing
```

### Linting

```bash
# Run ruff linter
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/
```

## Architecture Overview

### Multi-Stage Processing Pipeline

The core of Zeolite is a 6-stage pipeline implemented in `src/zeolite/schema/_table.py` (TableSchema class):

1. **Normalise** (`step_1_normalise_table_structure`) - Aligns column headers with schema definitions using column variants
2. **Coerce** (`step_2_coerce_datatypes`) - Coerces data types to match schema definitions
3. **Prepare** (`step_3_prepare_additional_columns`) - Appends cleaned, derived, and validation check columns
4. **Validate** (`step_4_validate_columns`) - Evaluates validation rules against thresholds
5. **Filter** (`step_5_validate_and_filter_table`) - Removes rows that failed checks, evaluates table-level validations
6. **Refine** (`step_6_refine_structure`) - Produces final dataset by renaming/dropping working columns

Each stage returns a `ValidationResult` containing the processed LazyFrame, errors, and a reject flag. The `apply()` method orchestrates all stages and returns either `ProcessingSuccess` or `ProcessingFailure`.

### Core Components

#### Column Registry System
- **Location**: `src/zeolite/registry/__init__.py`
- **Purpose**: Central registry that tracks all column nodes (source, derived, cleaned, validation) in the schema
- Maintains `by_id` and `by_name` lookups for fast column resolution
- Handles dependency tracking between columns via parent-child relationships
- Used to generate optimized execution stages for column transformations

#### Column Reference System
- **Location**: `src/zeolite/ref/_reference.py`
- **Purpose**: Provides a type-safe way to reference columns in expressions (e.g., `z.ref("column_name")`)
- `ColumnRef` encodes column metadata (schema, stage, is_clean, is_derived, is_meta, check_name) into unique IDs
- Enables chaining: `z.ref("ethnicity").clean().col.eq("maori")` - references the cleaned version of a column
- Column IDs use a hierarchical format: `{stage}__{schema}__{name}__clean__check__{check_name}`

#### Column Definitions (Col)
- **Location**: `src/zeolite/column/_base/__init__.py`
- **Factory**: `src/zeolite/column/__init__.py` (ColFactory pattern)
- Defines column structure including data type, sensitivity, variants (alternate column names), validations, and cleaning operations
- Each `Col` generates multiple `ColumnNode` objects: source node, cleaned node (if cleaning defined), validation nodes (one per check)
- **Types**: source columns (from raw data), derived columns (computed from expressions), meta columns (added during ingestion), custom check columns (custom validation expressions)

#### The "Variants" Pattern
The codebase uses a variants pattern for extensibility in two areas:

1. **Column Validation Variants** (`src/zeolite/column/validation/variants/`)
   - Individual check implementations: `_string.py`, `_number.py`, `_date.py`, `_null.py`, `_unique.py`, etc.
   - Each extends `BaseCheck` and implements `expression()` method to generate validation Polars expressions
   - Accessible via `z.Check.not_empty()`, `z.Check.unique()`, etc.

2. **Schema/Table Validation Variants** (`src/zeolite/schema/validation/variants/`)
   - Table-level checks: `_removed_rows.py`, `_min_rows.py`
   - Validate aggregate properties (e.g., percentage of rows removed, minimum row count)
   - Accessible via `z.TableCheck.removed_rows()`, `z.TableCheck.min_rows()`

3. **Column Cleaning Variants** (`src/zeolite/column/_clean/`)
   - Data transformation implementations: `_string.py`, `_number.py`, `_date.py`, `_boolean.py`, `_enum.py`, `_id.py`
   - Each extends `CleanColumn` base class
   - Accessible via `z.Clean.sanitised_string()`, `z.Clean.enum()`, `z.Clean.date()`, etc.

All variants follow a common pattern:
- Extend a base class (`BaseCheck`, `BaseTableCheck`, or `CleanColumn`)
- Use a `_params` dataclass to store configuration
- Implement a key method (`expression()` for checks, `clean_expr()` for cleaning)
- Support method chaining for configuration

#### Threshold System
- **Location**: `src/zeolite/types/validation/threshold.py`
- Validation checks produce results at different severity levels: `debug`, `warning`, `error`, `reject`
- Thresholds can be:
  - Boolean (`True`/`False`) - triggers at any occurrence
  - Numeric (0.0-1.0) - triggers when percentage of failures exceeds threshold
  - Literal (`"any"`, `"all"`) - triggers when any or all rows fail
- `reject` threshold causes the pipeline to abort in strict mode
- `remove_row_on_fail=True` removes failing rows during the filter stage

#### Optimized Execution Stages
- **Location**: `src/zeolite/registry/optimise_calc_stages.py`
- Analyzes column dependencies to determine optimal execution order
- Groups independent columns into parallel execution stages
- Ensures derived columns are computed after their dependencies
- Critical for performance with complex column transformations

### Key Data Flow

1. User defines schema: `z.schema("name").columns(z.col.str("id").clean(...).validations(...))`
2. Each `Col` generates `ColumnNode` objects added to the `ColumnRegistry`
3. Registry resolves parent-child dependencies between nodes
4. On `schema.apply(df)`:
   - Normalise stage maps raw column names to schema columns using variants
   - Coerce stage casts columns to target data types
   - Prepare stage generates optimized execution stages and applies all transformations
   - Validate stage evaluates check columns against thresholds
   - Filter stage removes failing rows and runs table-level checks
   - Refine stage selects final columns and applies aliases

### Column Naming Conventions

Working columns use prefixes to identify their purpose:
- Source columns: `column_name`
- Cleaned columns: `column_name__clean`
- Validation check columns: `column_name__check__{check_method}` or `column_name__clean__check__{check_method}`
- Derived columns: `derived__{column_name}`
- Meta columns: `meta__{column_name}`
- Custom check columns: `derived__custom_check__{column_name}`

The refine stage uses aliases to rename these back to clean final names.

### Sensitivity System

The `Sensitivity` enum tracks data sensitivity levels for compliance/privacy purposes. Set on columns and inherited by cleaned/derived columns unless explicitly overridden.

## Testing Guidelines

- Test files mirror source structure: `tests/unit/column/` corresponds to `src/zeolite/column/`
- Use fixtures from `tests/conftest.py` for common test data
- Test both success and failure cases for validations
- Test threshold behavior (debug, warning, error, reject levels)
- Use Polars DataFrames/LazyFrames in tests to match production usage
