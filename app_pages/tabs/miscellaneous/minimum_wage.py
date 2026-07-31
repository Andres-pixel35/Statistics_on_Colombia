import streamlit as st
import pandas as pd
from app_pages.helpers import charts as mc
from app_pages.helpers.macro import productivity_functions as pf
from generalities.dictionaries import presidents
from generalities.i18n import t
from generalities.function import (highlight_selectbox, get_valid_presidents,
                                   president_multiselect, reshape_by_presidents,
                                   show_all_years, to_datatime, BASE_DIR, load_csv,
                                   SeriesSpec, series_year_axis)

CONCEPTS = {"Wage": "Salario", "Transportation Allowance": "Auxilio"}
SUM_LABEL = "Wage + Transportation Allowance"
CPI_PATH = BASE_DIR / "data/banco_republica/CPI/city/Total_Nacional.csv"
BASE_YEAR = 2000


def render_minimum_wage(df: pd.DataFrame, trm_df: pd.DataFrame) -> None:
    st.title(t("Miscellaneous"))
    local = df.rename(columns={"Fecha": "año"})
    years = sorted(local["año"].unique())

    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Line", "Bar"], format_func=t)
    cur_years = st.sidebar.multiselect(t("Year:"), years, key="wage_years")

    valid_presidents = get_valid_presidents(years)
    with st.sidebar:
        selected_presidents = president_multiselect(valid_presidents, key="wage_presidents")
    comparing = len(selected_presidents) >= 2

    col1, col2 = st.columns(2)
    with col1:
        method = st.selectbox(t("Method:"), ["Total", "Growth", "USD"], format_func=t)
    with col2:
        concept_label = st.selectbox(t("Concept:"), list(CONCEPTS.keys()) + [SUM_LABEL], format_func=t)

    show_real = st.sidebar.checkbox(t("Show Real Values"))

    year_set = set(cur_years)
    for name in selected_presidents:
        year_set.update(set(presidents[name]) & set(years))

    if not year_set and not comparing:
        capped = show_all_years(pd.DataFrame(index=years), president=False)
        year_set = set(capped.index)

    if concept_label == SUM_LABEL:
        full = local.set_index("año")[["Salario", "Auxilio"]].sum(axis=1).sort_index()
        full.index.name = "Year"
        label = SUM_LABEL
    else:
        full = pf.productivity_pivot(local, {concept_label: CONCEPTS[concept_label]})[concept_label]
        label = concept_label

    if show_real:
        cpi_annual = series_year_axis(to_datatime(load_csv(CPI_PATH), False), SeriesSpec("Índice ", "CPI"), [])["CPI"]
        full = full * (cpi_annual.loc[BASE_YEAR] / cpi_annual.reindex(full.index))
        label = t("{label} (Real)").format(label=t(label))

    if method == "Growth":
        full = round(full.pct_change() * 100, 2).dropna()
        label = t("{label} Growth").format(label=t(label))
        unit = "%"
    elif method == "USD":
        trm_year = series_year_axis(to_datatime(trm_df, False), SeriesSpec("trm", "Exchange Rate"), [])["Exchange Rate"]
        full = (full / trm_year).dropna()
        unit = "USD"
    else:
        unit = "COP"

    series = full.to_frame(name=label)
    if not comparing:
        series = series[series.index.isin(year_set)]

    info = [label, "Year", unit]
    if comparing:
        series, info = reshape_by_presidents(series, selected_presidents, info)
    elif len(year_set) == 1:
        info[0] = f"{info[0]} · {sorted(year_set)[0]}"

    if series.empty:
        st.warning(t("No data for selected filters."))
    elif method == "Growth" and not comparing and len(year_set) == 1:
        reference = full.median()
        fig = mc.indicator(series, full, reference, [info[0], ".2f", "%", " vs Median"])
        mc.render_chart(fig)
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
    if method == "USD":
        st.caption(t("USD values use each year's average official exchange rate (TRM)."))
    if show_real:
        st.caption(t("Real values use {year} as the base year.").format(year=BASE_YEAR))
    st.caption(t("Source: Banco de la República"))
