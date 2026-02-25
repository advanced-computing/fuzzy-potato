# precinct_helpers.py
import pandas as pd
import requests

DATASET1_BASE = "https://data.cityofnewyork.us/resource/2fir-qns4.json"


def load_dataset1(limit: int | None = None) -> pd.DataFrame:
    """
    Load Dataset 1 (officer misconduct data) from API.
    """
    params = {}
    if limit is not None:
        params["$limit"] = limit

    r = requests.get(DATASET1_BASE, params=params, timeout=60)
    r.raise_for_status()
    return pd.DataFrame(r.json())


def extract_precinct_from_command(
    officers_df: pd.DataFrame,
    command_col: str = "Current Command",
) -> pd.DataFrame:
    """
    Extract precinct number from strings like '113 PCT'.
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
    Auto-detect the command and complaints columns, then sum complaints by precinct.
    """
    df = officers_df.copy()

    # ---- auto-detect command column ----
    possible_command_cols = [
        "Current Command",
        "current_command",
        "current_command_at_end_of_year",
        "command",
        "command_name",
        "assignment",
        "precinct",
    ]
    command_col = next((c for c in possible_command_cols if c in df.columns), None)
    if command_col is None:
        raise KeyError(
            f"Could not find a command/precinct column. Available columns: {list(df.columns)[:30]}"
        )

    # ---- auto-detect complaints column ----
    possible_complaint_cols = [
        "Total Complaints",
        "total_complaints",
        "complaints",
        "complaint_count",
        "num_complaints",
    ]
    complaints_col = next((c for c in possible_complaint_cols if c in df.columns), None)
    if complaints_col is None:
        raise KeyError(
            f"Could not find a complaints column. Available columns: {list(df.columns)[:30]}"
        )

    # If the command column is already numeric precincts, keep it.
    # Otherwise extract precinct numbers from strings like "113 PCT".
    if pd.api.types.is_numeric_dtype(df[command_col]):
        df["precinct"] = pd.to_numeric(df[command_col], errors="coerce")
    else:
        df["precinct"] = (
            df[command_col]
            .astype(str)
            .str.strip()
            .str.extract(r"(\d+)\s*PCT", expand=False)
        )
        df["precinct"] = pd.to_numeric(df["precinct"], errors="coerce")

    df = df.dropna(subset=["precinct"])
    df["precinct"] = df["precinct"].astype(int)

    df[complaints_col] = pd.to_numeric(df[complaints_col], errors="coerce").fillna(0)

    return (
        df.groupby("precinct")[complaints_col]
        .sum()
        .reset_index(name="allegation_count")
    )
