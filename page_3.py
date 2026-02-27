# page_3.py
from datetime import date

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from precinct_helpers import load_dataset1, misconduct_by_precinct

officers_df = load_dataset1()
misconduct_counts = misconduct_by_precinct(officers_df)

st.markdown("# Dataset 2: NYPD Complaint Data Historic")
st.sidebar.markdown("# Dataset 2: NYPD Complaint Data Historic")

DATASET2_BASE = "https://data.cityofnewyork.us/resource/qgea-i56i.json"


def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.8,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


SESSION = make_session()

# -------------------------
# Helpers
# -------------------------

# Human-readable names for columns
COLUMN_LABELS = {
    "addr_pct_cd": "Precinct",
    "boro_nm": "Borough",
    "patrol_boro": "Patrol Borough",
    "law_cat_cd": "Offense Level (Felony/Misdemeanor/Violation)",
    "ofns_desc": "Offense Description",
    "pd_desc": "Detailed Offense Description",
}


@st.cache_data(show_spinner=False)
def load_preview(n_rows: int = 200) -> pd.DataFrame:
    """Load a small sample to detect available columns."""
    params = {"$limit": n_rows}
    try:
        r = SESSION.get(DATASET2_BASE, params=params, timeout=90)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except requests.exceptions.RequestException:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def fetch_group_counts( # noqa: PLR0913
    group_col: str,
    top_n: int,
    start_dt: str | None = None,
    end_dt: str | None = None,
    boro: str | None = None,
    law_cat: str | None = None,
) -> pd.DataFrame:
    """
    Server-side aggregation:
    SELECT group_col, count(*) as crime_count
    WHERE group_col is not null (+ optional filters)
    GROUP BY group_col
    ORDER BY crime_count desc
    LIMIT top_n
    """
    where = [f"{group_col} IS NOT NULL"]

    # Date filter uses RPT_DT (report date). Socrata expects ISO timestamps.
    if start_dt:
        where.append(f"rpt_dt >= '{start_dt}T00:00:00.000'")
    if end_dt:
        where.append(f"rpt_dt < '{end_dt}T00:00:00.000'")

    if boro and boro != "All":
        where.append(f"boro_nm = '{boro}'")

    if law_cat and law_cat != "All":
        where.append(f"law_cat_cd = '{law_cat}'")

    params = {
        "$select": f"{group_col}, count(*) as crime_count",
        "$where": " AND ".join(where),
        "$group": group_col,
        "$order": "crime_count DESC",
        "$limit": top_n,
    }

    r = SESSION.get(DATASET2_BASE, params=params, timeout=120)
    r.raise_for_status()
    df = pd.DataFrame(r.json())

    # Ensure numeric
    if "crime_count" in df.columns:
        df["crime_count"] = pd.to_numeric(df["crime_count"], errors="coerce")

    return df


# -------------------------
# UI
# -------------------------
st.write(
    "This page pulls from NYC OpenData and shows a bar chart of crime counts by precinct. "
    "It answers RQ3: Crime vs Misconduct allegations by precinct"
)

with st.spinner("Loading preview to detect columns..."):
    df_preview = load_preview(2000)

if df_preview.empty:
    st.error(
        "NYC OpenData timed out or returned no data. Try again, or reduce the "
        "preview size / widen timeout."
    )
    st.stop()

# Sidebar filters
st.sidebar.subheader("Filters (optional)")

# keep defaults modest; this dataset is huge
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

# Suggest “area/unit” columns similar to Dataset 1 logic
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
candidates = [
    c for c in df_preview.columns if any(k in c.lower() for k in community_keywords)
]
if not candidates:
    candidates = list(df_preview.columns)

# Prefer precinct if present
default_idx = 0
for i, c in enumerate(candidates):
    if c.lower() == "addr_pct_cd":
        default_idx = i
        break

# Convert API names to readable names
friendly_options = {COLUMN_LABELS.get(col, col): col for col in candidates}

friendly_names = list(friendly_options.keys())

group_col = "addr_pct_cd"
group_col_label = "Precinct"
top_n = 100

# Convert back to API name for querying
group_col = friendly_options[group_col_label]

top_n = st.slider("Show top N groups", min_value=5, max_value=50, value=20, step=5)

st.subheader("2) Bar chart: Crime counts by selected group")

with st.spinner("Aggregating counts from NYC OpenData (server-side)..."):
    try:
        counts = fetch_group_counts(
            group_col=group_col,
            top_n=top_n,
            start_dt=start_date.strftime("%Y-%m-%d") if start_date else None,
            end_dt=end_date.strftime("%Y-%m-%d") if end_date else None,
            boro=None if boro == "All" else boro,
            law_cat=None if law_cat == "All" else law_cat,
        )
        # Keep only valid precinct rows and make precinct numeric
        crime_by_precinct = counts.dropna(subset=[group_col]).copy()

        crime_by_precinct["precinct"] = pd.to_numeric(
            crime_by_precinct[group_col], errors="coerce"
        )

        crime_by_precinct = crime_by_precinct.dropna(subset=["precinct"])
        crime_by_precinct["precinct"] = crime_by_precinct["precinct"].astype(int)
        crime_by_precinct = crime_by_precinct[["precinct", "crime_count"]]

        # Add readable precinct names
        crime_by_precinct["Precinct Name"] = "Precinct " + crime_by_precinct[
            "precinct"
        ].astype(str)

        # Checking if worked
        st.subheader("Crime by precinct preview")

        st.write("First few rows:")
        st.write(crime_by_precinct.head())

    except requests.HTTPError as e:
        st.error(
            "NYC OpenData request failed. This can happen if the chosen column "
            "cannot be grouped (or the API rejects the query). Try a different column."
        )
        st.exception(e)
        st.stop()

if counts.empty or group_col not in counts.columns:
    st.warning(
        "No results returned. Try a different grouping column or widen your date range."
    )
    st.stop()

# Clean labels
counts = counts.dropna(subset=[group_col]).copy()
counts[group_col] = counts[group_col].astype(str)

title = (
    f"Crime count by {group_col_label} (Top {top_n})"
    f" | {start_date} to {end_date}"
    + ("" if boro == "All" else f" | {boro}")
    + ("" if law_cat == "All" else f" | {law_cat}")
)

# Bar chart of crime counts by precinct
fig = px.bar(
    crime_by_precinct,
    x="Precinct Name",
    y="crime_count",
    title="Crime Count by Precinct",
)

fig.update_layout(xaxis_title="Precinct", yaxis_title="Crime Count")

st.plotly_chart(fig, use_container_width=True)

# Show the exact columns to merge on later
st.info(
        "For your research question, the key precinct column in Dataset 2 is "
        "**`addr_pct_cd`**. "
        "Aggregate to **crime_count by addr_pct_cd**, then merge with Dataset 1’s "
        "**misconduct_count by precinct** "
        "using 'precinct'/'addr_pct_cd' (make sure both are numeric or both are strings)."
)


# Load Dataset 1 misconduct counts by precinct for reference
@st.cache_data(show_spinner=False)
def load_dataset1_officers(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


# Build misconduct counts from Dataset 1
misconduct_counts = misconduct_by_precinct(officers_df)

# Merge and visualize relationship
merged = crime_by_precinct.merge(
    misconduct_counts,
    on="precinct",
    how="inner",
)
