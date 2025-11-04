"""
Advanced examples of using the Zeolite data validation framework.
This file demonstrates how to create schemas and define column validations.
"""

import polars as pl
import zeolite as z


# %%  ---------------------------------------------------------------------------------
# Advanced examples
# ---------------------------------------------------------------------------------

# Reusable ID column definition
id_col = (
    z.col("id")
    .data_type("id")
    .validations(
        z.Check.not_empty(
            warning="any", error=0.1, reject=0.2, remove_row_on_fail=True
        ),
        z.Check.unique(error="any", remove_row_on_fail=True),
    )
)

date_checks = [
    z.Check.not_empty(),
    z.Check.valid_date(check_on_cleaned=True).alias("enrollment_date_valid"),
]

advanced_schema_1 = (
    z.schema("advanced")
    .columns(
        # # Extending generic ID col with specific variants
        # id_col.variants("advanced_id"),
        # String column
        z.col.str("name")
        .optional()
        .clean(z.Clean.sanitised_string().alias("enrollment_date"))
        .validations(z.Check.not_empty().alias("popsicle")),
        # # Integer column
        z.col.int("age").optional().validations(z.Check.not_empty()),
        # # Date column
        z.col.date("enrollment_date")
        .clean(z.Clean.date().alias("clean_enrollment_date"))
        .variants("date_enrolled", "enrollment")
        .validations(date_checks),
        # # Boolean column
        # z.bool_col("is_active"),
        # # Float column
        # z.float_col("balance"),
        z.col.derived("age_over_21", function=pl.col("age").ge(21)),
    )
    .table_validation(
        z.TableCheck.removed_rows(warning=0.2, error=0.3, reject=0.4),
        z.TableCheck.min_rows(reject=1),
    )
)

# %%
df = pl.DataFrame(
    {
        "name": ["BOB ", None, "Bob!"],
        "enrollment_date": ["2025-11-02", "2027-1-2", "bob"],
        "age": [12, 52, 18],
    }
)
res = advanced_schema_1.apply(df)
