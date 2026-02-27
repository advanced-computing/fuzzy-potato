import pandas as pd
import pandera.pandas as pa
from pandera import Check

df1_schema = pa.DataFrameSchema(
    {
        # Snapshot date stored as string "YYYY-MM-DD"
        "As Of Date": pa.Column(
            pa.DateTime,
            checks=[Check.le(pd.Timestamp.today())],
            nullable=False,
            coerce=True,
        ),
        "Tax ID": pa.Column(str, nullable=True),
        "Shield No": pa.Column(str, nullable=True),
        "Officer First Name": pa.Column(
            str,
            checks=[Check.str_length(0, 100)],
            nullable=True,
        ),
        "Officer Last Name": pa.Column(
            str,
            checks=[Check.str_length(0, 100)],
            nullable=True,
        ),
        "Active Per Last Reported Status": pa.Column(str, nullable=True),
        "Last Reported Active Date": pa.Column(str, nullable=True),
        "Officer Race": pa.Column(
            str,
            checks=[Check.str_length(min_value=1)],
            nullable=False,
        ),
        "Officer Gender": pa.Column(
            str,
            checks=[Check.str_length(min_value=1)],
            nullable=False,
        ),
        "Current Rank Abbreviation": pa.Column(str, nullable=True),
        "Current Rank": pa.Column(
            str,
            checks=[Check.str_length(min_value=1)],
            nullable=False,
        ),
        "Current Command": pa.Column(
            str,
            checks=[Check.str_length(min_value=1)],
            nullable=False,
        ),
        "Total Complaints": pa.Column(
            int,
            checks=[
                Check.ge(0),
                Check.le(1000),  # upperbound
            ],
            nullable=False,
        ),
        "Total Substantiated Complaints": pa.Column(
            int,
            checks=[
                Check.ge(0),
                Check.le(1000),
                Check.less_than_or_equal_to("Total Complaints"),
            ],
            nullable=False,
        ),
    },
    strict=False,
)

df2_schema = pa.DataFrameSchema(
    {
        "precinct": pa.Column(
            int,
            checks=[
                Check.ge(1),
                Check.le(200),  # safe upper bound
            ],
            nullable=False,
        ),
        "crime_count": pa.Column(
            float,  # keep float since to_numeric may produce float
            checks=[
                Check.ge(0),
            ],
            nullable=False,
            coerce=True,
        ),
        "Precinct Name": pa.Column(
            str,
            checks=[
                Check.str_matches(r"^Precinct \d+$"),
            ],
            nullable=False,
        ),
    },
    strict=False,
)
