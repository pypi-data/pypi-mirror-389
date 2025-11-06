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
    .clean(z.Clean.id(prefix="user"))
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

price_col = z.col.float("price").clean(z.Clean.float())
quantity_col = z.col.int("quantity").clean(z.Clean.int())
temp_calc_col = z.col.derived(
    "temp_calc", function=price_col.ref.col * quantity_col.ref.col
)

TAX = 1.15

advanced_schema_1 = (
    z.schema("advanced")
    .columns(
        # -----------------------------------------------.temporary()
        # Extending generic ID col with specific variants
        id_col.variants("advanced_id"),
        # -----------------------------------------------
        z.col.str("name")
        .optional()
        .clean(z.Clean.sanitised_string().alias("clean_name"))
        .validations(z.Check.not_empty().alias("is_name_empty")),
        # -----------------------------------------------
        z.col.int("age").optional().validations(z.Check.not_empty()),
        # -----------------------------------------------
        z.col.date("enrollment_date")
        .clean(z.Clean.date().alias("clean_enrollment_date"))
        .variants("date_enrolled", "enrollment")
        .validations(date_checks),
        # -----------------------------------------------
        price_col.temporary(),
        quantity_col.temporary(),
        temp_calc_col.temporary(),
        z.col.derived("total_price", function=temp_calc_col.ref.col * TAX),
        # -----------------------------------------------
        z.col.derived("age_over_21", function=pl.col("age").ge(21)),
    )
    .table_validation(
        z.TableCheck.removed_rows(warning=0.2, error=0.3, reject=0.4),
        z.TableCheck.min_rows(reject=1),
    )
)

# %%
data = pl.DataFrame(
    {
        "id": ["jdk1l35", "a8s7nt7", "oki191o"],
        "name": ["BOB ", None, "Bob!"],
        "enrollment_date": ["2025-11-02", "2027-1-2", "bob"],
        "age": [12, 52, 18],
        "price": [140, 60, 100],
        "quantity": [1, 2, 1],
    }
)
res = advanced_schema_1.apply(data)

if res.success:
    print("✅ dataset successfully processed")
    df = res.data.collect()
else:
    print("Something went wrong.")
    for error in res.errors:
        if error.level == "reject":
            print(f"❌  {error.message}")
