from ._table import TableSchema


schema = TableSchema
"""
Defines a table schema for data validation and processing.

Parameters:
    name (str): Name of the schema.
    columns (List[ColumnSchema] | dict[str, ColumnSchema], optional): List of column schemas.
    is_required (bool): Whether the schema is required.
    stage (str, optional): Processing stage.

Example:
    demo_schema = z.schema("demo", columns=[...])
"""


__all__ = ["TableSchema", "schema"]
