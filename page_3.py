# page_3.py
import time

import pandas as pd
import plotly.express as px
import streamlit as st

from bigquery_helpers import run_query

start_time = time.time()

st.markdown("# RQ3: Is crime volume associated with misconduct allegations across precincts?")
st.sidebar.markdown("# Dataset 2: NYPD Complaint Data Historic")

PROJECT_ID = "fuzzy-potato-491318"
DATASET_NAME = "Project_Part5"
TABLE_NAME = "complaints_historic"


@st.cache_data(show_spinner=False)
def fetch_crime_counts_by_precinct(
    top_n: int,
    boro: str | None = None,
    law_cat: str | None = None,
) -> pd.DataFrame:
    where_clauses = [
        "addr_pct_cd IS NOT NULL",
    ]

    if boro:
        where_clauses.append(f"UPPER(TRIM(CAST(boro_nm AS STRING))) = UPPER('{boro}')")

    if law_cat:
        where_clauses.append(f"UPPER(TRIM(CAST(law_cat_cd AS STRING))) = UPPER('{law_cat}')")

    where_sql = " AND ".join(where_clauses)

    query = f"""
        SELECT
            CAST(addr_pct_cd AS STRING) AS precinct_raw,
            COUNT(*) AS crime_count
        FROM `{PROJECT_ID}.{DATASET_NAME}.{TABLE_NAME}`
        WHERE {where_sql}
        GROUP BY precinct_raw
        ORDER BY crime_count DESC
        LIMIT {top_n}
    """
    return run_query(query)


@st.cache_data(show_spinner=False)
def fetch_preview_rows() -> pd.DataFrame:
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_NAME}.{TABLE_NAME}`
        LIMIT 10
    """
    return run_query(query)


st.write(
    "This page pulls aggregated results from BigQuery and shows a bar "
    "chart of crime counts by precinct."
)

st.sidebar.subheader("Filters (optional)")

boro = st.sidebar.selectbox(
    "BORO_NM",
    options=["All", "BRONX", "BROOKLYN", "MANHATTAN", "QUEENS", "STATEN ISLAND"],
    index=0,
)

law_cat = st.sidebar.selectbox(
    "LAW_CAT_CD",
    options=["All", "FELONY", "MISDEMEANOR", "VIOLATION"],
    index=0,
)

top_n = st.slider("Show top N precincts", min_value=5, max_value=50, value=20, step=5)

with st.spinner("Loading aggregated crime counts from BigQuery..."):
    crime_by_precinct = fetch_crime_counts_by_precinct(
        top_n=top_n,
        boro=None if boro == "All" else boro,
        law_cat=None if law_cat == "All" else law_cat,
    )

st.subheader("Debug: query result preview")
st.write(crime_by_precinct)

if crime_by_precinct.empty:
    st.error("Still no results from BigQuery.")
    st.subheader("Debug: sample raw rows from the table")
    st.write(fetch_preview_rows())
    elapsed = time.time() - start_time
    st.caption(f"Page loaded in {elapsed:.2f} seconds")
    st.stop()

crime_by_precinct["precinct_raw"] = crime_by_precinct["precinct_raw"].astype(str).str.strip()
crime_by_precinct = crime_by_precinct[crime_by_precinct["precinct_raw"] != ""]

crime_by_precinct["Precinct Name"] = "Precinct " + crime_by_precinct["precinct_raw"]

fig = px.bar(
    crime_by_precinct,
    x="Precinct Name",
    y="crime_count",
    title="Crime Count by Precinct",
)

fig.update_layout(xaxis_title="Precinct", yaxis_title="Crime Count")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Preview")
st.write(crime_by_precinct.head())

elapsed = time.time() - start_time
st.caption(f"Page loaded in {elapsed:.2f} seconds")
