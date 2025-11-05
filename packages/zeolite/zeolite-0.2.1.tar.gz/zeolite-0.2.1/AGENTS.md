# AGENTS.md

## Development Commands

This project uses `uv` for package management. Always use `uv` commands instead of `pip`:

```bash
# Install dependencies
uv sync --dev

# Run all tests
uv run pytest

# Run single test file
uv run pytest tests/unit/schema/test_coercion.py

# Run tests matching pattern
uv run pytest -k "test_pattern"

# Run with coverage
uv run pytest --cov=zeolite --cov-report=term-missing

# Lint code
uv run ruff check src/ tests/

# Auto-fix linting issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/
```

## Code Style Guidelines

### Imports
- Use `from typing import` for type hints (modern Python 3.12+ style)
- Import polars as `import polars as pl`
- Group imports: stdlib, third-party, local (zeolite)
- Use relative imports for internal modules

### Types & Formatting
- Use modern type hints: `str | None` instead of `Optional[str]`
- Use `@dataclass(frozen=True, kw_only=True)` for configuration classes
- Follow ruff formatting (configured in project)
- Use snake_case for variables and functions
- Use PascalCase for classes

### Error Handling
- Use specific exception classes from `zeolite.exceptions`
- Configuration errors inherit from `*ConfigurationError` base classes
- Include context (column_name, schema_name) in exceptions when available
- Validate inputs early in constructors/methods

### Testing
- Test files mirror source structure in `tests/unit/`
- Use descriptive test class names: `TestCoerceStringToNumber`
- Use Arrange-Act-Assert pattern
- Test both success and failure cases
- Use fixtures from `conftest.py` for common test data

### Architecture Patterns
- Follow the "variants" pattern for extensibility
- Use method chaining for configuration (`.validations().clean().sensitivity()`)
- Implement `_params` dataclass for configuration storage
- Use `@classmethod method_id()` for variant identification
- Column naming: `column_name__clean`, `column_name__check__{method}`
