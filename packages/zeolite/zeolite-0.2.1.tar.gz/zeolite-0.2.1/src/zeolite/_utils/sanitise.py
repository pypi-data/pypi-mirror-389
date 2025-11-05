from enum import StrEnum, auto
import re
from typing import Dict, Literal

import polars as pl

from ..ref import parse_column_name
from ..types.data_type import NO_DATA

PREFIX = ""

"""
---------------------------------------------------------------------------------------------
    Cleaning functions
---------------------------------------------------------------------------------------------
These functions are used to clean the data in the columns - usually by converting to a 
correct data type
"""


class SanitiseLevel(StrEnum):
    FULL = auto()
    LOWERCASE = auto()
    TRIM = auto()


# Unfortunately, we can't use the enum as a type hint for the sanitise attribute
type SanitiseLevelType = Literal["full", "lowercase", "trim"] | None


def sanitise_string_col(
    col: str | pl.Expr,
    *,
    sanitise_level: SanitiseLevelType = None,
    join_char: str = "_",
) -> pl.Expr:
    if sanitise_level == SanitiseLevel.FULL:
        return full_sanitise_string_col(col, join_char=join_char)
    elif sanitise_level == SanitiseLevel.LOWERCASE:
        return lower_sanitise_string_col(col)
    elif sanitise_level == SanitiseLevel.TRIM:
        return trim_sanitise_string_col(col)
    else:
        return (
            pl.col(col).cast(pl.String) if isinstance(col, str) else col.cast(pl.String)
        )


def _sanitisation_fix(exp: pl.Expr, incorrect: str, corrected: str):
    # Can't do look behind regex in polars, so have to declare each option separately
    return (
        exp.str.replace_all(rf"^{incorrect}$", f"{corrected}", literal=False)
        .str.replace_all(rf"^{incorrect}_", f"{corrected}_", literal=False)
        .str.replace_all(rf"_{incorrect}$", f"_{corrected}", literal=False)
        .str.replace_all(rf"_{incorrect}_", f"_{corrected}_", literal=False)
    )


COMMON_MISTAKES = (
    ("i_d", "id"),
    ("u_r_l", "url"),
    ("h_t_t_p", "http"),
    ("h_t_m_l", "html"),
    ("c_s_v", "csv"),
    ("x_l_s_x", "xlsx"),
    ("p_d_f", "pdf"),
    ("a_p_i", "api"),
    ("d_b", "db"),
    ("u_i", "ui"),
    ("u_x", "ux"),
    ("s_q_l", "sql"),
    ("j_s_o_n", "json"),
    ("x_m_l", "xml"),
    ("s_s_l", "ssl"),
    ("t_l_s", "tls"),
    ("n_z", "nz"),
    ("u_k", "uk"),
    ("u_s", "us"),
    ("e_u", "eu"),
    ("m_ori", "maori"),
    ("wh_nau", "whanau"),
    ("p_keh_", "pakeha"),
    ("t_ne", "tane"),
    ("w_hine", "wahine"),
    ("hap_", "hapu"),
    ("w_nanga", "wananga"),
    ("k_inga", "kainga"),
    ("k_rero", "korero"),
)


def trim_sanitise_string_col(col: str | pl.Expr) -> pl.Expr:
    """
    Remove leading and trailing spaces
    """
    if isinstance(col, str):
        return pl.col(col).cast(pl.String).str.strip_chars()
    else:
        return col.cast(pl.String).str.strip_chars()


def lower_sanitise_string_col(col: str | pl.Expr) -> pl.Expr:
    """
    Convert to lowercase
    """
    return trim_sanitise_string_col(col).str.to_lowercase()


def full_sanitise_string_col(
    col: str | pl.Expr,
    join_char="_",
) -> pl.Expr:
    new_col = (
        lower_sanitise_string_col(col)
        # Replace special characters with their plain letter counterparts
        .str.replace_all("ā", "a", literal=True)
        .str.replace_all("ē", "e", literal=True)
        .str.replace_all("ī", "i", literal=True)
        .str.replace_all("ō", "o", literal=True)
        .str.replace_all("ū", "u", literal=True)
        # Replace spaces, question marks, slashes, and line breaks with underscores
        .str.replace_all(r"[ ?/\n\r]", "_", literal=False)
        # Remove any non-alphanumeric characters (except underscores)
        .str.replace_all(r"[^a-z0-9_]", "_", literal=False)
    )
    # handle common mis-coded words
    for incorrect, corrected in COMMON_MISTAKES:
        new_col = _sanitisation_fix(new_col, incorrect, corrected)

    new_col = (
        new_col
        # Replace multiple underscores with a single one
        .str.replace_all(r"_+", "_", literal=False)
        # Strip leading and trailing spaces (technically underscores...)
        .str.strip_chars("_")
        # Change underscores back to spaces
        .str.replace_all("_", join_char, literal=True)
    )
    return new_col


