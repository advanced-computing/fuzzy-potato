from __future__ import annotations

import pandas as pd
import streamlit as st
from google.cloud import bigquery


def get_bigquery_client() -> bigquery.Client:
    credentials_info = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"][
            "auth_provider_x509_cert_url"
        ],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
    }
    return bigquery.Client.from_service_account_info(credentials_info)


def run_query(query: str) -> pd.DataFrame:
    client = get_bigquery_client()
    return client.query(query).to_dataframe()


def load_table(project_id: str, dataset_name: str, table_name: str) -> pd.DataFrame:
    query = f"""
        SELECT *
        FROM `{project_id}.{dataset_name}.{table_name}`
    """
    return run_query(query)
