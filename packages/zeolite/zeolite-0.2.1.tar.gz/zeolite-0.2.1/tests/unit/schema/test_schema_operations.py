"""
Unit tests for TableSchema class methods.

Tests schema creation, column management, and configuration methods.
"""

import zeolite as z
from zeolite.schema._table import TableSchema


class TestSchemaCreation:
    """Tests for basic schema instantiation."""

    def test_schema_creation(self):
        """Test basic schema creation."""
        # Act
        schema = z.schema("test")

        # Assert
        assert isinstance(schema, TableSchema)
        assert schema._params.name == "test"

    def test_schema_creation_with_columns(self):
        """Test schema creation with initial columns."""
        # Act
        schema = z.schema("test").columns(
            z.col.str("id"),
            z.col.str("name"),
            z.col.int("age"),
        )

        # Assert
        assert isinstance(schema, TableSchema)
        assert len(schema._params.registry.by_name) >= 3  # At least source columns

    def test_schema_optional_flag(self):
        """Test optional parameter."""
        # Act
        required_schema = z.schema("required", optional=False)
        optional_schema = z.schema("optional", optional=True)

        # Assert
        assert required_schema._params.is_required is True
        assert optional_schema._params.is_required is False


class TestColumnsMethod:
    """Tests for .columns() method."""

    def test_add_columns_basic(self):
        """Test adding columns to schema."""
        # Arrange
        schema = z.schema("test")

        # Act
        updated_schema = schema.columns(
            z.col.str("id"),
            z.col.str("name"),
            z.col.int("age"),
        )

        # Assert
        assert len(updated_schema._params.registry.by_name) >= 3


class TestSchemaConfiguration:
    """Tests for schema configuration methods."""

    def test_optional_method(self):
        """Test .optional() method."""
        # Act
        schema = z.schema("test").optional()

        # Assert
        assert schema._params.is_required is False

    def test_strict_method_true(self):
        """Test .strict() method with True."""
        # Act
        schema = z.schema("test").strict(True)

        # Assert
        assert schema._params.strict is True

    def test_strict_method_false(self):
        """Test .strict() method with False."""
        # Act
        schema = z.schema("test").strict(False)

        # Assert
        assert schema._params.strict is False

    def test_coerce_override_method(self):
        """Test .coerce() method."""
        # Act
        default_schema = z.schema("default")
        force_coerce_schema = z.schema("force").coerce("force_strict")
        no_coerce_schema = z.schema("no_coerce").coerce("force_skip_all")

        # Assert
        assert default_schema._params.coerce == "default_true"
        assert force_coerce_schema._params.coerce == "force_strict"
        assert no_coerce_schema._params.coerce == "force_skip_all"

    def test_table_validation_config(self):
        """Test .table_validation() method."""
        # Act
        schema = z.schema("test").table_validation(
            z.TableCheck.removed_rows(warning=0.2, error=0.4, reject=0.6),
            z.TableCheck.min_rows(reject=10),
        )

        # Assert
        assert len(schema._params.table_checks) == 2


class TestSchemaChaining:
    """Tests for method chaining."""

    def test_method_chaining(self):
        """Test chaining multiple configuration methods."""
        # Act
        schema = (
            z.schema("test")
            .strict(True)
            .optional()
            .columns(
                z.col.str("id"),
                z.col.str("name"),
            )
            .table_validation(z.TableCheck.min_rows(reject=1))
        )

        # Assert
        assert schema._params.strict is True
        assert schema._params.is_required is False
        assert len(schema._params.table_checks) == 1
        assert len(schema._params.registry.by_name) >= 2
