from zeolite.ref import parse_column_name, ColumnRef
from zeolite._utils.column_id import (
    COLUMN_NAME_PART_DIVIDER as PD,
    COLUMN_NAME_SECTION_DIVIDER as SD,
)


def test_simple_base_name():
    """Test parsing a simple base name"""
    result = parse_column_name("foo")
    assert result == ColumnRef(
        base_name="foo",
        is_clean=False,
        is_derived=False,
        is_meta=False,
        is_custom_check=False,
        check_name=None,
    )


def test_base_name_with_sections():
    """Test parsing a base name with multiple sections"""
    result = parse_column_name(f"foo{SD}bar{SD}baz")
    assert result == ColumnRef(
        base_name=f"foo{SD}bar{SD}baz",
        is_clean=False,
        is_derived=False,
        is_meta=False,
        is_custom_check=False,
        check_name=None,
    )


def test_valid_single_prefix():
    """Test parsing with a single valid prefix"""
    result = parse_column_name(f"meta{SD}foo")
    assert result == ColumnRef(
        base_name="foo",
        is_clean=False,
        is_derived=False,
        is_meta=True,
        is_custom_check=False,
        check_name=None,
    )


def test_valid_prefixes():
    """Test parsing with valid prefixes"""
    result = parse_column_name(f"meta{PD}derived{SD}foo")
    assert result == ColumnRef(
        base_name="foo",
        is_clean=False,
        is_derived=True,
        is_meta=True,
        is_custom_check=False,
        check_name=None,
    )


def test_invalid_prefix_section():
    """Test parsing when first section contains non-prefix parts"""
    result = parse_column_name(f"foo{SD}bam")
    assert result == ColumnRef(
        base_name=f"foo{SD}bam",
        is_clean=False,
        is_derived=False,
        is_meta=False,
        is_custom_check=False,
        check_name=None,
    )


def test_valid_suffixes():
    """Test parsing with valid suffixes"""
    result = parse_column_name(f"foo{SD}clean{PD}check{PD}is_empty")
    assert result == ColumnRef(
        base_name="foo",
        is_clean=True,
        is_derived=False,
        is_meta=False,
        is_custom_check=False,
        check_name="is_empty",
    )


def test_invalid_suffix_section():
    """Test parsing when last section contains non-suffix parts"""
    test_cases = [
        f"foo{SD}clean{PD}popsicle",
        f"foo{SD}clean{PD}popsicle{PD}check{PD}is_empty",
        f"foo{SD}clean{PD}check{PD}is_empty{PD}popsicle",
    ]

    for test_case in test_cases:
        result = parse_column_name(test_case)
        assert result == ColumnRef(
            base_name=test_case,
            is_clean=False,
            is_derived=False,
            is_meta=False,
            is_custom_check=False,
            check_name=None,
        )


def test_complex_cases():
    """Test parsing complex combinations"""
    test_cases = [
        (
            f"meta{PD}derived{SD}foo{SD}bar{SD}clean{PD}check{PD}is_empty",
            ColumnRef(
                base_name=f"foo{SD}bar",
                is_clean=True,
                is_derived=True,
                is_meta=True,
                is_custom_check=False,
                check_name="is_empty",
            ),
        ),
        (
            f"meta{SD}bam{SD}clean{PD}check{PD}is_empty",
            ColumnRef(
                base_name="bam",
                is_clean=True,
                is_derived=False,
                is_meta=True,
                is_custom_check=False,
                check_name="is_empty",
            ),
        ),
        (
            f"bam{SD}popsicle",
            ColumnRef(
                base_name=f"bam{SD}popsicle",
                is_clean=False,
                is_derived=False,
                is_meta=False,
                is_custom_check=False,
                check_name=None,
            ),
        ),
    ]

    for test_case, expected in test_cases:
        result = parse_column_name(test_case)
        assert result == expected, f"Failed for {test_case}"


def test_multiple_valid_prefixes():
    """Test parsing with multiple valid prefixes in first section"""
    test_cases = [
        (
            f"meta{PD}derived{PD}custom_check{SD}foo",
            ColumnRef(
                base_name="foo",
                is_clean=False,
                is_derived=True,
                is_meta=True,
                is_custom_check=True,
                check_name=None,
            ),
        ),
        (
            f"derived{PD}meta{SD}foo",
            ColumnRef(
                base_name="foo",
                is_clean=False,
                is_derived=True,
                is_meta=True,
                is_custom_check=False,
                check_name=None,
            ),
        ),
    ]

    for test_case, expected in test_cases:
        result = parse_column_name(test_case)
        assert result == expected, f"Failed for {test_case}"


def test_multiple_valid_suffixes():
    """Test parsing with multiple valid suffixes in last section"""
    test_cases = [
        (
            f"foo{SD}clean{PD}check{PD}is_empty{PD}check{PD}is_null",
            ColumnRef(
                base_name="foo",
                is_clean=True,
                is_derived=False,
                is_meta=False,
                is_custom_check=False,
                check_name="is_null",  # Last check takes precedence
            ),
        ),
        (
            f"foo{SD}check{PD}is_empty{PD}clean",
            ColumnRef(
                base_name="foo",
                is_clean=True,
                is_derived=False,
                is_meta=False,
                is_custom_check=False,
                check_name="is_empty",
            ),
        ),
    ]

    for test_case, expected in test_cases:
        result = parse_column_name(test_case)
        assert result == expected, f"Failed for {test_case}"
