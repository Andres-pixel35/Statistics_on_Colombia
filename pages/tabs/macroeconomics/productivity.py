import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.macro import productivity_functions as pf
import generalities.macro_generalities.productivity as pr
from generalities.macro_generalities.dictionaries import presidents
from generalities.function import (load_csv, BASE_DIR, highlight_selectbox,
                                   get_valid_presidents, president_multiselect)

PRODUCTIVITY_BASE_DIR = str(BASE_DIR / "data/dane/productivity") + "/"
DEFAULT_STEM = "por_persona_empleada"


def render_productivity(prod_df: pd.DataFrame) -> None:
    top_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    file_label = st.selectbox("Table:", list(pr.PRODUCTIVITY_FILES.keys()))
    stem = pr.PRODUCTIVITY_FILES[file_label]
    terms = pr.PRODUCTIVITY_TERMS[stem]

    df = prod_df if stem == DEFAULT_STEM else load_csv(
        f"{PRODUCTIVITY_BASE_DIR}{pr.PRODUCTIVITY_BASE[stem]}/{stem}.csv")
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

    main_label = list(terms.keys())[0]
    units = {"%" if terms[label].rstrip().endswith("(%)") else "pp" for label in concept_labels}
    if units == {"%"}:
        value_label, unit_caption = "Value (%)", None
    elif units == {"pp"}:
        value_label = "Value (pp)"
        unit_caption = (f"Values in pp represent percentage-point contributions to {main_label}, "
                         "which is measured in %.")
    else:
        value_label = "Value (pp / %)"
        unit_caption = (f"{main_label} is in % (headline measure); "
                         "other concepts are in pp — their contribution to it.")

    info = [f"Labor Productivity — {file_label}", "Year", value_label]
    if len(year_set) == 1:
        info[0] = f"{info[0]} · {sorted(year_set)[0]}"

    highlight = highlight_selectbox(series)
    fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
    mc.render_chart(fig)
    if unit_caption:
        st.caption(unit_caption)
    st.caption("Source: DANE")
