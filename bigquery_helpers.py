from __future__ import annotations

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account


@st.cache_resource
def get_bigquery_client() -> bigquery.Client:
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(
        credentials=credentials,
        project=credentials.project_id,
    )


def run_query(query: str) -> pd.DataFrame:
    client = get_bigquery_client()
    return client.query(query).to_dataframe()


def load_table(
    project_id: str,
    dataset_name: str,
    table_name: str,
    columns: list[str] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    selected_columns = ", ".join(columns) if columns else "*"

    query = f"""
        SELECT {selected_columns}
        FROM `{project_id}.{dataset_name}.{table_name}`
    """

    if limit is not None and limit > 0:
        query += f"\nLIMIT {int(limit)}"

    return run_query(query)
