# page_3.py
import time

import pandas as pd
import plotly.express as px
import streamlit as st

from bigquery_helpers import run_query
from precinct_helpers import load_dataset1, misconduct_by_precinct

start_time = time.time()

st.markdown(
    "# RQ3: Is the number of crime incidents associated with "
    "misconduct allegations across precincts?"
)
st.write(
    "This page compares crime volume from the NYPD Complaint Data Historic dataset "
    "with misconduct allegations from the CCRB officer dataset at the precinct level. "
    "The goal is to explore whether precincts with more recorded crime also tend to have "
    "more misconduct allegations."
)
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
# --- LOAD MISCONDUCT DATA ---
officers_df = load_dataset1()
misconduct_counts = misconduct_by_precinct(officers_df)
misconduct_counts = misconduct_counts.rename(
    columns={
        "precinct": "precinct_raw",
        "allegation_count": "misconduct_count",
    }
)

misconduct_counts["precinct_raw"] = misconduct_counts["precinct_raw"].astype(str).str.strip()

if crime_by_precinct.empty:
    st.error("Still no results from BigQuery.")
    st.subheader("Debug: sample raw rows from the table")
    st.write(fetch_preview_rows())
    elapsed = time.time() - start_time
    st.caption(f"Page loaded in {elapsed:.2f} seconds")
    st.stop()

with st.expander("View crime count query result"):
    st.dataframe(crime_by_precinct, use_container_width=True)

crime_by_precinct["precinct_raw"] = crime_by_precinct["precinct_raw"].astype(str).str.strip()
crime_by_precinct = crime_by_precinct[crime_by_precinct["precinct_raw"] != ""]

crime_by_precinct["Precinct Name"] = "Precinct " + crime_by_precinct["precinct_raw"]

# --- MERGE DATA HERE ---
merged_df = crime_by_precinct.merge(misconduct_counts, on="precinct_raw", how="inner")
merged_df["Precinct Name"] = "Precinct " + merged_df["precinct_raw"]

if merged_df.empty:
    st.error("No matching precincts found between crime data and misconduct data.")
    st.stop()
# --- Summary metrics (ADD HERE) ---
col1, col2, col3 = st.columns(3)

col1.metric("Precincts matched", len(merged_df))
col2.metric("Total crime records", f"{merged_df['crime_count'].sum():,}")
col3.metric("Total misconduct allegations", f"{merged_df['misconduct_count'].sum():,}")

fig = px.bar(
    crime_by_precinct,
    x="Precinct Name",
    y="crime_count",
    title="Number of Crime Incidents by Precinct",
)

fig_scatter = px.scatter(
    merged_df,
    x="crime_count",
    y="misconduct_count",
    hover_name="Precinct Name",
    size="misconduct_count",
    title="Number of Crime Incidents vs Misconduct Allegations",
    labels={
        "crime_count": "Number of Crime Incidents",
        "misconduct_count": "Misconduct Allegations",
    },
)

# Scatterplot (answers RQ3)
st.subheader("Number of Crime Incidents vs Misconduct Relationship")
st.plotly_chart(fig_scatter, use_container_width=True)

corr = merged_df["crime_count"].corr(merged_df["misconduct_count"])

st.info(
    f"The correlation between the number of crime incidents and misconduct allegations "
    f"is **{corr:.2f}**. "
    "A higher value suggests that precincts with more recorded incidents tend to also have "
    "more misconduct allegations. "
    "A value closer to 0 suggests little to no relationship between incidents and misconduct."
)

# Bar chart (supporting context)
st.subheader("Crime Count Ranking")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Preview")
st.dataframe(merged_df.head(), use_container_width=True)

elapsed = time.time() - start_time
st.caption(f"Page loaded in {elapsed:.2f} seconds")

if st.button("Back to Homepage"):
    st.switch_page("main_page.py")
