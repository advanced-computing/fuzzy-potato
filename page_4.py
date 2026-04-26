from __future__ import annotations

import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from bigquery_helpers import load_table
from utils import compute_group_stats

start_time = time.time()

st.set_page_config(page_title="RQ2 | Group Risk Ranking", layout="wide")
st.title("RQ2: Which groups show the highest complaint burden and substantiation intensity?")
st.caption(
    "This page compares officer groups using a quadrant bubble chart and two ranked views: "
    "average complaints per officer and substantiated complaints per 100 complaints."
)

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

    for col in ["Current Command", "Current Rank", "Officer Race", "Officer Gender"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown")

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


@st.cache_data(show_spinner=False)
def cached_group_stats(df: pd.DataFrame, group_col: str, min_officers: int):
    return compute_group_stats(df, group_col=group_col, min_officers=min_officers)


def first_existing_col(df: pd.DataFrame, candidates: list[str]) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(f"None of these columns were found: {candidates}")


def plot_quadrant_bubble_chart(  # noqa: PLR0913
    df: pd.DataFrame,
    group_name_col: str,
    burden_col: str,
    intensity_col: str,
    size_col: str | None = None,
    top_n: int = 10,
    scope: str = "Top union only",
    size_mode: str = "Group size",
    size_scale: float = 1.0,
):
    work = df.copy()

    # 决定哪些点要打标签
    top_burden = work.sort_values(burden_col, ascending=False).head(top_n)
    top_intensity = work.sort_values(intensity_col, ascending=False).head(top_n)
    label_df = (
        pd.concat([top_burden, top_intensity], axis=0)
        .drop_duplicates(subset=[group_name_col])
        .copy()
    )

    # 决定画哪些点
    if scope == "Top union only":
        work = label_df.copy()

    x = work[burden_col].astype(float)
    y = work[intensity_col].astype(float)

    # 决定气泡大小
    if size_mode == "Group size" and size_col and size_col in work.columns:
        sizes_raw = work[size_col].astype(float)
        if sizes_raw.max() > 0:
            sizes = (120 + (sizes_raw / sizes_raw.max()) * 900) * size_scale
        else:
            sizes = np.repeat(260 * size_scale, len(work))
    else:
        sizes = np.repeat(260 * size_scale, len(work))

    x_med = float(df[burden_col].median())
    y_med = float(df[intensity_col].median())

    fig, ax = plt.subplots(figsize=(11, 7))

    x_min, x_max = x.min(), x.max()
    y_min, y_max = y.min(), y.max()

    x_pad = (x_max - x_min) * 0.15 if x_max > x_min else 1
    y_pad = (y_max - y_min) * 0.15 if y_max > y_min else 1

    x0, x1 = x_min - x_pad, x_max + x_pad
    y0, y1 = y_min - y_pad, y_max + y_pad

    # 四象限色块
    ax.add_patch(
        plt.Rectangle((x0, y_med), x_med - x0, y1 - y_med, color="#dbeafe", alpha=0.45, zorder=0)
    )  # 左上
    ax.add_patch(
        plt.Rectangle((x_med, y_med), x1 - x_med, y1 - y_med, color="#fee2e2", alpha=0.45, zorder=0)
    )  # 右上
    ax.add_patch(
        plt.Rectangle((x0, y0), x_med - x0, y_med - y0, color="#e5e7eb", alpha=0.55, zorder=0)
    )  # 左下
    ax.add_patch(
        plt.Rectangle((x_med, y0), x1 - x_med, y_med - y0, color="#fef3c7", alpha=0.45, zorder=0)
    )  # 右下

    ax.scatter(
        x,
        y,
        s=sizes,
        alpha=0.65,
        edgecolors="white",
        linewidths=1.0,
        zorder=2,
    )

    ax.axvline(x_med, linestyle="--", linewidth=1.6, color="#2563eb", zorder=1)
    ax.axhline(y_med, linestyle="--", linewidth=1.6, color="#2563eb", zorder=1)

    # 只给标签集合打标签
    label_names = set(label_df[group_name_col].astype(str).tolist())
    label_points = work[work[group_name_col].astype(str).isin(label_names)].copy()

    for _, row in label_points.iterrows():
        ax.annotate(
            str(row[group_name_col]),
            (row[burden_col], row[intensity_col]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
            zorder=3,
        )

    ax.text(x0, y1, "Low burden\nHigh intensity", ha="left", va="top", fontsize=10, weight="bold")
    ax.text(x1, y1, "High burden\nHigh intensity", ha="right", va="top", fontsize=10, weight="bold")
    ax.text(x0, y0, "Low burden\nLow intensity", ha="left", va="bottom", fontsize=10, weight="bold")
    ax.text(
        x1,
        y0,
        "High burden\nLow intensity",
        ha="right",
        va="bottom",
        fontsize=10,
        weight="bold",
    )

    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)

    ax.set_title("Quadrant Bubble Chart of Group-Level Risk")
    ax.set_xlabel("Average Complaints per Officer")
    ax.set_ylabel("Substantiated Complaints per 100 Complaints")

    return fig, ax, work, label_df, x_med, y_med


st.sidebar.header("Controls")

max_rows_ui = st.sidebar.number_input(
    "Max rows to load (0 = all)",
    min_value=0,
    value=0,
    step=5000,
)
max_rows = None if int(max_rows_ui) == 0 else int(max_rows_ui)

group_col = st.sidebar.selectbox(
    "Group by",
    ["Current Command", "Current Rank"],
    index=0,
)

min_officers = st.sidebar.slider(
    "Minimum officers per group",
    5,
    300,
    20,
    step=5,
)

top_n = st.sidebar.slider(
    "Show top N groups",
    5,
    20,
    10,
    step=1,
)

bubble_scope = st.sidebar.selectbox(
    "Bubble chart scope",
    ["Top union only", "All groups"],
    index=0,
)

bubble_size_mode = st.sidebar.selectbox(
    "Bubble size mode",
    ["Group size", "Fixed"],
    index=0,
)

bubble_size_scale = st.sidebar.slider(
    "Bubble size scale",
    min_value=0.4,
    max_value=2.0,
    value=1.0,
    step=0.1,
)

if st.sidebar.button("Clear cache"):
    st.cache_data.clear()
    st.sidebar.success("Cache cleared. Rerun.")

df = load_snapshot(max_rows=max_rows)

if df.empty:
    st.error("No data returned from BigQuery.")
    st.stop()

st.markdown(
    "We summarize group-level risk in three views:\n"
    "- **Complaint burden** = average complaints per officer in the group\n"
    "- **Substantiation intensity** = substantiated complaints per 100 complaints\n"
    "- **Quadrant bubble chart** = a compact overview of where groups fall on both dimensions\n"
    "\n"
    "The ranked charts make it easier to identify the highest-risk groups, while the bubble chart "
    "shows the broader relationship between burden and intensity."
)

df_for_groups = df.copy()
if group_col in df_for_groups.columns:
    df_for_groups = df_for_groups[df_for_groups[group_col] != "Unknown"]

group_stats = cached_group_stats(
    df_for_groups,
    group_col=group_col,
    min_officers=int(min_officers),
)

if group_stats.table.empty:
    st.warning("No groups remain after filtering. Lower 'Minimum officers per group'.")
    st.stop()

stats_df = group_stats.table.copy()

group_name_col = first_existing_col(
    stats_df,
    [group_col, "group", "Group", "group_name"],
)

burden_col = first_existing_col(
    stats_df,
    ["avg_complaints_per_officer", "avg_complaints", "complaints_per_officer"],
)

intensity_col = first_existing_col(
    stats_df,
    [
        "substantiated_per_100",
        "substantiated_per_100_complaints",
        "substantiated_rate_per_100",
        "subst_rate_per_100",
        "substantiated_per_100_total_complaints",
    ],
)

size_col = None
for c in ["n_officers", "officer_count", "num_officers", "count", "n"]:
    if c in stats_df.columns:
        size_col = c
        break

st.markdown("### Figure A. Quadrant bubble chart of group-level risk")
st.markdown(
    "This chart provides a high-level view of group risk across two dimensions. "
    "You can switch between a focused top-group view and a full-group view in the sidebar."
)

fig_bubble, ax_bubble, bubble_df, label_df, x_med, y_med = plot_quadrant_bubble_chart(
    stats_df,
    group_name_col=group_name_col,
    burden_col=burden_col,
    intensity_col=intensity_col,
    size_col=size_col,
    top_n=top_n,
    scope=bubble_scope,
    size_mode=bubble_size_mode,
    size_scale=bubble_size_scale,
)

st.pyplot(fig_bubble, clear_figure=True)

st.caption(
    f"Bubble chart scope = {bubble_scope}; bubble size mode = {bubble_size_mode}; "
    f"vertical line = median burden ({x_med:.2f}); "
    f"horizontal line = median intensity ({y_med:.2f})."
)

st.markdown("### Figure B. Groups ranked by complaint burden")
st.markdown(
    "This chart ranks groups by **average complaints per officer**. "
    "Higher values indicate a heavier complaint burden within the group."
)

top_burden = (
    stats_df[[group_name_col, burden_col]]
    .sort_values(burden_col, ascending=False)
    .head(top_n)
    .sort_values(burden_col, ascending=True)
)

fig_burden = px.bar(
    top_burden,
    x=burden_col,
    y=group_name_col,
    orientation="h",
    text=burden_col,
    title=f"Top {top_n} Groups by Average Complaints per Officer",
)

fig_burden.update_traces(texttemplate="%{text:.2f}", textposition="outside")
fig_burden.update_layout(
    xaxis_title="Average Complaints per Officer",
    yaxis_title=group_col,
    showlegend=False,
)

st.plotly_chart(fig_burden, use_container_width=True)

st.markdown("### Figure C. Groups ranked by substantiation intensity")
st.markdown(
    "This chart ranks groups by **substantiated complaints per 100 complaints**. "
    "Higher values indicate that a larger share of complaints in that group are substantiated."
)

top_intensity = (
    stats_df[[group_name_col, intensity_col]]
    .sort_values(intensity_col, ascending=False)
    .head(top_n)
    .sort_values(intensity_col, ascending=True)
)

fig_intensity = px.bar(
    top_intensity,
    x=intensity_col,
    y=group_name_col,
    orientation="h",
    text=intensity_col,
    title=f"Top {top_n} Groups by Substantiated Complaints per 100 Complaints",
)

fig_intensity.update_traces(texttemplate="%{text:.2f}", textposition="outside")
fig_intensity.update_layout(
    xaxis_title="Substantiated per 100 Complaints",
    yaxis_title=group_col,
    showlegend=False,
)

st.plotly_chart(fig_intensity, use_container_width=True)

st.markdown("### Group summary table")
show_cols = [
    c
    for c in [group_name_col, burden_col, intensity_col] + ([size_col] if size_col else [])
    if c is not None and c in stats_df.columns
]
st.dataframe(
    stats_df[show_cols].sort_values(burden_col, ascending=False),
    use_container_width=True,
)

st.download_button(
    "Download group stats as CSV",
    data=stats_df.to_csv(index=False).encode("utf-8"),
    file_name=f"rq2_group_stats_{group_col.replace(' ', '_').lower()}.csv",
    mime="text/csv",
)

st.markdown("### Key takeaway")
top_burden_name = top_burden.iloc[-1][group_name_col]
top_burden_value = top_burden.iloc[-1][burden_col]
top_intensity_name = top_intensity.iloc[-1][group_name_col]
top_intensity_value = top_intensity.iloc[-1][intensity_col]

st.write(
    f"When grouped by **{group_col}**, the highest complaint burden appears in "
    f"**{top_burden_name}** ({top_burden_value:.2f} complaints per officer), while the "
    f"highest substantiation intensity appears in **{top_intensity_name}** "
    f"({top_intensity_value:.2f} substantiated complaints per 100 complaints)."
)

elapsed = time.time() - start_time
st.caption(f"Page loaded in {elapsed:.2f} seconds")

if st.button("Back to Homepage"):
    st.switch_page("main_page.py")
