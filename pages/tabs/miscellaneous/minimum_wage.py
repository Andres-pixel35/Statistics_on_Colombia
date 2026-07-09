import streamlit as st
import pandas as pd
from pages.helpers import charts as mc
from pages.helpers.macro import productivity_functions as pf
from generalities.macro_generalities.dictionaries import presidents
from generalities.function import (highlight_selectbox, get_valid_presidents,
                                   president_multiselect, reshape_by_presidents,
                                   show_all_years)

CONCEPTS = {"Wage": "Salario", "Transportation Allowance": "Auxilio"}
SUM_LABEL = "Wage + Transportation Allowance"


def render_minimum_wage(df: pd.DataFrame) -> None:
    st.title("Miscellaneous")
    local = df.rename(columns={"Fecha": "año"})
    years = sorted(local["año"].unique())

    chart_type = st.sidebar.selectbox("Chart Type:", ["Line", "Bar"])
    concept_label = st.sidebar.selectbox("Concept:", list(CONCEPTS.keys()))

    cur_years = st.sidebar.multiselect("Year:", years, key="wage_years")
    valid_presidents = get_valid_presidents(years)
    selected_presidents = president_multiselect(valid_presidents, key="wage_presidents")
    comparing = len(selected_presidents) >= 2

    year_set = set(cur_years)
    for name in selected_presidents:
        year_set.update(set(presidents[name]) & set(years))

    if not year_set and not comparing:
        capped = show_all_years(pd.DataFrame(index=years), president=False)
        year_set = set(capped.index)

    show_sum = st.sidebar.checkbox(f"Show sum ({SUM_LABEL})")
    if show_sum:
        total = local.set_index("año")[["Salario", "Auxilio"]].sum(axis=1)
        total.index.name = "Year"
        if not comparing:
            total = total[total.index.isin(year_set)]
        series = total.sort_index().to_frame(name=SUM_LABEL)
    else:
        series = pf.productivity_pivot(local, {concept_label: CONCEPTS[concept_label]},
                                        None if comparing else year_set)

    info = [SUM_LABEL if show_sum else concept_label, "Year", "COP"]
    if comparing:
        series, info = reshape_by_presidents(series, selected_presidents, info)
    elif len(year_set) == 1:
        info[0] = f"{info[0]} · {sorted(year_set)[0]}"

    if series.empty:
        st.warning("No data for selected filters.")
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
    st.caption("Source: Banco de la República")
