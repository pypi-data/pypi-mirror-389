from collections import defaultdict

from ..types import ColumnNode
from ..exceptions import (
    MissingParentColumnError,
    RegistryIntegrityError,
    CircularDependencyError,
)


# %%
def _detect_circular_dependencies(columns: list[ColumnNode]) -> None:
    """
    Detect circular dependencies in column definitions using DFS.

    Detects both direct cycles (A -> B -> A) and indirect cycles (A -> B -> C -> A).

    Args:
        columns: List of column definitions

    Raises:
        CircularDependencyError: If a circular dependency is detected
    """
    column_by_id = {col.id: col for col in columns}

    # Three states for each node during DFS:
    # - Not visited (not in either set)
    # - Currently visiting (in visiting set) - part of current DFS path
    # - Visited (in visited set) - fully explored
    visiting = set()
    visited = set()

    def dfs(node_id: str, path: list[str]) -> None:
        """Perform DFS to detect cycles."""
        if node_id in visiting:
            # Found a cycle! node_id is already in the current path
            cycle_start_idx = path.index(node_id)
            cycle = path[cycle_start_idx:] + [node_id]

            # Convert IDs to names for readable error message
            cycle_names = [column_by_id[col_id].name for col_id in cycle]
            cycle_str = "` -> `".join(cycle_names)

            raise CircularDependencyError(
                f"Circular dependency detected: `{cycle_str}`",
                cycle=cycle_names,
            )

        if node_id in visited:
            # Already fully explored this node
            return

        # Mark as currently visiting
        visiting.add(node_id)
        path.append(node_id)

        # Visit all dependencies (parents)
        node = column_by_id[node_id]
        for parent_id in node.parent_ids:
            if parent_id in column_by_id:  # Only check parents that exist
                dfs(parent_id, path)

        # Done visiting this node
        visiting.remove(node_id)
        path.pop()
        visited.add(node_id)

    # Start DFS from each unvisited node
    for col in columns:
        if col.id not in visited:
            dfs(col.id, [])


def verify_column_registry_integrity(columns: list[ColumnNode]) -> bool:
    """
    Verify column definitions by checking:
    1. All parent_columns reference existing column names
    2. All parent_ids match existing column IDs
    3. parent_ids are properly mapped from parent_columns
    4. No circular dependencies exist in column references (only if columns have dependencies)

    Args:
        columns: List of column definitions

    Raises:
        MissingParentColumnError: If columns reference non-existent parent columns
        CircularDependencyError: If circular dependencies detected between columns
        RegistryIntegrityError: If multiple validation errors or internal registry issues found

    Returns:
        True if validation passes
    """
    # Create lookup maps
    column_by_id = {col.id: col for col in columns}
    column_by_name = {col.name: col for col in columns}

    # Check source references and mappings
    unmapped_sources = defaultdict(set)
    invalid_parent_ids = defaultdict(set)
    incorrect_mappings = defaultdict(set)

    for col in columns:
        # Check parent columns that don't map to any known column
        unmapped = {src for src in col.parent_columns if src not in column_by_name}
        if unmapped:
            unmapped_sources[col.id].update(unmapped)

        # Check parent_ids that don't exist
        invalid_ids = {
            src_id for src_id in col.parent_ids if src_id not in column_by_id
        }
        if invalid_ids:
            invalid_parent_ids[col.id].update(invalid_ids)

        # Check that all valid parent_columns are properly mapped to parent_ids
        for src in col.parent_columns:
            if src in column_by_name:
                expected_id = column_by_name[src].id
                if expected_id not in col.parent_ids:
                    incorrect_mappings[col.id].add(src)

    # Build error message if any issues found
    errors = []

    if unmapped_sources:
        # Format: column_name → missing parents: [parent1, parent2]
        error_details = "\n".join(
            f"  • {column_by_id[col_id].name} → missing parents: [{', '.join(sorted(refs))}]"
            for col_id, refs in sorted(unmapped_sources.items())
        )
        errors.append(
            f"Columns reference non-existent parent columns:\n{error_details}"
        )

    if invalid_parent_ids:
        error_details = "\n".join(
            f"  • {column_by_id[col_id].name} → invalid IDs: [{', '.join(sorted(refs))}]"
            for col_id, refs in sorted(invalid_parent_ids.items())
        )
        errors.append(f"Invalid parent IDs found:\n{error_details}")

    if incorrect_mappings:
        error_details = "\n".join(
            f"  • {column_by_id[col_id].name} → unmapped sources: [{', '.join(sorted(refs))}]"
            for col_id, refs in sorted(incorrect_mappings.items())
        )
        errors.append(f"Incorrect parent mappings found:\n{error_details}")

    # Raise appropriate exception based on error type
    if errors:
        # If only unmapped sources, use MissingParentColumnError
        if (
            len(errors) == 1
            and unmapped_sources
            and not invalid_parent_ids
            and not incorrect_mappings
        ):
            # Get the first column with missing parents for the exception
            first_col_id = next(iter(unmapped_sources.keys()))
            first_col_name = column_by_id[first_col_id].name
            all_missing = set()
            for refs in unmapped_sources.values():
                all_missing.update(refs)

            raise MissingParentColumnError(
                "\n\n".join(errors),
                column_name=first_col_name,
                missing_parents=all_missing,
            )
        else:
            # Multiple error types or internal registry issues
            raise RegistryIntegrityError("\n\n".join(errors))

    # Only check for circular dependencies if there are columns with dependencies
    # This optimization skips the expensive DFS check for simple schemas
    has_dependencies = any(col.parent_ids for col in columns)
    if has_dependencies:
        _detect_circular_dependencies(columns)

    return True
