from __future__ import annotations

import time

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from bigquery_helpers import load_table

start_time = time.time()

st.set_page_config(page_title="RQ1 | Complaint Extremes", layout="wide")
st.title(
    "RQ1: How extreme are the highest-complaint officers relative to the overall distribution?"
)
st.caption(
    "This page compares the highest-complaint officers with the overall distribution "
    "of complaints across all officers."
)

PROJECT_ID = "fuzzy-potato-491318"
DATASET_NAME = "Project_Part5"
TABLE_NAME = "officers"

BQ_TO_DF: dict[str, str] = {
    "as_of_date": "As Of Date",
    "tax_id": "Tax ID",
    "officer_first_name": "Officer First Name",
    "officer_last_name": "Officer Last Name",
    "current_rank": "Current Rank",
    "current_command": "Current Command",
    "shield_no": "Shield No",
    "total_complaints": "Total Complaints",
    "total_substantiated_complaints": "Total Substantiated Complaints",
}

NUMERIC_COLS = [
    "Tax ID",
    "Shield No",
    "Total Complaints",
    "Total Substantiated Complaints",
]

DATE_COLS = ["As Of Date"]


def _process_dataframe(df: pd.DataFrame) -> pd.DataFrame:  # noqa: C901
    if df.empty:
        return pd.DataFrame(columns=list(BQ_TO_DF.values()))

    df = df.rename(columns=BQ_TO_DF)
    df = df[[c for c in BQ_TO_DF.values() if c in df.columns]].copy()

    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["Total Complaints", "Total Substantiated Complaints"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    for col in DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    for col in ["Current Command", "Current Rank"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    for col in ["Officer First Name", "Officer Last Name"]:
        if col in df.columns:
            df[col] = df[col].fillna("")

    return df


@st.cache_data(show_spinner=False)
def load_snapshot(max_rows: int | None = None) -> pd.DataFrame:
    needed_cols = list(BQ_TO_DF.keys())

    df = load_table(
        PROJECT_ID,
        DATASET_NAME,
        TABLE_NAME,
        columns=needed_cols,
        limit=max_rows,
    )

    return _process_dataframe(df)


def build_officer_label(df: pd.DataFrame) -> pd.Series:
    if "Shield No" in df.columns:
        shield = df["Shield No"].fillna(-1).astype(int).astype(str)
    else:
        shield = pd.Series(["Unknown"] * len(df), index=df.index)

    if "Officer Last Name" in df.columns:
        last_name = df["Officer Last Name"].replace("", "Unknown")
    else:
        last_name = pd.Series(["Unknown"] * len(df), index=df.index)

    return "Shield " + shield + " - " + last_name


def prepare_ranked_data(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work = work.sort_values("Total Complaints", ascending=False).reset_index(drop=True)
    work["Officer Label"] = build_officer_label(work)
    return work


st.sidebar.header("Controls")

max_rows_ui = st.sidebar.number_input(
    "Max rows to load (0 = all)",
    min_value=0,
    value=0,
    step=5000,
)
max_rows = None if int(max_rows_ui) == 0 else int(max_rows_ui)

top_n = st.sidebar.slider(
    "Show top N officers",
    min_value=10,
    max_value=50,
    value=20,
    step=5,
)

if st.sidebar.button("Clear cache"):
    st.cache_data.clear()
    st.sidebar.success("Cache cleared. Rerun.")

df = load_snapshot(max_rows=max_rows)

if df.empty:
    st.error("No data returned from BigQuery.")
    st.stop()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Officers (rows)", f"{len(df):,}")
m2.metric("Total complaints", f"{int(df['Total Complaints'].sum()):,}")
m3.metric("Total substantiated", f"{int(df['Total Substantiated Complaints'].sum()):,}")

as_of_str = "Unknown"
if "As Of Date" in df.columns and df["As Of Date"].notna().any():
    as_of_str = str(df["As Of Date"].dropna().max().date())
m4.metric("Latest As Of Date", as_of_str)

st.divider()

ranked_df = prepare_ranked_data(df)
bar_df = ranked_df.head(top_n).copy()

# -----------------------------
# Figure A: Top officers
# -----------------------------
st.markdown("### Figure A. Top officers by total complaints")
st.markdown(
    "This bar chart highlights the officers with the highest complaint counts. "
    "It shows the scale of the most complained-about officers directly."
)

fig_bar = px.bar(
    bar_df,
    x="Officer Label",
    y="Total Complaints",
    title=f"Top {top_n} Officers by Total Complaints",
    hover_data={
        "Current Command": True,
        "Current Rank": True,
        "Total Substantiated Complaints": True,
    },
)

fig_bar.update_layout(
    xaxis_title="Officer",
    yaxis_title="Total Complaints",
    xaxis_tickangle=-35,
)

st.plotly_chart(fig_bar, use_container_width=True)

# -----------------------------
# Figure B: Distribution by complaint bucket
# -----------------------------

st.markdown("### Figure B. Distribution of officers by complaint level")
st.markdown(
    "This chart groups officers into complaint-count buckets. "
    "It shows that most officers are concentrated in the lowest complaint ranges, "
    "while only a small number fall into the high-complaint tail."
)

bucket_df = df.copy()

# 手动分桶
bucket_df["Complaint Bucket"] = "11+"
bucket_df.loc[bucket_df["Total Complaints"] == 0, "Complaint Bucket"] = "0"
bucket_df.loc[bucket_df["Total Complaints"] == 1, "Complaint Bucket"] = "1"
bucket_df.loc[bucket_df["Total Complaints"].between(2, 3), "Complaint Bucket"] = "2–3"
bucket_df.loc[bucket_df["Total Complaints"].between(4, 5), "Complaint Bucket"] = "4–5"
bucket_df.loc[bucket_df["Total Complaints"].between(6, 10), "Complaint Bucket"] = "6–10"

bucket_order = ["0", "1", "2–3", "4–5", "6–10", "11+"]

bucket_counts = (
    bucket_df.groupby("Complaint Bucket")
    .size()
    .reindex(bucket_order, fill_value=0)
    .reset_index(name="Number of Officers")
)

st.dataframe(bucket_counts, use_container_width=True, hide_index=True)

bucket_counts["Share of Officers (%)"] = (
    bucket_counts["Number of Officers"] / bucket_counts["Number of Officers"].sum() * 100
).round(1)

fig_bucket = go.Figure()

fig_bucket.add_trace(
    go.Bar(
        x=bucket_counts["Share of Officers (%)"].tolist(),
        y=bucket_counts["Complaint Bucket"].astype(str).tolist(),
        orientation="h",
        text=[f"{v:.1f}%" for v in bucket_counts["Share of Officers (%)"]],
        textposition="outside",
        name="Share of Officers",
    )
)

fig_bucket.update_layout(
    title="Share of Officers by Complaint Count Bucket",
    xaxis_title="Share of Officers (%)",
    yaxis_title="Complaint Count Bucket",
    showlegend=False,
    margin=dict(l=80, r=40, t=60, b=40),
)

fig_bucket.update_yaxes(
    type="category",
    categoryorder="array",
    categoryarray=bucket_order[::-1],
)

st.plotly_chart(fig_bucket, use_container_width=True)

# -----------------------------
# Summary table
# -----------------------------
q1 = df["Total Complaints"].quantile(0.25)
q3 = df["Total Complaints"].quantile(0.75)
iqr = q3 - q1
upper_fence = q3 + 1.5 * iqr
outlier_share = (df["Total Complaints"] > upper_fence).mean() * 100

summary_table = pd.DataFrame(
    [
        {"Metric": "Mean complaints per officer", "Value": f"{df['Total Complaints'].mean():.2f}"},
        {
            "Metric": "Median complaints per officer",
            "Value": f"{df['Total Complaints'].median():.2f}",
        },
        {"Metric": "75th percentile", "Value": f"{q3:.2f}"},
        {"Metric": "Maximum complaints", "Value": f"{df['Total Complaints'].max():.0f}"},
        {
            "Metric": "Officers with zero complaints",
            "Value": f"{(df['Total Complaints'] == 0).mean() * 100:.1f}%",
        },
        {"Metric": "Share above box-plot outlier threshold", "Value": f"{outlier_share:.1f}%"},
    ]
)

st.markdown("### Distribution Summary")
st.dataframe(summary_table, use_container_width=True, hide_index=True)

# -----------------------------
# Top officers table
# -----------------------------
top_table = bar_df[
    [
        c
        for c in [
            "Officer Label",
            "Current Command",
            "Current Rank",
            "Total Complaints",
            "Total Substantiated Complaints",
        ]
        if c in bar_df.columns
    ]
].copy()

st.markdown(f"### Top {top_n} Officers Table")
st.dataframe(top_table, use_container_width=True, hide_index=True)

# -----------------------------
# Interpretation
# -----------------------------
median_val = df["Total Complaints"].median()
max_val = df["Total Complaints"].max()
zero_share = (df["Total Complaints"] == 0).mean() * 100

st.markdown("### Key takeaway")
st.write(
    f"The distribution is highly uneven: the median officer has {median_val:.0f} complaints, "
    f"{zero_share:.1f}% of officers have zero complaints, while the highest observed value is "
    f"{max_val:.0f}. This suggests that the most complained-about officers are extreme relative "
    f"to the overall distribution rather than representative of the typical officer."
)

elapsed = time.time() - start_time
st.caption(f"Page loaded in {elapsed:.2f} seconds")

if st.button("Back to Homepage"):
    st.switch_page("main_page.py")
