# page_3.py
import time
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from bigquery_helpers import load_table
from precinct_helpers import load_dataset1, misconduct_by_precinct

start_time = time.time()

officers_df = load_dataset1()
misconduct_counts = misconduct_by_precinct(officers_df)

st.markdown("# Dataset 2: NYPD Complaint Data Historic")
st.sidebar.markdown("# Dataset 2: NYPD Complaint Data Historic")

PROJECT_ID = "fuzzy-potato-491318"
DATASET_NAME = "Project_Part5"
TABLE_NAME = "complaints_historic"


# -------------------------
# Helpers
# -------------------------

COLUMN_LABELS = {
    "addr_pct_cd": "Precinct",
    "boro_nm": "Borough",
    "patrol_boro": "Patrol Borough",
    "law_cat_cd": "Offense Level (Felony/Misdemeanor/Violation)",
    "ofns_desc": "Offense Description",
    "pd_desc": "Detailed Offense Description",
}


@st.cache_data(show_spinner=False)
def load_dataset2_bigquery() -> pd.DataFrame:
    df = load_table(PROJECT_ID, DATASET_NAME, TABLE_NAME)

    # Ensure common fields are in expected types
    if "rpt_dt" in df.columns:
        df["rpt_dt"] = pd.to_datetime(df["rpt_dt"], errors="coerce")

    if "addr_pct_cd" in df.columns:
        df["addr_pct_cd"] = pd.to_numeric(df["addr_pct_cd"], errors="coerce")

    return df


@st.cache_data(show_spinner=False)
def fetch_group_counts_bigquery(  # noqa: PLR0913
    df: pd.DataFrame,
    group_col: str,
    top_n: int,
    start_dt: str | None = None,
    end_dt: str | None = None,
    boro: str | None = None,
    law_cat: str | None = None,
) -> pd.DataFrame:
    work = df.copy()

    if boro and boro != "All" and "boro_nm" in work.columns:
        work = work[work["boro_nm"] == boro]

    if law_cat and law_cat != "All" and "law_cat_cd" in work.columns:
        work = work[work["law_cat_cd"] == law_cat]

    work = work.dropna(subset=[group_col])

    counts = (
        work.groupby(group_col, dropna=True)
        .size()
        .reset_index(name="crime_count")
        .sort_values("crime_count", ascending=False)
        .head(top_n)
    )

    counts["crime_count"] = pd.to_numeric(counts["crime_count"], errors="coerce")
    return counts


# -------------------------
# UI
# -------------------------
st.write(
    "This page pulls from BigQuery and shows a bar chart of crime counts by precinct. "
    "It answers RQ3: Crime vs Misconduct allegations by precinct."
)

with st.spinner("Loading Dataset 2 from BigQuery..."):
    df_preview = load_dataset2_bigquery()

if df_preview.empty:
    st.error("BigQuery returned no data for Dataset 2.")
    st.stop()

# Sidebar filters
st.sidebar.subheader("Filters (optional)")

default_start = date(2019, 1, 1)
default_end = date(2020, 1, 1)

start_date = st.sidebar.date_input("Start date (RPT_DT)", value=default_start)
end_date = st.sidebar.date_input("End date (exclusive)", value=default_end)

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

st.subheader("1) Choose a crime count to group by")

community_keywords = [
    "pct",
    "precinct",
    "addr_pct_cd",
    "boro",
    "borough",
    "law_cat",
    "ofns",
    "pd_desc",
]

candidates = [c for c in df_preview.columns if any(k in c.lower() for k in community_keywords)]
if not candidates:
    candidates = list(df_preview.columns)

friendly_options = {COLUMN_LABELS.get(col, col): col for col in candidates}

group_col = "addr_pct_cd"
group_col_label = "Precinct"

# 这里保留 slider
top_n = st.slider("Show top N groups", min_value=5, max_value=50, value=20, step=5)

st.subheader("2) Bar chart: Crime counts by selected group")

counts = fetch_group_counts_bigquery(
    df_preview,
    group_col=group_col,
    top_n=top_n,
    start_dt=start_date.strftime("%Y-%m-%d") if start_date else None,
    end_dt=end_date.strftime("%Y-%m-%d") if end_date else None,
    boro=None if boro == "All" else boro,
    law_cat=None if law_cat == "All" else law_cat,
)

crime_by_precinct = counts.dropna(subset=[group_col]).copy()
crime_by_precinct["precinct"] = pd.to_numeric(crime_by_precinct[group_col], errors="coerce")
crime_by_precinct = crime_by_precinct.dropna(subset=["precinct"])
crime_by_precinct["precinct"] = crime_by_precinct["precinct"].astype(int)
crime_by_precinct = crime_by_precinct[["precinct", "crime_count"]]
crime_by_precinct["Precinct Name"] = "Precinct " + crime_by_precinct["precinct"].astype(str)

st.subheader("Crime by precinct preview")
st.write("First few rows:")
st.write(crime_by_precinct.head())

if counts.empty or group_col not in counts.columns:
    st.warning("No results returned. Try widening your date range or adjusting filters.")
    st.stop()

counts = counts.dropna(subset=[group_col]).copy()
counts[group_col] = counts[group_col].astype(str)

title = (
    f"Crime count by {group_col_label} (Top {top_n})"
    f" | {start_date} to {end_date}"
    + ("" if boro == "All" else f" | {boro}")
    + ("" if law_cat == "All" else f" | {law_cat}")
)

fig = px.bar(
    crime_by_precinct,
    x="Precinct Name",
    y="crime_count",
    title="Crime Count by Precinct",
)

fig.update_layout(xaxis_title="Precinct", yaxis_title="Crime Count")
st.plotly_chart(fig, use_container_width=True)

st.info(
    "For your research question, the key precinct column in Dataset 2 is "
    "**`addr_pct_cd`**. "
    "Aggregate to **crime_count by addr_pct_cd**, then merge with Dataset 1’s "
    "**misconduct_count by precinct** "
    "using 'precinct'/'addr_pct_cd' (make sure both are numeric or both are strings)."
)

# Build misconduct counts from Dataset 1
misconduct_counts = misconduct_by_precinct(officers_df)

# Merge and visualize relationship
merged = crime_by_precinct.merge(
    misconduct_counts,
    on="precinct",
    how="inner",
)

elapsed = time.time() - start_time
st.caption(f"Page loaded in {elapsed:.2f} seconds")
