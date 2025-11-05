# Test Organization

This directory contains tests organized by purpose and scope.

## Test Categories

### 🔥 `smoke/` - Smoke Tests
**Purpose**: Quick sanity checks that verify basic functionality works at all.

**When to run**: Always run first, before the full test suite.

**What they test**:
- Pipeline doesn't crash with simple valid data
- Basic data types are handled
- Data passes through unchanged when no transformations are applied

**Example**:
```bash
# Run smoke tests only (fast)
pytest tests/smoke/ -v
```

---

### 🔬 `unit/` - Unit Tests
**Purpose**: Test individual components in isolation.

**Structure**:
- `unit/column/` - Column definitions, validations, cleaning
- `unit/ref/` - Column reference system
- `unit/registry/` - Column registry
- `unit/schema/` - Schema operations, coercion, normalization

**What they test**:
- Individual functions and methods
- Specific validation rules
- Type coercion behavior
- Schema configuration methods

**Example**:
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific component tests
pytest tests/unit/column/test_column_validation.py -v
```

---

### 🔗 `integration/` - Integration Tests
**Purpose**: Test complete workflows and realistic scenarios.

**What they test**:
- Full pipeline execution (all 6 stages)
- Data cleaning workflows
- Complex validation scenarios
- README examples
- Multi-column dependencies

**Example**:
```bash
# Run all integration tests
pytest tests/integration/ -v
```

---

### ⚠️ `edge_cases/` - Edge Case Tests
**Purpose**: Test boundary conditions and unusual data scenarios.

**What they test**:
- Empty dataframes
- Single-row datasets
- All null values
- All duplicate values
- 100% validation failure rates
- Unicode and special characters

**Example**:
```bash
# Run all edge case tests
pytest tests/edge_cases/ -v
```

---

### ⚡ `performance/` - Performance Tests
**Purpose**: Test performance with large datasets.

**What they test**:
- 100k+ row processing
- Wide datasets (100+ columns)
- Complex derived column chains
- LazyFrame efficiency

**Example**:
```bash
# Run performance tests
pytest tests/performance/ -v
```

---

## Running Tests

```bash
# Run all tests
pytest

# Run tests by category
pytest tests/smoke/         # Fastest - run first
pytest tests/unit/          # Fast unit tests
pytest tests/integration/   # Slower integration tests
pytest tests/edge_cases/    # Edge case scenarios
pytest tests/performance/   # Slowest - large datasets

# Run with coverage
pytest --cov=zeolite --cov-report=term-missing

# Run specific test
pytest tests/unit/column/test_column_validation.py::TestNotEmptyCheck::test_not_empty_with_none -v
```

## CI/CD Recommendation

```yaml
# Suggested CI pipeline order:
1. Smoke tests (fail fast if fundamentally broken)
2. Unit tests (fast feedback on components)
3. Integration tests (verify workflows)
4. Edge cases (ensure robustness)
5. Performance tests (optional - only on main branch)
```

## Writing New Tests

- **Smoke test**: Does the most basic thing work?
- **Unit test**: Does this specific function/method work correctly?
- **Integration test**: Does this complete workflow work end-to-end?
- **Edge case test**: Does it handle unusual/boundary conditions?
- **Performance test**: Does it scale to large datasets?
