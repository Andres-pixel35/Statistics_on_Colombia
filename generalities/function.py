import json
from pathlib import Path
from datetime import datetime
from typing import NamedTuple
import pandas as pd
import streamlit as st
import re
import unicodedata
from generalities.dictionaries import presidents, months

BASE_DIR = Path(__file__).resolve().parent.parent

PREV_YEAR = datetime.now().year - 1  # last observed year before projections

def get_valid_presidents(tmp_years: dict) -> list:
    return [
        name for name, pres_years in presidents.items()
        if not set(pres_years).isdisjoint(tmp_years)
    ]

def find_key_by_value(d: dict, value: str):
    return next((k for k, v in d.items() if v == value), None)

def cap(this, others):
    """Restrict peer multiselects to 1: if `this` dim grows to >=2 while another peer is already
    multi, keep only its newest pick. Editable + remembers the other dims (no reset, no lock)."""
    if len(st.session_state[this]) >= 2 and any(
            len(st.session_state.get(o, [])) >= 2 for o in others):
        st.session_state[this] = st.session_state[this][-1:]

def cap_one(keys):
    """Trim each named multiselect in session_state to its newest pick (cap to 1)."""
    for k in keys:
        if len(st.session_state.get(k, [])) >= 2:
            st.session_state[k] = st.session_state[k][-1:]

def highlight_selectbox(df, display_names=None, label="Highlight variable:"):
    if not isinstance(df, pd.DataFrame) or df.empty or len(df.columns) <= 1:
        return None
    names = display_names if display_names is not None else [str(c) for c in df.columns]
    with st.sidebar:
        choice = st.selectbox(label, ["—"] + names)
    return None if choice == "—" else choice

def cap_series(data: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame) and data.shape[1] > limit:
        st.session_state["chart_warning"] = f"Showing first {limit} of {data.shape[1]} series."
        return data.iloc[:, :limit]
    return data

def show_all_years(df: pd.DataFrame|pd.Series, president, return_flag=False) -> pd.DataFrame | pd.Series:
    with st.sidebar:
        show_all = st.checkbox("Show all years", value=False)

    if not show_all and not president:
        df = df[df.index >= 2000]

    return (df, show_all) if return_flag else df

@st.cache_data
def load_csv(path: str | Path, dtype=None) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", dtype=dtype)

@st.cache_data
def load_geojson(path: str | Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def to_datatime(df: pd.DataFrame, dayfirst: bool) -> pd.DataFrame | pd.Series:
    df_local = df.copy()
    df_local["Fecha"] = pd.to_datetime(df_local["Fecha"], dayfirst=dayfirst)
    df_local = df_local.set_index("Fecha").sort_index(ascending=True)

    return df_local

def president_multiselect(valid_presidents: list, disabled: bool = False, key=None) -> list:
    """Replacement for the single-president selectbox. 2+ selected = comparison mode."""
    return st.multiselect("Presidents:", valid_presidents, disabled=disabled, key=key)

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

def norm(label: str) -> str:
    """Accent/case/space-insensitive key so 'Úlcera' and 'Ulcera' collapse to one cause."""
    text = unicodedata.normalize("NFKD", str(label)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text).strip().lower()

class SeriesSpec(NamedTuple):
    value_col: str  # e.g. "trm" or "Tasa (%)"
    label: str       # e.g. "Exchange Rate" or "Monetary Policy Rate"

def series_year_axis(df: pd.DataFrame, spec: SeriesSpec, month_nums: list) -> pd.DataFrame:
    """x = years. Empty month_nums -> annual-average single column; else one column per month."""
    s = df[spec.value_col].dropna()
    if not month_nums:
        return s.groupby(s.index.year).mean().to_frame(name=spec.label)

    cols = {}
    for m in month_nums:
        sm = s[s.index.month == m]
        cols[months[m]] = sm.groupby(sm.index.year).mean()
    return pd.DataFrame(cols)

def series_month_axis(df: pd.DataFrame, spec: SeriesSpec, years: list) -> pd.DataFrame:
    """x = months (Jan-Dec). One column per year, values = that year's monthly average."""
    s = df[spec.value_col].dropna()
    cols = {}
    for y in years:
        sy = s[s.index.year == y]
        cols[str(y)] = sy.groupby(sy.index.month).mean()
    table = pd.DataFrame(cols)
    table.index = [months[m] for m in table.index]
    return table
