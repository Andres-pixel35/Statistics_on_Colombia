import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.macro import job_market_functions as mf
import generalities.macro_generalities.job_market as jm
from generalities.macro_generalities.dictionaries import presidents, months
from generalities.function import (to_datatime, load_csv, BASE_DIR,
                                   highlight_selectbox, find_key_by_value)

LABOR_FORCE_BASE = str(BASE_DIR / "data/dane/job_market/Mercado Laboral") + "/"


def render_job_market(unemployment_df: pd.DataFrame) -> None:
    st.title("Job Market")

    dataset = st.sidebar.radio("Dataset:", ["Unemployment", "Labor Force"])

    top_placeholder = st.sidebar.empty()
    president_placeholder = st.sidebar.empty()

    if dataset == "Unemployment":
        unemp_local = to_datatime(unemployment_df, True)

        # Mutually-exclusive controls: read prior selections to gate them (Streamlit reruns
        # top-to-bottom, so the lock comes from last run's session_state).
        prev_months = st.session_state.get("unemp_months", [])
        prev_years = st.session_state.get("unemp_years", [])
        prev_pres = st.session_state.get("unemp_presidents", [])
        month_disabled = bool(prev_years or prev_pres)
        yearpres_disabled = bool(prev_months)

        year_options = sorted(unemp_local.index.year.unique())
        col1, col2 = st.columns(2)
        with col1:
            cur_years = st.multiselect(
                "Year:", year_options, key="unemp_years", disabled=yearpres_disabled
            )
        with col2:
            cur_month_labels = st.multiselect(
                "Month:", list(months.values()), key="unemp_months", disabled=month_disabled
            )

        selected_presidents, chart_type = mf.job_market_sidebar_filters(
            mf.unemployment_year_axis(unemp_local, []), top_placeholder, president_placeholder,
            president_disabled=yearpres_disabled, president_key="unemp_presidents",
        )

        # Null out disabled controls so a stale lock can't leak into mode resolution.
        month_nums = ([] if month_disabled
                      else [find_key_by_value(months, m) for m in cur_month_labels])
        years = [] if yearpres_disabled else cur_years
        presidents_sel = [] if yearpres_disabled else selected_presidents

        if years or presidents_sel:  # YEAR mode -> x = months
            year_set = set(years)
            for name in presidents_sel:
                year_set.update(presidents[name])
            series = mf.unemployment_month_axis(unemp_local, sorted(year_set))
            info = ["Unemployment rate by month", "Month", "Rate (%)"]
        else:  # MONTH mode (months selected) or DEFAULT -> x = years
            series = mf.unemployment_year_axis(unemp_local, month_nums)
            info = ["Unemployment rate", "Year", "Rate (%)"]

        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
        if not (years or presidents_sel or month_nums):
            st.caption("Showing the annual average across all months. "
                       "Pick month(s) to compare them across years, or year(s)/a president to see months.")
        st.caption("Source: Banco de la República")
        return

    # Labor Force
    col2, col3, col4 = st.columns(3)
    with col2:
        file_label = st.selectbox("Table:", list(jm.LABOR_FORCE_FILES.keys()))
    stem = jm.LABOR_FORCE_FILES[file_label]
    terms = jm.LABOR_FORCE_TERMS[stem]

    data = load_csv(f"{LABOR_FORCE_BASE}{stem}.csv")

    with col3:
        gender = st.selectbox("Gender:", list(jm.GENDER.keys()))
    gender_sp = jm.GENDER[gender]

    # Period (window) / Year / President are mutually-exclusive axes; gate on last run's state.
    # Concepts vs Years are symmetrically capped: picking 2+ of one locks the other to 1.
    prev_concept_n = st.session_state.get("lf_concept_n", 0)
    prev_years = st.session_state.get("lf_years", [])
    prev_period = st.session_state.get("lf_period", "Annual average")
    prev_pres = st.session_state.get("lf_presidents", [])

    multi_concept = prev_concept_n >= 2
    period_active = prev_period not in (None, "Annual average")
    windows_active = bool(prev_years) or bool(prev_pres)

    period_disabled = windows_active
    year_disabled = period_active
    year_max = 1 if multi_concept else None
    president_disabled = period_active or multi_concept
    concept_max = 1 if (len(prev_years) >= 2 or prev_pres) else None

    with col4:
        period = st.selectbox(
            "Period:", ["Annual average"] + list(jm.PERIOD_EN.values()),
            key="lf_period", disabled=period_disabled,
        )

    year_options = sorted(data["Fecha"].unique())
    cur_years = st.sidebar.multiselect(
        "Year:", year_options, key="lf_years", disabled=year_disabled, max_selections=year_max
    )

    concept_labels = st.sidebar.multiselect(
        "Concepts:", list(terms.values()), default=[next(iter(terms.values()))],
        max_selections=concept_max,
    )
    if not concept_labels:
        concept_labels = [next(iter(terms.values()))]
    st.session_state["lf_concept_n"] = len(concept_labels)
    concepts_sp = [find_key_by_value(terms, lbl) for lbl in concept_labels]
    eng_map = {sp: terms[sp] for sp in concepts_sp}

    selected_presidents, chart_type = mf.job_market_sidebar_filters(
        mf.labor_force_pivot(data, gender_sp, None, concepts_sp),
        top_placeholder, president_placeholder,
        president_disabled=president_disabled, president_key="lf_presidents",
    )

    # Null out disabled controls so a stale lock can't leak into mode resolution.
    years_sel = [] if year_disabled else cur_years
    presidents_sel = [] if president_disabled else selected_presidents
    year_set = set(years_sel)
    for name in presidents_sel:
        year_set.update(presidents[name])

    if year_set:  # WINDOWS mode -> x = rolling windows
        years_sorted = sorted(year_set)
        if len(concepts_sp) >= 2:  # concept priority -> single year (enforced by gating)
            years_sorted, labels = years_sorted[:1], eng_map
        else:
            labels = {}
        series = mf.labor_force_period_axis(data, gender_sp, years_sorted, concepts_sp)
        info = [f"Labor Force — {file_label} ({gender}) by 3-month window", "Period", "People"]
        highlight = highlight_selectbox(
            series, display_names=list(eng_map.values()) if labels else None
        )
        fig = mc.line_or_bar(chart_type, series, info, labels=labels, highlight=highlight)
        mc.render_chart(fig)
        st.caption("Source: DANE (GEIH)")
        return

    # YEAR-axis mode (no years, no president)
    period_sp = None if period == "Annual average" else find_key_by_value(jm.PERIOD_EN, period)
    series = mf.labor_force_pivot(data, gender_sp, period_sp, concepts_sp)
    info = [f"Labor Force — {file_label} ({gender}) · {period}", "Year", "People"]
    highlight = highlight_selectbox(series, display_names=list(eng_map.values()))
    fig = mc.line_or_bar(chart_type, series, info, labels=eng_map, highlight=highlight)
    mc.render_chart(fig)
    st.caption("Source: DANE (GEIH)")
