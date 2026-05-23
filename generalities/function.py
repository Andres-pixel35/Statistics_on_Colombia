from pathlib import Path
import pandas as pd
import streamlit as st
from generalities.dictionaries import presidents

BASE_DIR = Path(__file__).resolve().parent.parent

def get_valid_presidents(tmp_years: dict) -> list:
    return [
        name for name, pres_years in presidents.items()
        if not set(pres_years).isdisjoint(tmp_years)
    ]

def find_key_by_value(d: dict, value: str):
    return next((k for k, v in d.items() if v == value), None)

def show_all_years(df: pd.DataFrame|pd.Series, president) -> pd.DataFrame | pd.Series:
    with st.sidebar:
        show_all = st.checkbox("Show all years", value=False)

    if not show_all and not president:
        df = df[df.index >= 2000]

    return df

@st.cache_data
def load_csv(path: str, dtype=None) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", dtype=dtype)

def to_datatime(df: pd.DataFrame, dayfirst: bool) -> pd.DataFrame | pd.Series:
    df_local = df.copy()
    df_local["Fecha"] = pd.to_datetime(df_local["Fecha"], dayfirst=dayfirst)
    df_local = df_local.set_index("Fecha").sort_index(ascending=True)

    return df_local

def president_multiselect(valid_presidents: list) -> list:
    """Replacement for the single-president selectbox. 2+ selected = comparison mode."""
    return st.multiselect("Presidents:", valid_presidents)

def reshape_by_presidents(df: pd.DataFrame, selected_presidents: list, info: list, col_labels: dict | None = None) -> tuple:
    """
    Reshape a year-indexed DataFrame for president comparison.

    The index becomes the relative term position ("Year 1", "Year 2", ...) and each
    (variable x president) pair becomes a column "{variable} ({president})". Returns the
    reshaped frame plus an updated info list (title names the presidents, x-axis label
    becomes "Term Year").
    """
    data = df.copy()
    data.index = (
        pd.Index(data.index).astype(str)
        .str.replace(r"[pr]", "", regex=True)
        .astype(int)
    )
    data = data[~data.index.duplicated(keep="first")]

    ordered = sorted(selected_presidents, key=lambda name: min(presidents[name]))
    max_len = max(len(presidents[name]) for name in ordered)

    columns = {}
    for name in ordered:
        term_years = sorted(presidents[name])
        for col in data.columns:
            var = col_labels.get(col, col) if col_labels else str(col)
            values = [
                data.at[year, col] if year in data.index else float("nan")
                for year in term_years
            ]
            values += [float("nan")] * (max_len - len(values))
            columns[f"{var} ({name})"] = values

    result = pd.DataFrame(columns, index=[f"Year {i}" for i in range(1, max_len + 1)])
    result.index.name = "Term Year"

    new_info = [f"{info[0]} — {' vs '.join(ordered)}", "Term Year", info[2], *info[3:]]
    return result, new_info
