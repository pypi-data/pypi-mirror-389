# ⚗️ Zeolite

---

Zeolite is a Python library that uses a simple configuration approach to define a table/schema structure. Raw
data can normalised, cleaned, and validated against the schema in a performant and standardised way.

The schema implements a multi-stage pipeline:
- **normalise** - Normalises the dataset to ensure column headers align with the
        defined schema/column definitions
- **coerce** - Coerces the data types of the columns in the dataset to match the
        defined schema/column definitions
- **prepare** - Appends new columns to the dataset representing cleaned & derived/calculated columns and check/validation columns based on the validation rules
- **validate** - Applies validation rules/thresholds to the dataset, captures errors and determines if the dataset as a whole should be rejected
- **filter** - Drops rows that have failed checks based on the `remove_row_on_fail` argument
- **refine** - Renames working columns, and drops unneeded column to  refine the dataset to the final structure

The final datasets are guaranteed to be in the correct format and can be easily exported to a variety of formats. 
In addition, Zeolite captures errors and warnings during the processing of the data, which can be used to improve 
the quality of the data.



### Example
First we define a data schema that describes how our data *should be*, and includes both structural definitions, 
cleaning functions, and validation/data quality checks

```python
import zeolite as z

data_schema = z.schema("individual").columns(
    z.col.str("id")
    .clean(z.Clean.id(prefix="ORG_X"))
    .validations(
        z.Check.not_empty(
            warning="any", 
            error=0.1, 
            treat_empty_strings_as_null=True, 
            remove_row_on_fail=True
        ),
        z.Check.unique(check_on_cleaned=True, reject="any"),
    ),

    z.col.str("birthdate")
    .clean(z.Clean.date())
    .validations(z.Check.valid_date(reject="all")),

    z.col.str("gender").clean(
        z.Clean.enum(
            sanitise="lowercase",
            enum_map={
                "m": "Male", "male": "Male",
                "f": "Female", "female": "Female",
                "d": "Gender Diverse", "diverse": "Gender Diverse"
            },
        )
    ),

    z.col.str("is_active").clean(
        z.Clean.boolean(
            true_values={"yes", "active"}, false_values={"no", "inactive"}
        )
    ),

    z.col.str("ethnicity").clean(z.Clean.sanitised_string()),
    z.col.str("ethnicity_2").clean(z.Clean.sanitised_string()),
    z.col.derived(
        "is_maori",
        function=(
                z.ref("ethnicity").clean().col.eq("maori")
                | z.ref("ethnicity_2").clean().col.eq("maori")
        ),
        data_type="boolean",
    ),
)


```
Once we have the schema defined, we can apply it against our Polars DataFrame/LazyFrame

```python
import polars as pl

df = pl.DataFrame({
    # the third row will be removed because the empty string is treated as null 
    # and our `Check.not_empty` has `remove_row_on_fail=True`
    "id":["1","2","","4"],
   
    # we can handle multiple date formats (including weird Excel dates!)
    "birthdate":["1970-01-01","33746","","1987-01-25T00:00:00Z"],
    
    # using our enum_map, we can collapse category variants to a common definition
    "gender":["Male"," Male "," F ","d"],
    
    # boolean fields can be coerced from categories/values as well as bools
    "is_active":["active","inactive",None,"true"],
    
    # sanitising these fields means that we can match e.g. 'maori' more accurately
    "ethnicity":["Maori","Pakeha",None,"Asian"],
    "ethnicity_2":[None,"Māori ",None,"maori"],
})

res = data_schema.apply(df)

```

The `.apply(...)` method returns a result - either a `ProcessingFailure` or a `ProcessingSuccess`. 
These can be differentiated with a simple check on the `success` attribute:

```python

if res.success:
    # Do stuff with the data (LazyFrame) on success
    clean_df = res.data.collect()
else:
    # Gracefully handle failures
    failed_stage = res.failed_stage
    
# Regardless of the result, we have access to all the errors 
# that occurred during processing, which we can use for 
# logging/data quality reports  
errors = res.errors
for e in errors:
    print(e.message)

# We can also examine the snapshot data at each stage if necessary
# This is particularly useful to capture & debug working data!
if res.prepared is not None:
    prepared_df = res.prepared.collect()
    
if res.validated is not None:
    validated_df = res.validated.collect()

```

