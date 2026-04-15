import os

import pandas as pd
import requests
from google.oauth2 import service_account
from pandas_gbq import to_gbq


def get_gbq_credentials():
    return service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    )


PROJECT_ID = "fuzzy-potato-491318"
DATASET_ID = "Project_Part5"
TABLE_ID = "officers"

FULL_TABLE_ID = f"{DATASET_ID}.{TABLE_ID}"

API_URL = "https://data.cityofnewyork.us/resource/2fir-qns4.json"


def load_data(limit=50000):
    params = {"$limit": limit}
    r = requests.get(API_URL, params=params)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    return df


def clean_data(df):
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace(r"[^a-z0-9_]", "", regex=True)
    )

    numeric_cols = [
        "shield_no",
        "tax_id",
        "complaint_count",
        "substantiated_count",
        "unsubstantiated_count",
        "exonerated_count",
        "unfounded_count",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def write_to_bigquery(df):
    credentials = get_gbq_credentials()

    to_gbq(
        dataframe=df,
        destination_table=FULL_TABLE_ID,
        project_id=PROJECT_ID,
        credentials=credentials,
        if_exists="replace",
    )


def main():
    print("Loading data from API...")
    df = load_data()

    print("First 5 rows:")
    print(df.head())
    print("Shape:", df.shape)

    print("Cleaning data...")
    df = clean_data(df)
    print("Columns after cleaning:")
    print(df.columns.tolist())

    print("Uploading to BigQuery...")
    write_to_bigquery(df)

    print(f"Done! Uploaded to {PROJECT_ID}.{FULL_TABLE_ID}")


if __name__ == "__main__":
    main()
