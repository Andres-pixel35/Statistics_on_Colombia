import pandas as pd
import streamlit as st
from generalities.function import get_valid_presidents, president_multiselect
from generalities.macro_generalities.dictionaries import months
import generalities.macro_generalities.job_market as jm


def job_market_sidebar_filters(df: pd.DataFrame, placeholder, president_placeholder,
                               president_disabled: bool = False, president_key=None) -> tuple:
    """Render Chart Type + president multiselect for a year-indexed frame; returns (presidents, chart_type)."""
    years = df.index.unique().astype(int)

    with placeholder.container():
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])

    valid_presidents = get_valid_presidents(years)
    with president_placeholder.container():
        selected_presidents = president_multiselect(
            valid_presidents, disabled=president_disabled, key=president_key
        )

    return selected_presidents, chart_type


def unemployment_year_axis(df: pd.DataFrame, month_nums: list) -> pd.DataFrame:
    """x = years. Empty month_nums -> annual-average single column; else one column per month."""
    s = df["Tasa de desempleo"].dropna()
    if not month_nums:
        return s.groupby(s.index.year).mean().to_frame(name="Unemployment rate")

    cols = {}
    for m in month_nums:
        sm = s[s.index.month == m]
        sm.index = sm.index.year
        cols[months[m]] = sm
    return pd.DataFrame(cols)


def unemployment_month_axis(df: pd.DataFrame, years: list) -> pd.DataFrame:
    """x = months (Jan-Dec). One column per year, values that year's monthly rate."""
    s = df["Tasa de desempleo"].dropna()
    cols = {}
    for y in years:
        sy = s[s.index.year == y]
        sy.index = sy.index.month
        cols[str(y)] = sy
    table = pd.DataFrame(cols).reindex(range(1, 13))
    table.index = [months[m] for m in table.index]
    return table


def labor_force_pivot(df: pd.DataFrame, gender_sp: str, period_sp, concepts_sp: list) -> pd.DataFrame:
    """Year x Concepto pivot (people, values x1000). period_sp None -> mean across the 12 windows."""
    d = df[df["Perspectiva"] == gender_sp].replace({"Concepto": jm.CONCEPT_ALIASES})
    if period_sp is not None:
        d = d[d["Periodo"] == period_sp]

    table = d.pivot_table(index="Fecha", columns="Concepto", values="Valor", aggfunc="mean")
    return table.reindex(columns=concepts_sp) * 1000


def labor_force_period_axis(df: pd.DataFrame, gender_sp: str, years: list, concepts_sp: list) -> pd.DataFrame:
    """x = rolling 3-month windows. >=2 concepts -> single year, one col per concept;
    else one col per year for the single concept. Columns: Spanish concept (concept-priority)
    or str(year) (year-priority)."""
    d = df[df["Perspectiva"] == gender_sp].replace({"Concepto": jm.CONCEPT_ALIASES})
    cols = {}
    if len(concepts_sp) >= 2:                      # concept priority -> lock to 1 year
        dy = d[d["Fecha"] == years[0]]
        for c in concepts_sp:
            cols[c] = dy[dy["Concepto"] == c].set_index("Periodo")["Valor"]
    else:
        dc = d[d["Concepto"] == concepts_sp[0]]
        for y in years:
            cols[str(y)] = dc[dc["Fecha"] == y].set_index("Periodo")["Valor"]
    table = pd.DataFrame(cols).reindex(list(jm.PERIOD_EN)) * 1000
    table.index = [jm.PERIOD_EN[p] for p in table.index]
    return table
