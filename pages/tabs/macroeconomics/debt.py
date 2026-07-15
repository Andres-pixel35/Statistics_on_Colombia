import streamlit as st
import pandas as pd
from pages.helpers import charts as mc
from generalities.dictionaries import presidents, months
from generalities.function import (highlight_selectbox, get_valid_presidents,
                                   president_multiselect, find_key_by_value, to_datatime,
                                   cap_one as _cap_one, SeriesSpec, series_year_axis, series_month_axis)

CONCEPTS = {"Total Debt": "Deuda total", "Internal Debt": "Deuda interna", "External Debt": "Deuda externa"}


def _compare_series(build_fn) -> pd.DataFrame:
    """Internal vs External Debt as two columns, via the same build_fn used for the single-concept case."""
    cols = {}
    for label in ("Internal Debt", "External Debt"):
        spec = SeriesSpec(CONCEPTS[label], label)
        cols[label] = build_fn(spec).iloc[:, 0]
    return pd.DataFrame(cols)


def render_debt(df: pd.DataFrame) -> None:
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

    compare = st.sidebar.checkbox(
        "Compare internal vs. external debt", value=False, key="debt_compare"
    )

    month_labels = list(months.values())
    col1, col2 = st.columns(2)
    with col1:
        concept_label = st.selectbox("Concept:", list(CONCEPTS.keys()), disabled=prev_compare)
    with col2:
        month_label = st.selectbox(
            "Month:", month_labels, index=month_labels.index(months[12]), disabled=bool(year_set)
        )

    if year_set:
        years_sorted = sorted(year_set)
        year = years_sorted[0]
        year_list = [year] if compare else years_sorted
        if compare:
            series = _compare_series(lambda spec: series_month_axis(local, spec, year_list))
            info = [f"Internal vs. External Debt · {year}", "Month", "COP millions"]
        else:
            spec = SeriesSpec(CONCEPTS[concept_label], concept_label)
            series = series_month_axis(local, spec, year_list)
            info = [concept_label, "Month", "COP millions"]
    else:
        month_num = find_key_by_value(months, month_label)
        if compare:
            series = _compare_series(lambda spec: series_year_axis(local, spec, [month_num]))
            info = [f"Internal vs. External Debt · {month_label}", "Year", "COP millions"]
        else:
            spec = SeriesSpec(CONCEPTS[concept_label], concept_label)
            series = series_year_axis(local, spec, [month_num]).rename(columns={month_label: concept_label})
            info = [f"{concept_label} · {month_label}", "Year", "COP millions"]

    if series.empty:
        st.warning("No data for selected filters.")
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
    st.caption("Source: Ministerio de Hacienda")
