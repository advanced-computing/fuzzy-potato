# page_2.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.markdown("# Dataset 1: NYC OpenData – Complaints by Community")
st.sidebar.markdown("# Dataset 1: Complaints by Community")

DATASET1_BASE = "https://data.cityofnewyork.us/resource/6xgr-kwjq.json"

# -------------------------
# Helpers
# -------------------------
@st.cache_data(show_spinner=False)
def load_preview(n_rows: int = 2000) -> pd.DataFrame:
    """Load a small sample to detect available columns."""
    params = {"$limit": n_rows}
    r = requests.get(DATASET1_BASE, params=params, timeout=30)
    r.raise_for_status()
    return pd.DataFrame(r.json())

@st.cache_data(show_spinner=False)
def fetch_group_counts(group_col: str, top_n: int) -> pd.DataFrame:
    """
    Server-side aggregation:
    SELECT group_col, count(*) as complaint_count
    WHERE group_col is not null
    GROUP BY group_col
    ORDER BY complaint_count desc
    LIMIT top_n
    """
    params = {
        "$select": f"{group_col}, count(*) as complaint_count",
        "$where": f"{group_col} IS NOT NULL",
        "$group": group_col,
        "$order": "complaint_count DESC",
        "$limit": top_n,
    }
    r = requests.get(DATASET1_BASE, params=params, timeout=60)
    r.raise_for_status()
    df = pd.DataFrame(r.json())

    # Ensure numeric
    if "complaint_count" in df.columns:
        df["complaint_count"] = pd.to_numeric(df["complaint_count"], errors="coerce")

    return df

# -------------------------
# UI
# -------------------------
st.write(
    "This page pulls data from NYC OpenData and shows a bar chart of complaint counts by a selected community-like field."
)

with st.spinner("Loading preview to detect columns..."):
    df_preview = load_preview(2000)

if df_preview.empty:
    st.error("Preview returned no data. The dataset endpoint may be unavailable right now.")
    st.stop()

st.subheader("1) Choose a 'community' column")

# Try to guess "community" fields; if none match, let user pick anything
community_keywords = [
    "community", "board", "district", "neighborhood", "neighbourhood",
    "boro", "borough", "precinct", "pct", "command", "zip"
]
candidates = [
    c for c in df_preview.columns
    if any(k in c.lower() for k in community_keywords)
]
if not candidates:
    candidates = list(df_preview.columns)

default_idx = 0
for i, c in enumerate(candidates):
    if "community" in c.lower():
        default_idx = i
        break

community_col = st.selectbox(
    "Pick a column to represent 'community / area / unit'",
    options=candidates,
    index=default_idx if candidates else 0,
)

top_n = st.slider("Show top N communities", min_value=5, max_value=50, value=20, step=5)

st.subheader("2) Bar chart: Complaint counts by community")

with st.spinner("Aggregating counts from NYC OpenData (server-side)..."):
    try:
        counts = fetch_group_counts(community_col, top_n)
    except requests.HTTPError as e:
        st.error(
            "NYC OpenData request failed. This often happens if the chosen column "
            "cannot be grouped (or the API rejects the query). Try a different column."
        )
        st.exception(e)
        st.stop()

if counts.empty or community_col not in counts.columns:
    st.warning("No results returned. Try a different column.")
    st.stop()

# Clean labels
counts = counts.dropna(subset=[community_col]).copy()
counts[community_col] = counts[community_col].astype(str)

fig = px.bar(
    counts,
    x=community_col,
    y="complaint_count",
    title=f"Complaint count by {community_col} (Top {top_n})",
)
fig.update_layout(xaxis_title=community_col, yaxis_title="Complaint count")
st.plotly_chart(fig, use_container_width=True)

with st.expander("See aggregated table"):
    st.dataframe(counts, use_container_width=True)
