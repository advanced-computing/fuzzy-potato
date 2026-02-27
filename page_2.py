# page_2.py
# CCRB Officer Snapshot (2fir-qns4)
# RQ1: Concentration (Lorenz + Gini)
# RQ2: Risk Matrix (Group by Current Command / Current Rank)

from __future__ import annotations

import pandas as pd
import requests
import streamlit as st

from utils import (
    compute_group_stats,
    plot_lorenz_curves,
    plot_risk_matrix,  # (plot_command_risk_matrix is also available as alias if you prefer)
)

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
# Socrata config
# -----------------------------
SOCRATA_URL = "https://data.cityofnewyork.us/resource/2fir-qns4.json"

API_TO_DF: dict[str, str] = {
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

NUMERIC_COLS = ["Total Complaints", "Total Substantiated Complaints"]


# -----------------------------
# HTTP helpers
# -----------------------------
def _get_json(params: dict[str, str], timeout: int = 60) -> list[dict]:
    r = requests.get(SOCRATA_URL, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def _latest_as_of_date() -> str | None:
    """
    Returns latest as_of_date as YYYY-MM-DD (best-effort).
    """
    params = {"$select": "max(as_of_date) as max_date", "$limit": "1"}
    data = _get_json(params)
    if not data:
        return None
    raw = data[0].get("max_date")
    if not raw:
        return None
    return str(raw)[:10]


def _build_where_clause(as_of_date: str | None) -> str | None:
    """Build Socrata WHERE clause for date filtering."""
    if not as_of_date:
        return None
    return f"as_of_date >= '{as_of_date}T00:00:00.000' AND as_of_date < '{as_of_date}T23:59:59.999'"


def _fetch_all_rows(
    select_fields: str,
    where_clause: str | None,
    max_rows: int | None,
) -> list[dict[str, object]]:
    """Fetch all rows from Socrata with pagination."""
    rows: list[dict[str, object]] = []
    limit = 50_000
    offset = 0
    offset = 0

    while True:
        batch_limit = limit
        if max_rows is not None:
            remaining = max_rows - len(rows)
            if remaining <= 0:
                break
            batch_limit = min(batch_limit, remaining)

        params = {"$select": select_fields, "$limit": str(batch_limit), "$offset": str(offset)}
        if where_clause:
            params["$where"] = where_clause

        batch = _get_json(params)
        if not batch:
            break

        rows.extend(batch)
        offset += len(batch)

        if len(batch) < batch_limit:
            break

    return rows


def _process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Process and clean the dataframe."""
    if df.empty:
        return pd.DataFrame(columns=list(API_TO_DF.values()))

    df = df.rename(columns=API_TO_DF)
    df = df[[c for c in API_TO_DF.values() if c in df.columns]].copy()

    # types
    if "As Of Date" in df.columns:
        as_of = pd.to_datetime(df["As Of Date"], errors="coerce")
        df["As Of Date"] = as_of.dt.date.astype("string")

    for c in NUMERIC_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    # friendly categorical fills
    for c in ["Current Command", "Current Rank", "Officer Race", "Officer Gender"]:
        if c in df.columns:
            df[c] = df[c].fillna("Unknown")

    return df


@st.cache_data(show_spinner=False)
def load_snapshot(
    as_of_date: str | None,
    max_rows: int | None = None,
) -> pd.DataFrame:
    """
    Load 2fir-qns4 snapshot from Socrata.
    If as_of_date is provided, filter to that date (snapshot day).
    """
    select_fields = ", ".join(API_TO_DF.keys())
    where_clause = _build_where_clause(as_of_date)
    rows = _fetch_all_rows(select_fields, where_clause, max_rows)
    df = pd.DataFrame(rows)
    return _process_dataframe(df)


# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Controls")

auto_latest = st.sidebar.checkbox("Use latest snapshot date", value=True)

latest = None
if auto_latest:
    with st.sidebar.spinner("Fetching latest as_of_date…"):
        latest = _latest_as_of_date()

as_of_date = (
    st.sidebar.text_input(
        "Snapshot date (YYYY-MM-DD)",
        value=latest or "",
        help="This dataset is a daily snapshot; all rows typically share the same As Of Date.",
    ).strip()
    or None
)

max_rows_ui = st.sidebar.number_input(
    "Max rows to load (0 = all)",
    min_value=0,
    value=0,
    step=10000,
    help="For faster development you can limit rows.",
)
max_rows = None if int(max_rows_ui) == 0 else int(max_rows_ui)

if st.sidebar.button("Clear cache"):
    st.cache_data.clear()
    st.sidebar.success("Cache cleared. Rerun.")

# -----------------------------
# Load data
# -----------------------------
with st.spinner("Loading snapshot…"):
    df = load_snapshot(as_of_date=as_of_date, max_rows=max_rows)

if df.empty:
    st.error("No data returned. Check date format or network.")
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
    as_of_str = str(df["As Of Date"].dropna().iloc[0])

m4.metric("As Of Date", as_of_str)

st.divider()

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3 = st.tabs(
    ["RQ1 — Concentration (Lorenz/Gini)", "RQ2 — Risk Matrix (Group)", "Preview / Download"]
)

# -----------------------------
# RQ1
# -----------------------------
with tab1:
    st.subheader("RQ1: Are complaints concentrated among a small subset of officers?")

    st.markdown(
        "This plot compares how **Total Complaints** and "
        "**Total Substantiated Complaints** are distributed across officers. "
        "If the curve bows far below the equality line, outcomes are "
        "concentrated among fewer officers."
    )

    as_of_str = None
    if "As Of Date" in df.columns and df["As Of Date"].notna().any():
        as_of_str = str(df["As Of Date"].dropna().iloc[0])

    fig, ax, summary = plot_lorenz_curves(
        total_values=df["Total Complaints"].tolist(),
        subst_values=df["Total Substantiated Complaints"].tolist(),
        as_of_date=as_of_str,
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
with tab2:
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
with tab3:
    st.subheader("Preview")
    st.dataframe(df.head(200), use_container_width=True)

    st.download_button(
        "Download loaded snapshot as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"ccrb_officer_snapshot_{(as_of_date or 'all')}.csv",
        mime="text/csv",
    )
