from dataclasses import dataclass
from typing import Optional

COLUMN_NAME_PART_DIVIDER = "__"
COLUMN_NAME_SECTION_DIVIDER = "___"

ID_PART_DIVIDER = "::"
ID_SECTION_DIVIDER = ":::"


@dataclass(frozen=True)
class ColumnIdConfig:
    """Configuration for column IDs"""

    base_name: str
    stage: Optional[str] = None
    schema: Optional[str] = None
    is_clean: bool = False
    is_derived: bool = False
    is_check: bool = False
    is_meta: bool = False
    is_custom_check: bool = False
    check_name: Optional[str] = None


def make_column_id(
    name: str,
    *,
    schema: str,
    is_clean: bool = False,
    is_derived: bool = False,
    is_meta: bool = False,
    is_custom_check: bool = False,
    check_name: Optional[str] = None,
    stage: Optional[str] = None,
    alias_name: Optional[str] = None,
    include_schema_prefix: bool = True,
) -> str:
    base_name = parse_column_name_to_config(name).base_name

    schema_parts = []
    if stage and include_schema_prefix:
        schema_parts.append(stage)
    if schema and include_schema_prefix:
        schema_parts.append(schema)

    # Build prefix
    prefix_parts = []
    if is_meta:
        prefix_parts.append("meta")
    if is_derived:
        prefix_parts.append("derived")
    if is_custom_check:
        prefix_parts.append("custom_check")

    # Build type parts
    type_parts = []
    if is_clean:
        type_parts.append("clean")
    if check_name:
        type_parts.append("check")
        type_parts.append(check_name)

    schema_prefix = (
        [ID_PART_DIVIDER.join(schema_parts)] if len(schema_parts) > 0 else []
    )
    attr_prefix = [ID_PART_DIVIDER.join(prefix_parts)] if len(prefix_parts) > 0 else []

    attr_suffix = [ID_PART_DIVIDER.join(type_parts)] if len(type_parts) > 0 else []

    column_id = ID_SECTION_DIVIDER.join(
        [*schema_prefix, *attr_prefix, base_name, *attr_suffix]
    )

    # Add alias if specified
    if alias_name:
        column_id = f"{column_id}{ID_SECTION_DIVIDER}alias{ID_PART_DIVIDER}{alias_name}"

    return column_id


def parse_column_name_to_config(col_name: str) -> ColumnIdConfig:
    """
    Parse a column name string into a ColumnIdConfig

    Args:
        col_name: The column name string to parse

    Returns:
        ColumnIdConfig
    """
    # If no section divider, treat as simple base name
    if COLUMN_NAME_SECTION_DIVIDER not in col_name:
        return ColumnIdConfig(
            base_name=col_name,
        )

    # First split by section divider to get main parts
    sections = col_name.split(COLUMN_NAME_SECTION_DIVIDER)

    # Initialize variables
    base_name = None
    is_clean = False
    is_derived = False
    is_meta = False
    is_custom_check = False
    check_name = None

    # Valid prefixes and suffixes
    VALID_PREFIXES = {"meta", "derived", "custom_check"}
    VALID_SUFFIXES = {"clean", "check"}

    # Process each section
    for i, section in enumerate(sections):
        if not section:
            continue

        parts = section.split(COLUMN_NAME_PART_DIVIDER)

        # First section: check for valid prefixes
        if i == 0:
            # Check if all parts are valid prefixes
            all_valid_prefixes = all(part in VALID_PREFIXES for part in parts)
            if all_valid_prefixes:
                # Set flags for each valid prefix
                for part in parts:
                    if part == "meta":
                        is_meta = True
                    elif part == "derived":
                        is_derived = True
                    elif part == "custom_check":
                        is_custom_check = True
            else:
                # If any part is not a valid prefix, treat whole section as base name
                base_name = section
            continue

        # Last section: check for valid suffixes
        if i == len(sections) - 1:
            # First check if all parts are valid suffixes or their values
            is_valid_suffix_section = True
            for j, part in enumerate(parts):
                if part not in VALID_SUFFIXES and (j == 0 or parts[j - 1] != "check"):
                    is_valid_suffix_section = False
                    break

            if is_valid_suffix_section:
                # Process valid suffixes
                for j, part in enumerate(parts):
                    if part == "check" and j + 1 < len(parts):
                        check_name = parts[j + 1]
                    elif part == "clean":
                        is_clean = True
            else:
                # If any non-suffix parts found, the whole section is base name
                if base_name is None:
                    base_name = section
                else:
                    base_name = f"{base_name}{COLUMN_NAME_SECTION_DIVIDER}{section}"
            continue

        # Everything else is part of the base name
        if base_name is None:
            base_name = section
        else:
            base_name = f"{base_name}{COLUMN_NAME_SECTION_DIVIDER}{section}"

    return ColumnIdConfig(
        base_name=base_name,
        is_clean=is_clean,
        is_derived=is_derived,
        is_meta=is_meta,
        is_custom_check=is_custom_check,
        check_name=check_name,
    )
