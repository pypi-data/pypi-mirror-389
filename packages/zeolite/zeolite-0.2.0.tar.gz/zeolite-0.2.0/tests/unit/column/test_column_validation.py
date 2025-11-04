from polars import DataFrame
from zeolite.column.validation import Check
from zeolite.ref import ref
from zeolite.types.error import DataValidationError


def test_string_pattern_validation_rule():
    df = DataFrame(
        {
            "source_col": ["abc", "123", "def", "456"],
        }
    )
    chk = Check.str_matches(r"^[A-Za-z]+$", warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.5  # 2 out of 4 values failed
    assert validation_res.count_failed == 2
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 2 row(s) not matching pattern `^[A-Za-z]+$` (50.00%)"
    )


def test_not_pattern_match_validation_rule():
    df = DataFrame(
        {
            "source_col": ["abc", "123", "def", "456"],
        }
    )
    chk = Check.str_not_matches(r"^[A-Za-z]+$", warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.5  # 2 out of 4 values failed
    assert validation_res.count_failed == 2
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 2 row(s) matching pattern `^[A-Za-z]+$` (50.00%)"
    )


def test_not_null_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 2, None, 4],
        }
    )
    chk = Check.not_null(warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.25  # 1 out of 4 values failed
    assert validation_res.count_failed == 1
    assert validation_res.level == "warning"
    assert validation_res.message == "`source_col` has 1 null (empty) value(s) (25.00%)"


def test_unique_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 2, 2, 3, 3, 4],
        }
    )
    chk = Check.unique(warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 4 / 6  # 4 out of 6 values failed
    assert validation_res.count_failed == 4
    assert validation_res.level == "warning"
    assert validation_res.message == "`source_col` has 4 duplicate value(s) (66.67%)"


def test_equality_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 5, 3, 5, 7],
        }
    )
    chk = Check.equal_to(5, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.6  # 3 out of 5 values failed
    assert validation_res.count_failed == 3
    assert validation_res.level == "warning"
    assert (
        validation_res.message == "`source_col` has 3 row(s) not equal to `5` (60.00%)"
    )


def test_not_equality_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 5, 3, 5, 7],
        }
    )
    chk = Check.not_equal_to(5, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.4  # 2 out of 5 values failed
    assert validation_res.count_failed == 2
    assert validation_res.level == "warning"
    assert validation_res.message == "`source_col` has 2 row(s) equal to `5` (40.00%)"


def test_numeric_range_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 5, 11, 3, 8],
        }
    )
    chk = Check.between(1, 10, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.2  # 1 out of 5 values failed
    assert validation_res.count_failed == 1
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 1 row(s) which are not between `1` and `10` (20.00%)"
    )


def test_less_than_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 5, 3, 5, 7],
        }
    )
    chk = Check.less_than(5, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.6  # 3 out of 5 values failed
    assert validation_res.count_failed == 3
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 3 row(s) greater than max `5` (60.00%)"
    )


def test_less_than_or_equal_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 5, 3, 5, 7],
        }
    )
    chk = Check.lte(5, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.2
    assert validation_res.count_failed == 1
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 1 row(s) greater than or equal to max `5` (20.00%)"
    )


def test_greater_than_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 5, 3, 5, 7],
        }
    )
    chk = Check.greater_than(5, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.8  # 3 out of 5 values failed
    assert validation_res.count_failed == 4
    assert validation_res.level == "warning"
    assert (
        validation_res.message == "`source_col` has 4 row(s) less than min `5` (80.00%)"
    )


def test_greater_than_or_equal_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 5, 3, 5, 7],
        }
    )
    chk = Check.gte(5, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.4
    assert validation_res.count_failed == 2
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 2 row(s) less than or equal to min `5` (40.00%)"
    )


def test_in_list_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 4, 2, 5, 3],
        }
    )
    chk = Check.is_in([1, 2, 3], warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.4  # 2 out of 5 values failed
    assert validation_res.count_failed == 2
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 2 row(s) not in `[ 1 | 2 | 3 ]` (40.00%)"
    )


def test_not_in_list_validation_rule():
    df = DataFrame(
        {
            "source_col": [1, 4, 2, 5, 3],
        }
    )
    chk = Check.not_in([1, 2, 3], warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.6  # 3 out of 5 values failed
    assert validation_res.count_failed == 3
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 3 row(s) in `[ 1 | 2 | 3 ]` (60.00%)"
    )


def test_str_length_min_validation_rule():
    df = DataFrame(
        {
            "source_col": ["a", "ab", "abc", "abcd"],
        }
    )
    chk = Check.str_length(min_length=3, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.5  # 2 out of 4 values failed
    assert validation_res.count_failed == 2
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 2 row(s) with length less than min `3` (50.00%)"
    )


def test_str_length_max_validation_rule():
    df = DataFrame(
        {
            "source_col": ["a", "ab", "abc", "abcd"],
        }
    )
    chk = Check.str_length(max_length=2, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.5  # 2 out of 4 values failed
    assert validation_res.count_failed == 2
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 2 row(s) with length greater than max `2` (50.00%)"
    )


def test_str_length_between_validation_rule():
    df = DataFrame(
        {
            "source_col": ["a", "ab", "abc", "abcd"],
        }
    )
    chk = Check.str_length(min_length=2, max_length=3, warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 0.5  # 2 out of 4 values failed
    assert validation_res.count_failed == 2
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 2 row(s) with length not between `2 <-> 3` (50.00%)"
    )


def test_date_validation_rule():
    df = DataFrame(
        {
            "source_col": ["2023-01-01", "invalid", "2023-12-31"],
        }
    )
    chk = Check.valid_date(warning="any")
    node = chk.get_validation_node(ref("source_col"))
    test_df = df.with_columns(node.expression)

    validation_res = node.validation_rule.validate(
        test_df.lazy(), source="testing_schema"
    )

    assert isinstance(validation_res, DataValidationError)
    assert validation_res.fraction_failed == 1 / 3  # 1 out of 3 values failed
    assert validation_res.count_failed == 1
    assert validation_res.level == "warning"
    assert (
        validation_res.message
        == "`source_col` has 1 row(s) with invalid date format (33.33%)"
    )
