import pandas as pd
from generalities.macro_generalities.population import GENDER_AGG, GENDER_PREFIX, PYRAMID_GROUPS


def pop_value(df: pd.DataFrame, gender: str, age_label: str) -> pd.Series:
    """Population column for a (gender, age) selection, aligned to df rows."""
    if age_label == "All ages":
        col = GENDER_AGG[gender]
    else:
        col = f"{GENDER_PREFIX[gender]}_{age_label}"
    return df[col].astype(float)


def national_total_series(pop_df: pd.DataFrame, gender: str = "Total", age: str = "All ages", cap: int | None = None) -> pd.Series:
    """Year-indexed population series; optional `cap` keeps only years <= cap."""
    df = pop_df.copy()
    df["_val"] = pop_value(df, gender, age)
    s = df.set_index("AÑO")["_val"].sort_index()
    s.index = s.index.astype(int)
    if cap is not None:
        s = s[s.index <= cap]
    return s


def dept_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Zero-pad the DANE code (old-era rows store it unpadded) and pick one canonical
    name per code (collapses accent/spelling variants like Quindio/Quindío)."""
    d = df.copy()
    d["Code"] = d["DP"].astype(str).str.zfill(2)
    d["Name"] = d.groupby("Code")["DPNOM"].transform(lambda s: s.mode().iloc[0])
    return d


def dept_map_data(df: pd.DataFrame, year: int, gender: str, age: str) -> pd.DataFrame:
    """One value per department (Code/Name) for a single year, for the choropleth."""
    d = df[df["AÑO"] == year].copy()
    d["_val"] = pop_value(d, gender, age)
    return d.groupby(["Code", "Name"], as_index=False)["_val"].sum()


def geo_trend(df: pd.DataFrame, name_col: str, selected: list, gender: str, age: str) -> pd.DataFrame:
    """Year × entity pivot over the full year range (so projection is visible)."""
    d = df.copy()
    d["_val"] = pop_value(d, gender, age)
    if selected:
        d = d[d[name_col].isin(selected)]
    pivot = d.pivot_table(index="AÑO", columns=name_col, values="_val", aggfunc="sum").sort_index()
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"
    return pivot


def pyramid_rows(df_year: pd.DataFrame) -> tuple:
    """Sum single-year columns into 5-year buckets for men and women (one year's rows)."""
    men, women = {}, {}
    for label, lo, hi in PYRAMID_GROUPS:
        hcols = [f"Hombres_{n}" for n in range(lo, hi + 1) if f"Hombres_{n}" in df_year.columns]
        mcols = [f"Mujeres_{n}" for n in range(lo, hi + 1) if f"Mujeres_{n}" in df_year.columns]
        men[label] = float(df_year[hcols].to_numpy().sum())
        women[label] = float(df_year[mcols].to_numpy().sum())
    return pd.Series(men, name="Men"), pd.Series(women, name="Women")
