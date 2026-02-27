# tests/test_precinct_helpers.py
import pandas as pd

from precinct_helpers import extract_precinct_from_command, misconduct_by_precinct


def test_extract_precinct_from_command_extracts_pct_and_drops_non_pct():
    officers = pd.DataFrame(
        {
            "Current Command": [
                "113 PCT",
                "010 PCT",
                "AVIATION",
                None,
                "PSA 2",
                "120 PCT",
            ],
            "Total Complaints": [2, 1, 5, 3, 4, 0],
        }
    )

    out = extract_precinct_from_command(officers)

    # Keep only rows with "<number> PCT"
    assert set(out["precinct"].tolist()) == {113, 10, 120}
    assert out["precinct"].dtype == int


def test_misconduct_by_precinct_sums_total_complaints_by_precinct():
    officers = pd.DataFrame(
        {
            "Current Command": ["113 PCT", "113 PCT", "010 PCT", "AVIATION"],
            "Total Complaints": [2, 3, 1, 99],
        }
    )

    agg = misconduct_by_precinct(officers)

    got = dict(zip(agg["precinct"], agg["allegation_count"], strict=True))
    # AVIATION should be excluded because it's not a precinct
    assert got == {113: 5, 10: 1}
