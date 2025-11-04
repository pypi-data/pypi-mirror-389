from polars import DataFrame
from zeolite.column.validation import Check, BaseCheck
from zeolite.types.validation.threshold import Threshold
from zeolite.ref import ref


# Test BaseCheck functionality
def test_base_check_initialization():
    check = BaseCheck(
        remove_row_on_fail=True,
        alias="test_check",
        check_on_cleaned=True,
        message="Test message",
        thresholds=Threshold(warning=True, error=True),
    )

    assert check.params.remove_row_on_fail is True
    assert check.params.alias == "test_check"
    assert check.params.check_on_cleaned is True
    assert check.params.message == "Test message"
    assert check.params.thresholds.warning is True
    assert check.params.thresholds.error is True


def test_base_check_threshold_configuration():
    check = BaseCheck()

    # Test individual threshold methods
    check_with_warning = check.warning(True)
    assert check_with_warning.params.thresholds.warning is True

    check_with_error = check.error(True)
    assert check_with_error.params.thresholds.error is True

    check_with_reject = check.reject("all")
    assert check_with_reject.params.thresholds.reject == "all"

    # Test combined thresholds
    check_with_all = check.thresholds(
        debug=True, warning=True, error=True, reject="all"
    )
    assert check_with_all.params.thresholds.debug is True
    assert check_with_all.params.thresholds.warning is True
    assert check_with_all.params.thresholds.error is True
    assert check_with_all.params.thresholds.reject == "all"


def test_base_check_utility_methods():
    check = BaseCheck()

    # Test alias
    check_with_alias = check.alias("new_alias")
    assert check_with_alias.params.alias == "new_alias"

    # Test message
    check_with_message = check.message("new message")
    assert check_with_message.params.message == "new message"

    # Test check_on_cleaned
    check_with_cleaned = check.check_on_cleaned(True)
    assert check_with_cleaned.params.check_on_cleaned is True

    # Test remove_row_on_fail
    check_with_remove = check.remove_row_on_fail(True)
    assert check_with_remove.params.remove_row_on_fail is True


# Test specific validation checks
def test_not_null_validation():
    df = DataFrame(
        {
            "source_col": [1, 2, None, 4],
        }
    )
    chk = Check.not_null(warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    expected = ["pass", "pass", "fail", "pass"]
    assert test_df[node.name].to_list() == expected


def test_not_null_validation_with_remove():
    df = DataFrame(
        {
            "source_col": [1, 2, None, 4],
        }
    )
    chk = Check.not_null(warning="any").remove_row_on_fail()
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    expected = ["pass", "pass", "reject", "pass"]
    assert test_df[node.name].to_list() == expected


def test_unique_validation():
    df = DataFrame(
        {
            "source_col": [1, 2, 2, 3, 3, 4],
        }
    )
    chk = Check.unique(warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    expected = ["pass", "fail", "fail", "fail", "fail", "pass"]
    assert test_df[node.name].to_list() == expected


def test_equality_validation():
    df = DataFrame(
        {
            "source_col": [1, 5, 3, 5, 7],
        }
    )
    chk = Check.equal_to(5, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    expected = ["fail", "pass", "fail", "pass", "fail"]
    assert test_df[node.name].to_list() == expected


def test_string_pattern_validation():
    df = DataFrame(
        {
            "source_col": ["abc", "123", "def", "456"],
        }
    )
    chk = Check.str_matches(r"^[A-Za-z]+$", warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    expected = ["pass", "fail", "pass", "fail"]
    assert test_df[node.name].to_list() == expected


def test_numeric_range_validation():
    df = DataFrame(
        {
            "source_col": [1, 5, 11, 3, 8],
        }
    )
    chk = Check.between(1, 10, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    expected = ["pass", "pass", "fail", "pass", "pass"]
    assert test_df[node.name].to_list() == expected


def test_in_list_validation():
    df = DataFrame(
        {
            "source_col": [1, 4, 2, 5, 3],
        }
    )
    chk = Check.is_in([1, 2, 3], warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    expected = ["pass", "fail", "pass", "fail", "pass"]
    assert test_df[node.name].to_list() == expected


# def test_date_validation():
#     df = DataFrame({
#         "source_col": ["2023-01-01", "invalid", "2023-12-31"],
#     })
#     chk = Check.valid_date(warning="any")
#     node = chk.get_validation_node(ref("source_col"))
#     test_df = df.with_columns(node.expression)
#
#     expected = ["pass", "fail", "pass"]
#     assert test_df[node.name].to_list() == expected


def test_threshold_configuration():
    df = DataFrame(
        {
            "source_col": [1, 2, None, 4],
        }
    )

    # Test with warning threshold
    chk = Check.not_null(warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)
    assert test_df[node.name].to_list() == ["pass", "pass", "fail", "pass"]

    # Test with error threshold
    chk = Check.not_null(error="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)
    assert test_df[node.name].to_list() == ["pass", "pass", "fail", "pass"]

    # Test with reject threshold
    chk = Check.not_null(reject="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)
    assert test_df[node.name].to_list() == ["pass", "pass", "fail", "pass"]
