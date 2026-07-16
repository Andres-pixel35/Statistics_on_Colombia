import streamlit as st
import pandas as pd
from pages.helpers import charts as mc
from pages.helpers.macro import debt_functions as dbf
import generalities.macro_generalities.debt as dg
from generalities.dictionaries import presidents, months
from generalities.function import (highlight_selectbox, get_valid_presidents,
                                   president_multiselect, find_key_by_value, to_datatime,
                                   cap_one as _cap_one, SeriesSpec, series_year_axis, series_month_axis)


def _compare_series(build_fn) -> pd.DataFrame:
    """Internal vs External Debt as two columns, via the same build_fn used for the single-concept case."""
    cols = {}
    for label in ("Internal Debt", "External Debt"):
        spec = SeriesSpec(dg.CONCEPTS[label], label)
        cols[label] = build_fn(spec).iloc[:, 0]
    return pd.DataFrame(cols)


def render_debt(df: pd.DataFrame) -> None:
    st.title("Debt")

    local = to_datatime(df, False)
    years = sorted(local.index.year.unique())

    # Compare mode charts one concept-pair line per axis point, so it caps Year to 1 and
    # disables President entirely (mirrors job_market.py's "Compare men vs. women" pattern).
    prev_compare = st.session_state.get("debt_compare", False)
    if prev_compare:
        _cap_one(["debt_years"])

    chart_type = st.sidebar.selectbox("Chart Type:", ["Line", "Bar"])
    cur_years = st.sidebar.multiselect("Year:", years, key="debt_years")

    valid_presidents = get_valid_presidents(years)
    with st.sidebar:
        selected_presidents = president_multiselect(
            valid_presidents, key="debt_presidents", disabled=prev_compare
        )

    year_set = set(cur_years)
    if not prev_compare:
        for name in selected_presidents:
            year_set.update(set(presidents[name]) & set(years))

    month_labels = list(months.values())
    col1, col2 = st.columns(2)
    with col1:
        concept_label = st.selectbox("Concept:", list(dg.CONCEPTS.keys()), disabled=prev_compare)
    with col2:
        month_label = st.selectbox(
            "Month:", month_labels, index=month_labels.index(months[12]), disabled=bool(year_set)
        )

    compare = st.sidebar.checkbox(
        "Compare internal vs. external debt", value=False, key="debt_compare"
    )

    prev_gdp_pct = st.session_state.get("debt_gdp_pct", False)
    show_pct_total_visible = compare or concept_label != "Total Debt"
    prev_pct_total = show_pct_total_visible and st.session_state.get("debt_pct_total", False)
    show_gdp_pct = st.sidebar.checkbox("Show as % of GDP", key="debt_gdp_pct", disabled=prev_pct_total)
    show_pct_total = False
    if show_pct_total_visible:
        show_pct_total = st.sidebar.checkbox(
            "Show as % of Total Debt", key="debt_pct_total", disabled=prev_gdp_pct
        )
    else:
        st.session_state["debt_pct_total"] = False

    if year_set:
        years_sorted = sorted(year_set)
        year = years_sorted[0]
        year_list = [year] if compare else years_sorted
        if compare:
            series = _compare_series(lambda spec: series_month_axis(local, spec, year_list))
            info = [f"Internal vs. External Debt · {year}", "Month", "Trillion (COP)"]
        else:
            spec = SeriesSpec(dg.CONCEPTS[concept_label], concept_label)
            series = series_month_axis(local, spec, year_list)
            info = [concept_label, "Month", "Trillion (COP)"]
    else:
        month_num = find_key_by_value(months, month_label)
        if compare:
            series = _compare_series(lambda spec: series_year_axis(local, spec, [month_num]))
            info = [f"Internal vs. External Debt · {month_label}", "Year", "Trillion (COP)"]
        else:
            spec = SeriesSpec(dg.CONCEPTS[concept_label], concept_label)
            series = series_year_axis(local, spec, [month_num]).rename(columns={month_label: concept_label})
            info = [f"{concept_label} · {month_label}", "Year", "Trillion (COP)"]

    gdp_note = None
    if show_gdp_pct:
        gdp = dbf.gdp_millions(dg.NOMINAL_ANNUAL_PATH)
        pct_year = years_sorted[0] if (year_set and compare) else None
        missing = dbf.missing_gdp_years(series, gdp, year=pct_year)
        labels = dbf.gdp_pct_labels(series, pct_year)
        if missing and len(missing) == len(labels):
            gdp_note = f"No GDP data yet for {', '.join(missing)} — showing Trillion (COP) instead."
            show_gdp_pct = False
        else:
            if missing:
                gdp_note = f"No GDP data yet for {', '.join(missing)} — shown as gaps."
            series = dbf.to_gdp_pct(series, gdp, year=pct_year)
            info[2] = "% of GDP"

    elif show_pct_total:
        if year_set:
            total = series_month_axis(local, dg.TOTAL_SPEC, year_list)
            if compare:
                total = total.iloc[:, 0]
        else:
            total = series_year_axis(local, dg.TOTAL_SPEC, [month_num]).iloc[:, 0]
        series = dbf.to_total_pct(series, total)
        info[2] = "% of Total Debt"

    if not show_gdp_pct and not show_pct_total:
        series = series / 1_000_000  # COP millions -> Trillion (COP)

    if series.empty:
        st.warning("No data for selected filters.")
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
    if gdp_note:
        st.info(gdp_note)
    st.caption("Shows Central National Government Gross Debt")
    st.caption("Source: Ministerio de Hacienda")
