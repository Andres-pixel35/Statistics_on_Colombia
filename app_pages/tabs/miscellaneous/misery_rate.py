import streamlit as st
import pandas as pd
from app_pages.helpers import charts as mc
from app_pages.helpers.macro import job_market_functions as mf
from app_pages.helpers.miscellaneous import rates_functions as rf
from generalities.dictionaries import presidents
from generalities.i18n import t
from generalities.function import (to_datatime, highlight_selectbox, get_valid_presidents,
                                   president_multiselect, reshape_by_presidents, BASE_DIR)

UNIT = "pts"
DESEST_UNEMPLOYMENT_PATH = str(BASE_DIR / "data/dane/job_market/desestacionalizado/total.csv")


def render_misery_rate(cpi_df: pd.DataFrame, lending_df: pd.DataFrame, gdp_growth_by_year: pd.Series) -> None:
    st.title(t("Miscellaneous"))

    unemployment = mf.load_desestacionalizado_unemployment(DESEST_UNEMPLOYMENT_PATH)["Tasa de desempleo"]
    cpi = to_datatime(cpi_df, False)["Variación anual (%)"]
    lending = to_datatime(lending_df, True)["Tasa (%)"]
    full = rf.misery_index_annual(unemployment, cpi, lending, gdp_growth_by_year)["Misery Index"]

    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Line", "Bar", "Table"], format_func=t)
    years = sorted(full.index)
    cur_years = st.sidebar.multiselect(t("Year:"), years, key="misery_years")

    valid_presidents = get_valid_presidents(years)
    with st.sidebar:
        selected_presidents = president_multiselect(valid_presidents, key="misery_presidents")
    comparing = len(selected_presidents) >= 2

    year_set = set(cur_years)
    for name in selected_presidents:
        year_set.update(set(presidents[name]) & set(years))

    if not year_set and not comparing:
        year_set = set(years)

    series = full.to_frame(name="Misery Index")
    if not comparing:
        series = series[series.index.isin(year_set)]

    info = ["Misery Index", "Year", UNIT]
    if comparing:
        series, info = reshape_by_presidents(series, selected_presidents, info)
    elif len(year_set) == 1:
        info[0] = f"{info[0]} · {sorted(year_set)[0]}"

    if series.empty:
        st.warning(t("No data for selected filters."))
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)

    st.caption(t("Hanke Misery Index = 2 × Seasonally Adjusted Unemployment + Inflation + Lending Rate − Real GDP per-capita growth."))
    st.caption(t("Source: DANE, Banco de la República"))
