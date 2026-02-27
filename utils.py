# utils.py
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# =========================
# Core math helpers
# =========================


def _to_1d_nonneg_array(values: Iterable[float]) -> np.ndarray:
    arr = np.asarray(list(values), dtype=float).reshape(-1)
    if arr.size == 0:
        raise ValueError("Empty input.")
    if np.any(~np.isfinite(arr)):
        raise ValueError("Input contains non-finite values (NaN/Inf).")
    if np.any(arr < 0):
        raise ValueError("Input contains negative values; expected non-negative.")
    return arr


def lorenz_curve(values: Iterable[float]) -> tuple[np.ndarray, np.ndarray]:
    """
    Return Lorenz curve points (x, y) for non-negative values.

    x: cumulative share of population (0..1), length n+1
    y: cumulative share of value (0..1), length n+1

    If sum(values)==0 -> equality line.
    """
    v = _to_1d_nonneg_array(values)
    n = v.size
    v_sorted = np.sort(v)
    total = v_sorted.sum()
    x = np.linspace(0.0, 1.0, n + 1)

    if total == 0:
        return x, x.copy()

    cum = np.cumsum(v_sorted)
    y = np.concatenate([[0.0], cum / total])
    y[-1] = 1.0
    return x, y


def gini_coefficient(values: Iterable[float]) -> float:
    """
    Gini via Lorenz area:
      G = 1 - 2 * area_under_lorenz
    """
    x, y = lorenz_curve(values)
    # NumPy 2.x: np.trapz removed -> use trapezoid
    area = np.trapezoid(y, x) if hasattr(np, "trapezoid") else np.trapz(y, x)
    g = 1.0 - 2.0 * area
    return float(np.clip(g, 0.0, 1.0))


def top_share(values: Iterable[float], top_pct: float) -> float:
    """
    Share of total contributed by the top top_pct fraction (e.g. 0.01 for top 1%).
    """
    if not (0 < top_pct <= 1):
        raise ValueError("top_pct must be in (0, 1].")
    v = _to_1d_nonneg_array(values)
    total = v.sum()
    if total == 0:
        return 0.0
    k = int(np.ceil(v.size * top_pct))
    v_desc = np.sort(v)[::-1]
    return float(v_desc[:k].sum() / total)


# =========================
# RQ1: Plot Lorenz + Gini
# =========================


def plot_lorenz_curves(
    total_values: Iterable[float],
    subst_values: Iterable[float],
    *,
    title: str = "Lorenz Curves for CCRB Complaints (Officer Snapshot)",
    as_of_date: str | None = None,
    top_pcts: tuple[float, float] = (0.01, 0.05),
) -> tuple[plt.Figure, plt.Axes, dict[str, float]]:
    """
    Plot Lorenz curves for:
      - total complaints
      - substantiated complaints
    and return (fig, ax, summary_dict).
    """
    x1, y1 = lorenz_curve(total_values)
    x2, y2 = lorenz_curve(subst_values)

    g1 = gini_coefficient(total_values)
    g2 = gini_coefficient(subst_values)
    top1 = top_share(total_values, top_pcts[0])
    top5 = top_share(total_values, top_pcts[1])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x1, y1, label="Total Complaints")
    ax.plot(x2, y2, label="Total Substantiated Complaints")
    ax.plot([0, 1], [0, 1], linestyle="--", label="Equality line")

    ax.set_title(title)
    ax.set_xlabel("Cumulative share of officers (sorted low → high)")
    ax.set_ylabel("Cumulative share of complaints")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.legend(
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        borderaxespad=0.0,
    )
    fig.subplots_adjust(right=0.78)

    caption = (
        f"Gini(Total)={g1:.3f}   Gini(Subst)={g2:.3f}   "
        f"Top 1% share={top1:.1%}   Top 5% share={top5:.1%}"
    )
    if as_of_date:
        caption = f"As Of Date: {as_of_date}   " + caption
    fig.text(0.5, 0.005, caption, ha="center", va="bottom", fontsize=10)

    summary = {
        "gini_total": g1,
        "gini_subst": g2,
        "top_1pct_share_total": top1,
        "top_5pct_share_total": top5,
    }
    return fig, ax, summary


# =========================
# RQ2: Group stats + Risk Matrix
# =========================

REQUIRED_COLUMNS = {
    "Tax ID",
    "Total Complaints",
    "Total Substantiated Complaints",
}

ALLOWED_RQ2_GROUP_COLS = {"Current Command", "Current Rank"}


