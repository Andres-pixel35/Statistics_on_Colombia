import pandas as pd
from generalities.function import find_key_by_value
from generalities.demography_generalities.births import GENDER_EN, AGE_EN, EDU_EN


def births_national_series(total_df: pd.DataFrame) -> pd.Series:
    s = total_df.set_index("year")["total_nacional"].astype(float)
    s.index = s.index.astype(int)
    return s

def births_gender_pivot(total_df: pd.DataFrame) -> tuple:
    df = total_df.set_index("year")[["hombres", "mujeres"]].astype(int).rename(columns=GENDER_EN)
    df.index = df.index.astype(int)
    df.index.name = "Year"
    return df, ["Births by gender", "Year", "Births"]

def births_gender_age_pivot(age_df: pd.DataFrame, age_label: str) -> tuple:
    es = find_key_by_value(AGE_EN, age_label) or age_label
    df = age_df[age_df["grupo_edad"] == es].set_index("year")[["hombres", "mujeres"]]
    df = df.astype(int).rename(columns=GENDER_EN)
    df.index = df.index.astype(int)
    df.index.name = "Year"
    return df, [f"Births by gender — mothers {age_label}", "Year", "Births"]

def births_age_pivot(age_df: pd.DataFrame, gender: str = "Total") -> tuple:
    col = "total" if gender == "Total" else find_key_by_value(GENDER_EN, gender)
    df = age_df.copy()
    df["age"] = df["grupo_edad"].map(AGE_EN).fillna(df["grupo_edad"])
    pivot = df.pivot_table(index="year", columns="age", values=col, aggfunc="sum").astype(int)
    order = [v for v in AGE_EN.values() if v in pivot.columns]
    pivot = pivot[order]
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"
    title = "Births by mother's age group" + ("" if gender == "Total" else f" ({gender})")
    return pivot, [title, "Year", "Births"]

def births_education_pivot(edu_df: pd.DataFrame, age_label: str | None) -> tuple:
    df = edu_df.copy()
    edu_cols = [c for c in EDU_EN if c in df.columns]

    title = "Births by mother's education level"
    if age_label and age_label != "All ages":
        es = find_key_by_value(AGE_EN, age_label) or age_label
        df = df[df["grupo_edad"] == es]
        title += f" — mothers {age_label}"

    g = df.groupby("year")[edu_cols].sum().astype(int)
    g.columns = [EDU_EN[c] for c in g.columns]
    g.index = g.index.astype(int)
    g.index.name = "Year"
    return g, [title, "Year", "Births"]

def births_department_data(dept_df: pd.DataFrame, years: list, metric_col: str) -> pd.DataFrame:
    df = dept_df.copy()
    if years:
        df = df[df["year"].isin(years)]
    grouped = df.groupby("departamento")[metric_col].sum().reset_index()
    grouped["Code"] = grouped["departamento"].str.split(n=1).str[0]
    grouped["Name"] = grouped["departamento"].str.split(n=1).str[1]
    return grouped

def births_geo_trend(df: pd.DataFrame, entity_col: str, selected: list, years: list, value_col: str = "total") -> pd.DataFrame:
    d = df.copy()
    d["Name"] = d[entity_col].str.split(n=1).str[1]
    if years:
        d = d[d["year"].isin(years)]
    if selected:
        d = d[d["Name"].isin(selected)]
    pivot = (
        d.pivot_table(index="year", columns="Name", values=value_col, aggfunc="sum")
        .fillna(0)
        .astype(int)
    )
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"
    return pivot
