# page_2.py
# CCRB Officer Snapshot (2fir-qns4)
# RQ1: Concentration (Lorenz + Gini)
# RQ2: Risk Matrix (Group by Current Command / Current Rank)

from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from bigquery_helpers import load_table  # type: ignore
from utils import (
    compute_group_stats,
    plot_lorenz_curves,
    plot_risk_matrix,
)

start_time = time.time()
# -----------------------------
# Page config + title
# -----------------------------
st.set_page_config(page_title="CCRB Officer Snapshot | RQ1 & RQ2", layout="wide")
st.title("CCRB Officer Snapshot: RQ1 Concentration & RQ2 Risk Matrix")
st.caption(
    "NYC Open Data (CCRB) officer-level snapshot. "
    "RQ1 examines concentration across officers; RQ2 compares group-level risk patterns."
)

# -----------------------------
# BigQuery config
# -----------------------------
PROJECT_ID = "fuzzy-potato-491318"
DATASET_NAME = "Project_Part5"
TABLE_NAME = "officers"

BQ_TO_DF: dict[str, str] = {
    "as_of_date": "As Of Date",
    "tax_id": "Tax ID",
    "active_per_last_reported_status": "Active Per Last Reported Status",
    "last_reported_active_date": "Last Reported Active Date",
    "officer_first_name": "Officer First Name",
    "officer_last_name": "Officer Last Name",
    "officer_race": "Officer Race",
    "officer_gender": "Officer Gender",
    "current_rank_abbreviation": "Current Rank Abbreviation",
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

DATE_COLS = [
    "As Of Date",
    "Last Reported Active Date",
]


def _process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Process and clean the dataframe loaded from BigQuery."""
    if df.empty:
        return pd.DataFrame(columns=list(BQ_TO_DF.values()))

    # rename to the display column names used by the rest of the page
    df = df.rename(columns=BQ_TO_DF)

    # keep only expected columns that actually exist
    df = df[[c for c in BQ_TO_DF.values() if c in df.columns]].copy()

    # numeric conversions
    for col in NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # keep complaint counts as ints for downstream summaries
    for col in ["Total Complaints", "Total Substantiated Complaints"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    # dates
    for col in DATE_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # friendly categorical fills
    for col in ["Current Command", "Current Rank", "Officer Race", "Officer Gender"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

    return df


@st.cache_data(show_spinner=False)
def load_snapshot(max_rows: int | None = None) -> pd.DataFrame:
    """
    Load officer snapshot from BigQuery.
    """

    needed_cols = list(BQ_TO_DF.keys())

    df = load_table(
        PROJECT_ID,
        DATASET_NAME,
        TABLE_NAME,
        columns=needed_cols,
        limit=max_rows,
    )

    df = _process_dataframe(df)

    return df


@st.cache_data(show_spinner=False)
def convert_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Controls")

max_rows_ui = st.sidebar.number_input(
    "Max rows to load (0 = all)",
    min_value=0,
    value=5000,
    step=5000,
    help="For faster development you can limit rows.",
)
max_rows = None if int(max_rows_ui) == 0 else int(max_rows_ui)

if st.sidebar.button("Clear cache"):
    st.cache_data.clear()
    st.sidebar.success("Cache cleared. Rerun.")

# -----------------------------
# Load data
# -----------------------------
with st.spinner("Loading snapshot from BigQuery..."):
    df = load_snapshot(max_rows=max_rows)

if df.empty:
    st.error("No data returned from BigQuery.")
    st.stop()

# Summary metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("Officers (rows)", f"{len(df):,}")
m2.metric("Total complaints (sum)", f"{int(df['Total Complaints'].sum()):,}")
m3.metric(
    "Total substantiated (sum)",
    f"{int(df['Total Substantiated Complaints'].sum()):,}",
)

as_of_str = "Unknown"
if "As Of Date" in df.columns and df["As Of Date"].notna().any():
    as_of_str = str(df["As Of Date"].dropna().max().date())

m4.metric("Latest As Of Date", as_of_str)

st.divider()

# -----------------------------
# Tabs
# -----------------------------
section = st.sidebar.radio(
    "Choose section",
    ["RQ1 – Concentration (Lorenz/Gini)", "RQ2 – Risk Matrix (Group)", "Preview / Download"],
)

# -----------------------------
# RQ1
# -----------------------------
if section == "RQ1 – Concentration (Lorenz/Gini)":
    st.subheader("RQ1: Are complaints concentrated among a small subset of officers?")

    st.markdown(
        "This plot compares how **Total Complaints** and "
        "**Total Substantiated Complaints** are distributed across officers. "
        "If the curve bows far below the equality line, outcomes are "
        "concentrated among fewer officers."
    )

    rq1_as_of_str = None
    if "As Of Date" in df.columns and df["As Of Date"].notna().any():
        rq1_as_of_str = str(df["As Of Date"].dropna().max().date())

    fig, ax, summary = plot_lorenz_curves(
        total_values=df["Total Complaints"].tolist(),
        subst_values=df["Total Substantiated Complaints"].tolist(),
        as_of_date=rq1_as_of_str,
    )
    st.pyplot(fig, clear_figure=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gini (Total)", f"{summary['gini_total']:.3f}")
    c2.metric("Gini (Substantiated)", f"{summary['gini_subst']:.3f}")
    c3.metric("Top 1% share (Total)", f"{summary['top_1pct_share_total'] * 100:.1f}%")
    c4.metric("Top 5% share (Total)", f"{summary['top_5pct_share_total'] * 100:.1f}%")

    st.caption(
        "Interpretation: Higher Gini means greater concentration. "
        "Top 1%/5% shares show how much of total complaints come from the "
        "most-complained-about officers."
    )

# -----------------------------
# RQ2
# -----------------------------
elif section == "RQ2 – Risk Matrix (Group)":
    st.subheader(
        "RQ2: Which groups show higher complaint burden and higher substantiation intensity?"
    )

    st.markdown(
        "**Risk Matrix definition**\n"
        "- **X** = average complaints per officer in the group (burden)\n"
        "- **Y** = substantiated per 100 complaints (intensity)\n"
        "- **Bubble size** = number of officers in the group\n"
        "\n"
        "Choose whether groups are defined by **Current Command** or **Current Rank**."
    )

    left, right = st.columns([1, 2], gap="large")

    with left:
        group_col = st.selectbox("Group by", ["Current Command", "Current Rank"], index=0)
        min_officers = st.slider("Minimum officers per group", 50, 1000, 200, step=50)
        annotate_n = st.slider("Annotate top-N (by avg complaints)", 0, 20, 0, step=1)

    group_stats = compute_group_stats(
        df,
        group_col=group_col,
        min_officers=int(min_officers),
    )

    if group_stats.table.empty:
        st.warning("No groups remain after filtering. Lower 'Minimum officers per group'.")
    else:
        fig2, ax2 = plot_risk_matrix(
            group_stats,
            title=f"Risk Matrix (Grouped by {group_col}) — Snapshot",
            annotate_top_n=int(annotate_n),
        )
        st.pyplot(fig2, clear_figure=True)

        st.markdown("### Group table")
        st.dataframe(
            group_stats.table.sort_values("avg_complaints_per_officer", ascending=False),
            use_container_width=True,
        )

        st.download_button(
            "Download group stats as CSV",
            data=group_stats.table.to_csv(index=False).encode("utf-8"),
            file_name=f"rq2_group_stats_{group_col.replace(' ', '_').lower()}.csv",
            mime="text/csv",
        )

# -----------------------------
# Preview / Download
# -----------------------------
elif section == "Preview / Download":
    st.subheader("Preview")

    with st.expander("Show data preview"):
        st.dataframe(df.head(50), use_container_width=True)

    export_date = "latest"
    if "As Of Date" in df.columns and df["As Of Date"].notna().any():
        export_date = str(df["As Of Date"].dropna().max().date())

    st.download_button(
        "Download loaded snapshot as CSV",
        data=convert_to_csv(df),
        file_name=f"ccrb_officer_snapshot_{export_date}.csv",
        mime="text/csv",
    )

elapsed = time.time() - start_time
st.caption(f"Page loaded in {elapsed:.2f} seconds")
