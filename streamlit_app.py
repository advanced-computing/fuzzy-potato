# streamlit_app.py
# Streamlit app: load NYC OpenData (Socrata) and draw a line chart over time by police unit.
# Fix: use requests + params so spaces in $where/$order are URL-encoded properly.

import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="NYC OpenData – Allegations Over Time", layout="wide")

st.title("Part 2 Streamlit App")
st.write("Team: Emily Chu, Elsie Zhang")  # <-- change names if needed

DATASET1_BASE = "https://data.cityofnewyork.us/resource/6xgr-kwjq.json"


# -------------------------
# 1) Load a small preview to detect columns
# -------------------------
@st.cache_data(show_spinner=False)
def load_preview(n_rows: int = 2000) -> pd.DataFrame:
    params = {"$limit": n_rows}
    r = requests.get(DATASET1_BASE, params=params, timeout=30)
    r.raise_for_status()
    return pd.DataFrame(r.json())


with st.spinner("Loading a small preview to detect columns..."):
    df_preview = load_preview(2000)

st.subheader("Choose columns")

# Detect likely date columns
date_candidates = [c for c in df_preview.columns if "date" in c.lower() or "time" in c.lower()]
if not date_candidates:
    date_candidates = list(df_preview.columns)

# Detect likely police unit columns
unit_keywords = ["command", "precinct", "pct", "boro", "borough", "unit"]
unit_candidates = [c for c in df_preview.columns if any(k in c.lower() for k in unit_keywords)]
if not unit_candidates:
    unit_candidates = list(df_preview.columns)

date_col = st.selectbox("Choose a DATE column", options=date_candidates)
unit_col = st.selectbox("Choose a POLICE UNIT column", options=unit_candidates)

limit = st.slider("Rows to fetch (ordered by date ASC)", 2000, 50000, 15000, step=1000)

use_filter = st.checkbox("Filter to incidents after a given date (recommended)", value=True)
start_date = st.date_input("Start date", value=pd.to_datetime("2016-01-01").date()) if use_filter else None


# -------------------------
# 2) Load ordered data (KEY FIX: requests params auto-encode spaces)
# -------------------------
@st.cache_data(show_spinner=False)
def load_ordered_data(date_column: str, unit_column: str, n_rows: int, start_date_str: str | None) -> pd.DataFrame:
    # Build SoQL params safely
    params = {
        "$select": f"{date_column},{unit_column}",
        "$where": f"{date_column} IS NOT NULL",
        "$order": f"{date_column} ASC",
        "$limit": n_rows,
    }

    # Optional: filter by start date
    if start_date_str:
        # Combine conditions
        params["$where"] = f"{date_column} IS NOT NULL AND {date_column} >= '{start_date_str}'"

    r = requests.get(DATASET1_BASE, params=params, timeout=60)
    r.raise_for_status()
    return pd.DataFrame(r.json())


start_date_str = str(start_date) if use_filter else None

with st.spinner("Loading ordered data from NYC OpenData..."):
    df = load_ordered_data(date_col, unit_col, limit, start_date_str)

st.subheader("Dataset preview (ordered sample)")
st.write(f"Rows: {len(df):,} | Columns: {list(df.columns)}")
st.dataframe(df.head(30), use_container_width=True)


# -------------------------
# 3) Build time buckets and aggregate counts
# -------------------------
st.subheader("Line chart: Allegations Over Time by Police Unit (Figure 2 style)")

granularity = st.selectbox("Time granularity", ["Year", "Month"], index=0)
top_k = st.slider("Show top K units (by total allegations)", 3, 15, 8)

tmp = df[[date_col, unit_col]].dropna().copy()

# Convert date column to datetime
tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
tmp = tmp.dropna(subset=[date_col])

# Create time buckets
if granularity == "Year":
    tmp["time_bucket"] = tmp[date_col].dt.year.astype("Int64").astype(str)
else:
    tmp["time_bucket"] = tmp[date_col].dt.to_period("M").astype(str)

# Aggregate counts
counts = (
    tmp.groupby(["time_bucket", unit_col])
       .size()
       .reset_index(name="allegation_count")
)

# Debug checks
st.caption("Debug checks (to ensure multiple time points):")
c1, c2, c3 = st.columns(3)
with c1:
    st.write("Min date:", tmp[date_col].min())
with c2:
    st.write("Max date:", tmp[date_col].max())
with c3:
    st.write("Unique time buckets:", tmp["time_bucket"].nunique())

# Keep only top K units overall
top_units = (
    counts.groupby(unit_col)["allegation_count"]
          .sum()
          .sort_values(ascending=False)
          .head(top_k)
          .index
)
counts = counts[counts[unit_col].isin(top_units)].copy()
counts = counts.sort_values("time_bucket")

if counts["time_bucket"].nunique() < 2:
    st.warning(
        "Not enough time points to draw lines (only 1 time bucket). "
        "Try increasing rows, using an earlier start date, or selecting a different DATE column."
    )
else:
    fig = px.line(
        counts,
        x="time_bucket",
        y="allegation_count",
        color=unit_col,
        markers=True,
        title="Allegations Over Time by Police Unit",
    )
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Number of Allegations",
        legend_title="Police Unit",
    )
    st.plotly_chart(fig, use_container_width=True)

with st.expander("See aggregated table"):
    st.dataframe(counts, use_container_width=True)