def sanitise_scalar_string(value: str, join_char: str = "_") -> str:
    """
    Sanitise a string value by converting to lowercase, replacing special characters with their plain letter counterparts,
    and replacing spaces, question marks, slashes, and line breaks with underscores.
    Also handles common mis-coded words.
    """
    if not isinstance(value, str):
        value = str(value)

    # Replace special characters with their plain letter counterparts
    value = (
        value.strip()
        .lower()
        .replace("ā", "a")
        .replace("ē", "e")
        .replace("ī", "i")
        .replace("ō", "o")
        .replace("ū", "u")
    )
    # Replace spaces, question marks, slashes, and line breaks with underscores
    value = re.sub(r"[ ?/\n\r]", "_", value)
    # Replace any non-alphanumeric characters (except underscores)
    value = re.sub(r"[^a-z0-9_]", "_", value)
    # Handle common mis-sanitised words
    value = fix_sanitisation_mistakes(value)
    # Replace multiple underscores with a single one
    value = re.sub(r"_+", "_", value)
    # Strip leading and trailing underscores/spaces
    value = value.strip("_ ")

    # Finally, replace underscores with the specified join character
    return value.replace("_", join_char)


def clean_enum_col(
    col: str,
    enum_def=Dict[str, str],
    *,
    prefix: str = PREFIX,
    alias: str = None,
    default=NO_DATA,
    sanitise: bool = True,
) -> pl.Expr:
    unique_values = set(enum_def.values())
    unique_values.add(default)
    new_col = pl.col(col) if not sanitise else full_sanitise_string_col(col)

    return new_col.replace(
        enum_def,
        default=default,
        return_dtype=pl.Enum(list(unique_values)),
    ).alias(alias if alias else f"{prefix}{col}")


def clean_boolean_col(
    col: str,
    *,
    prefix: str = PREFIX,
    alias: str = None,
    true_values=("yes", "true", "1"),
    false_values=("no", "false", "0"),
    sanitise: bool = True,
) -> pl.Expr:
    new_col = pl.col(col) if not sanitise else full_sanitise_string_col(col)

    return new_col.replace(
        {**{val: True for val in true_values}, **{val: False for val in false_values}},
        default=None,
        return_dtype=pl.Boolean,
    ).alias(alias if alias else f"{prefix}{col}")


def fix_sanitisation_mistakes(text, mistakes=COMMON_MISTAKES):
    # Handle cases where the incorrect term appears:
    # 1. As a complete word by itself
    # 2. At the start of a compound word
    # 3. At the end of a compound word
    # 4. In the middle of a compound word
    for incorrect, corrected in mistakes:
        pattern = rf"(^|_)({re.escape(incorrect)})($|_)"
        replacement = rf"\1{corrected}\3"
        text = re.sub(pattern, replacement, text)

    # value = text
    # for incorrect, corrected in COMMON_MISTAKES:
    #     value = re.sub(rf"^{incorrect}$", corrected, value)
    #     value = re.sub(rf"^{incorrect}_", f"{corrected}_", value)
    #     value = re.sub(rf"_{incorrect}$", f"_{corrected}", value)
    #     value = re.sub(rf"_{incorrect}_", f"_{corrected}_", value)
    return text


def sanitise_column_name(column: str, join_char="_"):
    """
    --------------------------------------------------------------------------------------------------
      Sanitise column name
    --------------------------------------------------------------------------------------------------
    This function takes a string (assumed to be a column name) and sanitises it by:

    - Removing the prefix/suffix (if any)
    - Converting camel case words to snake case
    - Lowercasing the string
    - Replacing special characters with their plain letter counterparts
    - Replacing common incorrect words with their correct versions
    - Replacing spaces, dashes, question marks, slashes, and line breaks with underscores
    - Removing any non-alphanumeric characters (except underscores)
    - Replacing multiple underscores with a single one
    - Stripping leading and trailing underscores/spaces
    - Appending the prefix/suffix back to the string (if any)

    :param column: The original string/column name
    :param join_char: The character to use to join words in the column headers (default: "_")
    :return: A sanitised string/column name
    """
    ref = parse_column_name(column)
    base = ref.base_name

    # Check if string is screaming snake case (all letters are uppercase)
    if not re.search(r"[a-z]", base):
        # Already screaming snake case or all caps - just lowercase it
        col = sanitise_scalar_string(base.lower(), join_char=join_char)
    else:
        # Convert camel/pascal case to snake case, then lowercase
        col = sanitise_scalar_string(
            re.sub(r"(?<!^)(?=[A-Z])", "_", base).lower(), join_char=join_char
        )

    return ref.with_base_name(col).name


def sanitise_column_headers(lf: pl.LazyFrame, join_char="_") -> pl.LazyFrame:
    """
    --------------------------------------------------------------------------------------------------
      Sanitise column headers
    --------------------------------------------------------------------------------------------------
    This function takes a LazyFrame and sanitises the column headers by:

    - Lowercasing the column name
    - Replacing special characters with their plain letter counterparts
    - Replacing common incorrect words with their correct versions
    - Replacing spaces, dashes, question marks, slashes, and line breaks with underscores
    - Removing any non-alphanumeric characters (except underscores)
    - Replacing multiple underscores with a single one
    - Stripping leading and trailing underscores/spaces

    :param lf: The Polars LazyFrame to sanitise
    :param join_char: The character to use to join words in the column headers (default: "_")
    :return: A Polars LazyFrame with the column headers sanitised
    """

    return lf.rename(
        # {col: sanitise(col) for col in lf.collect_schema().names() if not re.match(_INTERNAL_COL_PATTERN, col)})
        {
            col: sanitise_column_name(col, join_char)
            for col in lf.collect_schema().names()
        }
    )
