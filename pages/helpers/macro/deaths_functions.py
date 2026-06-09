import pandas as pd
import streamlit as st
from generalities.macro_generalities.dictionaries import presidents
from generalities.function import find_key_by_value, load_csv, norm
from generalities.macro_generalities.deaths import GENDER_EN as DEATHS_GENDER_EN, AREA_EN, AGE_EN as DEATHS_AGE_EN, CAUSE_EN


def _cause_label(causa: pd.Series) -> pd.Series:
    """Strip the leading NNN code, then map to English (accent-variants collapse to one)."""
    stripped = causa.astype(str).str.replace(r"^\d+\s+", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    return stripped.map(lambda s: CAUSE_EN.get(norm(s), s))

@st.cache_data
def deaths_dept_prepared(path) -> pd.DataFrame:
    df = load_csv(path)
    df = df[~df["departamento"].str.strip().str.lower().eq("total nacional")].copy()
    df["Name"] = df["departamento"].str.split(n=1).str[1]
    df["cause"] = _cause_label(df["causa"])
    return df

def _dept_filter(dept_df: pd.DataFrame, years: list, president: str, dept_name: str = None) -> pd.DataFrame:
    df = dept_df
    if dept_name and dept_name != "All":
        df = df[df["Name"] == dept_name]
    if president:
        df = df[df["Fecha"].isin(presidents[president])]
    elif years:
        df = df[df["Fecha"].isin(years)]
    return df

def deaths_national_series(total_df: pd.DataFrame) -> pd.Series:
    s = total_df.set_index("Fecha")["total"].astype(float)
    s.index = s.index.astype(int)
    return s

def deaths_gender_pivot(total_df: pd.DataFrame) -> tuple:
    cols = {f"Total_{es}": en for es, en in DEATHS_GENDER_EN.items()}
    df = total_df.set_index("Fecha")[list(cols)].astype(int).rename(columns=cols)
    df.index = df.index.astype(int)
    df.index.name = "Year"
    return df, ["Deaths by gender", "Year", "Deaths"]

def deaths_gender_cause_pivot(dept_df: pd.DataFrame, cause: str) -> tuple:
    df = dept_df[dept_df["cause"] == cause]
    cols = {f"Total_{es}": en for es, en in DEATHS_GENDER_EN.items()}
    out = df.groupby("Fecha")[list(cols)].sum().astype(int).rename(columns=cols)
    out.index = out.index.astype(int)
    out.index.name = "Year"
    return out, [f"Deaths by gender — {cause}", "Year", "Deaths"]

def deaths_area_pivot(area_df: pd.DataFrame, age_label: str = "All ages", gender: str = "Total", area: str = "All areas") -> tuple:
    df = area_df.copy()
    df["age"] = df["grupo_edad"].map(DEATHS_AGE_EN).fillna(df["grupo_edad"])
    title = "Deaths by area"
    if age_label and age_label != "All ages":
        df = df[df["age"] == age_label]
        title += f" — age {age_label}"
    gender_es = find_key_by_value(DEATHS_GENDER_EN, gender)  # None when "Total"
    items = AREA_EN.items() if area == "All areas" else [(find_key_by_value(AREA_EN, area), area)]
    out = pd.DataFrame(index=sorted(df["Fecha"].unique()))
    for es, en in items:
        cols = [f"{es}_{g}" for g in DEATHS_GENDER_EN] if gender == "Total" else [f"{es}_{gender_es}"]
        out[en] = df.groupby("Fecha")[cols].sum().sum(axis=1).astype(int)
    out.index = out.index.astype(int)
    out.index.name = "Year"
    if area != "All areas":
        title += f" — {area}"
    if gender != "Total":
        title += f" — {gender}"
    return out, [title, "Year", "Deaths"]

def deaths_age_pivot(area_df: pd.DataFrame, gender: str = "Total", area: str = "Total") -> tuple:
    df = area_df.copy()
    df["age"] = df["grupo_edad"].map(DEATHS_AGE_EN).fillna(df["grupo_edad"])

    area_es = find_key_by_value(AREA_EN, area)  # None when area == "Total"
    gender_es = find_key_by_value(DEATHS_GENDER_EN, gender)  # None when gender == "Total"

    if area == "Total" and gender == "Total":
        df["val"] = df["total"]
    elif area == "Total":
        df["val"] = df[f"Total_{gender_es}"]
    elif gender == "Total":
        df["val"] = df[[f"{area_es}_{g}" for g in DEATHS_GENDER_EN]].sum(axis=1)
    else:
        df["val"] = df[f"{area_es}_{gender_es}"]

    pivot = df.pivot_table(index="Fecha", columns="age", values="val", aggfunc="sum").astype(int)
    order = list(dict.fromkeys(DEATHS_AGE_EN.values()))  # dedupe typo collisions, keep order
    pivot = pivot[[c for c in order if c in pivot.columns]]
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"

    parts = [p for p in (None if area == "Total" else area, None if gender == "Total" else gender) if p]
    title = "Deaths by age group" + (f" — {', '.join(parts)}" if parts else "")
    return pivot, [title, "Year", "Deaths"]

def deaths_age_cause_pivot(dept_df: pd.DataFrame, gender: str = "Total", cause: str = "All causes") -> tuple:
    df = dept_df if cause == "All causes" else dept_df[dept_df["cause"] == cause]
    genders = list(DEATHS_GENDER_EN) if gender == "Total" else [find_key_by_value(DEATHS_GENDER_EN, gender)]
    order = list(dict.fromkeys(DEATHS_AGE_EN.values()))
    out = pd.DataFrame(index=sorted(df["Fecha"].unique()))
    for en in order:
        age_keys = [k for k, v in DEATHS_AGE_EN.items() if v == en]
        cols = [f"{a}_{g}" for a in age_keys for g in genders if f"{a}_{g}" in df.columns]
        if cols:
            out[en] = df.groupby("Fecha")[cols].sum().sum(axis=1).astype(int)
    out.index = out.index.astype(int)
    out.index.name = "Year"
    title = "Deaths by age group" + (f" — {gender}" if gender != "Total" else "")
    if cause != "All causes":
        title += f" ({cause})"
    return out, [title, "Year", "Deaths"]

def deaths_age_gender_value(df: pd.DataFrame, gender: str, age_label: str) -> pd.Series:
    """Series of deaths for a (gender, age) combo from dept×cause frames (cols: total, Total_<gender>, <age>_<gender>)."""
    genders = list(DEATHS_GENDER_EN) if gender == "Total" else [find_key_by_value(DEATHS_GENDER_EN, gender)]
    if not age_label or age_label == "All ages":
        return df["total"] if gender == "Total" else df[f"Total_{genders[0]}"]
    age_keys = [k for k, v in DEATHS_AGE_EN.items() if v == age_label]
    cols = [f"{a}_{g}" for a in age_keys for g in genders if f"{a}_{g}" in df.columns]
    return df[cols].sum(axis=1)

def deaths_top_causes(dept_df: pd.DataFrame, years: list, dept_name: str, president: str, value_col: str = "total") -> pd.Series:
    df = _dept_filter(dept_df, years, president, dept_name)
    return df.groupby("cause")[value_col].sum().astype(int).nlargest(5)

def deaths_cause_pivot(dept_df: pd.DataFrame, selected_causes: list, years: list, president: str, value_col: str = "total", dept_name: str = "All") -> pd.DataFrame:
    df = _dept_filter(dept_df, years, president, dept_name)
    df = df[df["cause"].isin(selected_causes)]
    pivot = (
        df.pivot_table(index="Fecha", columns="cause", values=value_col, aggfunc="sum")
        .fillna(0)
        .astype(int)
    )
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"
    return pivot

def deaths_cause_names(dept_df: pd.DataFrame) -> list:
    return sorted(dept_df["cause"].unique())
