import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.macro import productivity_functions as pf
import generalities.macro_generalities.productivity as pr
from generalities.macro_generalities.dictionaries import presidents
from generalities.function import (load_csv, BASE_DIR, highlight_selectbox,
                                   get_valid_presidents, president_multiselect)

PRODUCTIVITY_LABORAL_BASE = str(BASE_DIR / "data/dane/productivity/laboral") + "/"
DEFAULT_STEM = "por_persona_empleada"


def render_productivity(prod_df: pd.DataFrame) -> None:
    top_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    file_label = st.selectbox("Table:", list(pr.PRODUCTIVITY_FILES.keys()))
    stem = pr.PRODUCTIVITY_FILES[file_label]
    terms = pr.PRODUCTIVITY_TERMS[stem]

    df = prod_df if stem == DEFAULT_STEM else load_csv(f"{PRODUCTIVITY_LABORAL_BASE}{stem}.csv")
    years = sorted(df["año"].unique())

    concept_labels = st.sidebar.multiselect(
        "Concepts:", list(terms.keys()), default=[list(terms.keys())[0]])
    if not concept_labels:
        concept_labels = [list(terms.keys())[0]]

    cur_years = st.sidebar.multiselect("Year:", years, key="prod_years")

    with top_placeholder.container():
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])

    valid_presidents = get_valid_presidents(years)
    with president_placeholder.container():
        selected_presidents = president_multiselect(valid_presidents, key="prod_presidents")

    year_set = set(cur_years)
    for name in selected_presidents:
        year_set.update(set(presidents[name]) & set(years))

    concept_cols = {label: terms[label] for label in concept_labels}
    series = pf.productivity_pivot(df, concept_cols, year_set)

    info = [f"Labor Productivity — {file_label}", "Year", "Value (pp / %)"]
    if len(year_set) == 1:
        info[0] = f"{info[0]} · {sorted(year_set)[0]}"

    highlight = highlight_selectbox(series)
    fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
    mc.render_chart(fig)
    st.caption("Source: DANE")
