# precinct_helpers.py
import pandas as pd


def extract_precinct_from_command(
    officers_df: pd.DataFrame, command_col: str = "Current Command"
) -> pd.DataFrame:
    """
    Extract precinct number from strings like '113 PCT' or '010 PCT'.
    Adds an integer 'precinct' column and drops rows without a precinct.
    """
    out = officers_df.copy()

    out["precinct"] = (
        out[command_col]
        .astype(str)
        .str.strip()
        .str.extract(r"(\d+)\s*PCT", expand=False)
    )

    out["precinct"] = pd.to_numeric(out["precinct"], errors="coerce")
    out = out.dropna(subset=["precinct"])
    out["precinct"] = out["precinct"].astype(int)

    return out


def misconduct_by_precinct(officers_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns total complaints summed by precinct.
    Requires columns: 'Current Command', 'Total Complaints'
    """
    df = extract_precinct_from_command(officers_df, command_col="Current Command")

    # Ensure numeric complaints
    df["Total Complaints"] = pd.to_numeric(
        df["Total Complaints"], errors="coerce"
    ).fillna(0)

    out = (
        df.groupby("precinct")["Total Complaints"]
        .sum()
        .reset_index(name="allegation_count")
    )
    return out