def _validate_df(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")


def _validate_group_col(df: pd.DataFrame, group_col: str) -> None:
    if group_col not in df.columns:
        raise ValueError(f"group_col='{group_col}' not found in DataFrame.")
    if group_col not in ALLOWED_RQ2_GROUP_COLS:
        allowed = sorted(ALLOWED_RQ2_GROUP_COLS)
        raise ValueError(f"group_col='{group_col}' not allowed. Choose one of {allowed}.")


@dataclass(frozen=True)
class GroupStats:
    table: pd.DataFrame
    group_col: str
    median_avg_complaints: float
    median_subst_per_100: float


def compute_group_stats(  # noqa: PLR0913
    df: pd.DataFrame,
    *,
    group_col: str,
    min_officers: int = 200,
    officer_id_col: str = "Tax ID",
    total_col: str = "Total Complaints",
    subst_col: str = "Total Substantiated Complaints",
) -> GroupStats:
    """
    Aggregate to group-level (Command or Rank) metrics for risk matrix.
    """
    _validate_df(df)
    _validate_group_col(df, group_col)

    tmp = df[[group_col, officer_id_col, total_col, subst_col]].copy()
    tmp[total_col] = pd.to_numeric(tmp[total_col], errors="coerce")
    tmp[subst_col] = pd.to_numeric(tmp[subst_col], errors="coerce")

    if tmp[total_col].isna().any() or tmp[subst_col].isna().any():
        raise ValueError("Total/Substantiated columns contain non-numeric values.")
    if (tmp[total_col] < 0).any() or (tmp[subst_col] < 0).any():
        raise ValueError("Total/Substantiated columns contain negatives.")

    grouped = (
        tmp.groupby(group_col, dropna=False)
        .agg(
            officers=(officer_id_col, "count"),
            total_complaints=(total_col, "sum"),
            total_substantiated=(subst_col, "sum"),
        )
        .reset_index()
    )

    grouped = grouped[grouped["officers"] >= int(min_officers)].copy()

    grouped["avg_complaints_per_officer"] = grouped["total_complaints"] / grouped["officers"]
    grouped["substantiated_per_100_complaints"] = np.where(
        grouped["total_complaints"] > 0,
        grouped["total_substantiated"] / grouped["total_complaints"] * 100.0,
        np.nan,
    )

    if len(grouped):
        med_x = float(np.nanmedian(grouped["avg_complaints_per_officer"]))
        med_y = float(np.nanmedian(grouped["substantiated_per_100_complaints"]))
    else:
        med_x = float("nan")
        med_y = float("nan")

    return GroupStats(
        table=grouped.sort_values("avg_complaints_per_officer").reset_index(drop=True),
        group_col=group_col,
        median_avg_complaints=med_x,
        median_subst_per_100=med_y,
    )


def plot_risk_matrix(
    group_stats: GroupStats,
    *,
    title: str = "Risk Matrix (Snapshot)",
    annotate_top_n: int = 0,
) -> tuple[plt.Figure, plt.Axes]:
    """
    Bubble scatter:
      x = avg complaints per officer
      y = substantiated per 100 complaints
      size = officers
    """
    tbl = group_stats.table.copy()
    if tbl.empty:
        raise ValueError("group_stats.table is empty (min_officers too high or no data).")

    sizes = tbl["officers"].to_numpy(dtype=float)
    bubble_sizes = 20.0 + 1800.0 * (sizes / sizes.max())

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(
        tbl["avg_complaints_per_officer"],
        tbl["substantiated_per_100_complaints"],
        s=bubble_sizes,
        alpha=0.6,
        edgecolors="none",
    )

    ax.axvline(group_stats.median_avg_complaints, linestyle="--")
    ax.axhline(group_stats.median_subst_per_100, linestyle="--")

    ax.set_title(title)
    ax.set_xlabel("Avg complaints per officer (Total complaints / #officers)")
    ax.set_ylabel("Substantiated per 100 complaints (Total substantiated / Total * 100)")

    subtitle = (
        f"Each dot = {group_stats.group_col} (filtered). "
        f"Vertical line = median avg complaints ({group_stats.median_avg_complaints:.2f}); "
        f"Horizontal line = median substantiated per 100 ({group_stats.median_subst_per_100:.2f})."
    )
    fig.text(0.5, 0.02, subtitle, ha="center", va="bottom", fontsize=9)

    if annotate_top_n and annotate_top_n > 0:
        top = tbl.nlargest(int(annotate_top_n), "avg_complaints_per_officer")
        for _, r in top.iterrows():
            ax.annotate(
                str(r[group_stats.group_col]),
                (r["avg_complaints_per_officer"], r["substantiated_per_100_complaints"]),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
            )

    return fig, ax
