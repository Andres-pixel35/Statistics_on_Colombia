import streamlit as st
import pandas as pd
from app_pages.helpers import charts as mc
from app_pages.helpers.macro import productivity_functions as pf
import generalities.macro_generalities.productivity as pr
from generalities.i18n import t
from generalities.dictionaries import presidents
from generalities.function import (load_csv, BASE_DIR, highlight_selectbox,
                                   get_valid_presidents, president_multiselect,
                                   reshape_by_presidents, find_key_by_value,
                                   cap as _cap, cap_one as _cap_one)

PRODUCTIVITY_BASE_DIR = str(BASE_DIR / "data/dane/productivity") + "/"


def render_productivity(prod_df: pd.DataFrame) -> None:
    st.title(t("Productivity"))

    top_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    file_label = st.selectbox(t("Table:"), list(pr.PRODUCTIVITY_FILES.keys()), format_func=t)
    stem = pr.PRODUCTIVITY_FILES[file_label]
    terms = pr.PRODUCTIVITY_TERMS[stem]

    df = prod_df if stem == pr.DEFAULT_STEM else load_csv(
        f"{PRODUCTIVITY_BASE_DIR}{pr.PRODUCTIVITY_BASE[stem]}/{stem}.csv")
    if stem == pr.ACTIVITY_STEM:
        df[pr.ACTIVITY_COL] = df[pr.ACTIVITY_COL].str.strip()
    years = sorted(df["año"].unique())

    if stem == pr.ACTIVITY_STEM:
        concept_key, activity_key = "prod_concepts_activity", "prod_activities"
        concept_labels = st.sidebar.multiselect(
            t("Concepts:"), list(terms.keys()), default=[list(terms.keys())[0]], key=concept_key,
            on_change=_cap, args=(concept_key, [activity_key]), format_func=t)
        if not concept_labels:
            concept_labels = [list(terms.keys())[0]]
        activity_labels = st.sidebar.multiselect(
            t("Economic Activity:"), list(pr.ACTIVITY_EN.values()), default=["Total Economy"],
            key=activity_key, on_change=_cap, args=(activity_key, [concept_key]), format_func=t)
        if not activity_labels:
            activity_labels = ["Total Economy"]
    else:
        concept_labels = st.sidebar.multiselect(
            t("Concepts:"), list(terms.keys()), default=[list(terms.keys())[0]], format_func=t)
        if not concept_labels:
            concept_labels = [list(terms.keys())[0]]

    cur_years = st.sidebar.multiselect(t("Year:"), years, key="prod_years")

    with top_placeholder.container():
        st.header(t("Filters"))
        chart_type = st.selectbox(t("Chart Type:"), ["Line", "Bar"], format_func=t)

    valid_presidents = get_valid_presidents(years)
    president_restricted = len(concept_labels) >= 2 or (
        stem == pr.ACTIVITY_STEM and len(activity_labels) >= 2)
    if president_restricted:
        _cap_one(["prod_presidents"])
    with president_placeholder.container():
        selected_presidents = president_multiselect(valid_presidents, key="prod_presidents")
    comparing = len(selected_presidents) >= 2

    year_set = set(cur_years)
    for name in selected_presidents:
        year_set.update(set(presidents[name]) & set(years))

    concept_cols = {label: terms[label] for label in concept_labels}
    if stem == pr.ACTIVITY_STEM:
        activities_sp = [find_key_by_value(pr.ACTIVITY_EN, lbl) for lbl in activity_labels]
        series = pf.productivity_activity_pivot(
            df, activities_sp, concept_cols, year_set, activity_col=pr.ACTIVITY_COL)
        if len(activities_sp) >= 2:
            series = series.rename(columns=pr.ACTIVITY_EN)
    else:
        series = pf.productivity_pivot(df, concept_cols, year_set)

    main_label = list(terms.keys())[0]
    units = {"%" if terms[label].rstrip().endswith("(%)") else "pp" for label in concept_labels}
    if units == {"%"}:
        value_label, unit_caption = "Value (%)", None
    elif units == {"pp"}:
        value_label = "Value (pp)"
        unit_caption = t("Values in pp represent percentage-point contributions to {main}, "
                         "which is measured in %.").format(main=t(main_label))
    else:
        value_label = "Value (pp / %)"
        unit_caption = t("{main} is in % (headline measure); "
                         "other concepts are in pp — their contribution to it.").format(main=t(main_label))

    if stem == pr.ACTIVITY_STEM and len(activities_sp) >= 2:
        info = [f"{t(concept_labels[0])} {t('by Economic Activity')}", "Year", value_label]
    elif stem == pr.ACTIVITY_STEM:
        info = [f"{t('Labor Productivity')} — {t(file_label)} · {t(activity_labels[0])}", "Year", value_label]
    else:
        info = [f"{t('Labor Productivity')} — {t(file_label)}", "Year", value_label]
    if comparing:
        series, info = reshape_by_presidents(series, selected_presidents, info)
    elif len(year_set) == 1:
        info[0] = f"{info[0]} · {sorted(year_set)[0]}"

    highlight = highlight_selectbox(series)
    fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
    mc.render_chart(fig)
    if unit_caption:
        st.caption(unit_caption)
    st.caption(t("Source: DANE"))
