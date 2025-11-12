"""Utility functions for the Streamlit dashboard.

Functions here read CSVs from the repository `data/` folder, add a `country`
column inferred from filenames, and provide simple helpers used by the UI.
"""
from pathlib import Path
import pandas as pd
import re
from typing import List, Dict


def _project_root() -> Path:
    """Return the project root (parent of the `app` folder)."""
    return Path(__file__).resolve().parents[1]


def list_data_files(data_dir: str = "data") -> List[Path]:
    """Return a list of CSV file Paths in the repository data directory.

    The function is robust if the directory doesn't exist — it returns an
    empty list.
    """
    root = _project_root()
    data_path = root / data_dir
    if not data_path.exists():
        return []
    return [p for p in data_path.iterdir() if p.suffix.lower() == ".csv"]


def extract_country_from_filename(path: Path) -> str:
    """Infer a country name from a filename like 'benin-malanville.csv'.

    This is a heuristic: take the first alpha-only token at the start of the
    basename and capitalise it.
    """
    name = path.name
    m = re.match(r"([A-Za-z]+)", name)
    if m:
        return m.group(1).capitalize()
    return name


def get_files_by_country(data_dir: str = "data") -> Dict[str, List[Path]]:
    """Return mapping country -> list of file paths for that country."""
    files = list_data_files(data_dir)
    mapping = {}
    for f in files:
        country = extract_country_from_filename(f)
        mapping.setdefault(country, []).append(f)
    return mapping


def load_csv_file(path: Path) -> pd.DataFrame:
    """Load a CSV and add metadata columns: __source_file and country.

    Returns an empty DataFrame on failure.
    """
    try:
        df = pd.read_csv(path)
    except Exception:
        return pd.DataFrame()
    # Normalize column names
    df = df.rename(columns=lambda x: x.strip())
    df["__source_file"] = path.name
    df["country"] = extract_country_from_filename(path)
    return df


def load_data_for_countries(countries: List[str], data_dir: str = "data") -> pd.DataFrame:
    """Load and concatenate CSVs for the provided countries.

    If a country has multiple files, all are concatenated. Returns an empty
    DataFrame if nothing could be loaded.
    """
    files_by_country = get_files_by_country(data_dir)
    dfs = []
    for c in countries:
        for p in files_by_country.get(c, []):
            df = load_csv_file(p)
            if not df.empty:
                dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def infer_numeric_columns(df: pd.DataFrame) -> List[str]:
    """Return a list of numeric column names in the DataFrame."""
    if df is None or df.empty:
        return []
    return df.select_dtypes(include=["number"]).columns.tolist()
