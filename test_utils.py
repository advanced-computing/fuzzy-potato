# test_utils.py
import matplotlib
matplotlib.use("Agg")  # headless backend for tests

import numpy as np
import pandas as pd
import pytest

from utils import (
    lorenz_curve,
    gini_coefficient,
    top_share,
    plot_lorenz_curves,
    compute_group_stats,
    plot_risk_matrix,
    GroupStats,
)


def test_lorenz_curve_all_zero_returns_equality():
    x, y = lorenz_curve([0, 0, 0, 0])
    assert np.allclose(x, y)
    assert x[0] == 0 and y[0] == 0
    assert x[-1] == 1 and y[-1] == 1


def test_gini_perfect_equality_is_zero():
    g = gini_coefficient([5, 5, 5, 5])
    assert abs(g - 0.0) < 1e-12


def test_gini_extreme_concentration_n4():
    g = gini_coefficient([0, 0, 0, 100])
    # For n=4 discrete case: (n-1)/n = 0.75
    assert abs(g - 0.75) < 1e-12


def test_top_share_simple_case():
    share = top_share([1, 2, 3, 4], 0.5)  # top2 => 7/10
    assert abs(share - 0.7) < 1e-12


def test_plot_lorenz_curves_runs_and_returns_summary():
    fig, ax, summary = plot_lorenz_curves([0, 1, 2, 3], [0, 0, 1, 1], as_of_date="2026-02-23")
    assert fig is not None and ax is not None
    assert "gini_total" in summary and "gini_subst" in summary
    assert 0 <= summary["gini_total"] <= 1
    assert 0 <= summary["gini_subst"] <= 1
    # cleanup
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_compute_group_stats_by_command():
    df = pd.DataFrame(
        {
            "Tax ID": [1, 2, 3, 4, 5, 6],
            "Current Command": ["A", "A", "A", "B", "B", "C"],
            "Current Rank": ["R1", "R1", "R2", "R2", "R2", "R3"],
            "Total Complaints": [2, 0, 1, 4, 0, 0],
            "Total Substantiated Complaints": [1, 0, 0, 1, 0, 0],
        }
    )

    stats = compute_group_stats(df, group_col="Current Command", min_officers=2)
    assert isinstance(stats, GroupStats)
    assert stats.group_col == "Current Command"
    assert set(stats.table["Current Command"]) == {"A", "B"}


def test_compute_group_stats_by_rank():
    df = pd.DataFrame(
        {
            "Tax ID": [1, 2, 3, 4, 5, 6],
            "Current Command": ["A", "A", "A", "B", "B", "C"],
            "Current Rank": ["R1", "R1", "R2", "R2", "R2", "R3"],
            "Total Complaints": [2, 0, 1, 4, 0, 0],
            "Total Substantiated Complaints": [1, 0, 0, 1, 0, 0],
        }
    )

    stats = compute_group_stats(df, group_col="Current Rank", min_officers=2)
    assert stats.group_col == "Current Rank"
    assert set(stats.table["Current Rank"]) == {"R1", "R2"}


def test_plot_risk_matrix_runs():
    df = pd.DataFrame(
        {
            "Tax ID": [1, 2, 3, 4],
            "Current Command": ["A", "A", "B", "B"],
            "Current Rank": ["R1", "R2", "R1", "R2"],
            "Total Complaints": [10, 0, 4, 1],
            "Total Substantiated Complaints": [2, 0, 1, 0],
        }
    )
    stats = compute_group_stats(df, group_col="Current Command", min_officers=1)
    fig, ax = plot_risk_matrix(stats, title="Test Risk Matrix")
    assert fig is not None and ax is not None
    import matplotlib.pyplot as plt
    plt.close(fig)


def test_compute_group_stats_invalid_group_col():
    df = pd.DataFrame(
        {
            "Tax ID": [1],
            "Current Command": ["A"],
            "Current Rank": ["R1"],
            "Total Complaints": [0],
            "Total Substantiated Complaints": [0],
        }
    )
    with pytest.raises(ValueError):
        compute_group_stats(df, group_col="Officer Race", min_officers=1)