import streamlit as st
import pandas as pd
from pages.helpers import charts as mc
from generalities.dictionaries import presidents, months
from generalities.function import (to_datatime, highlight_selectbox, find_key_by_value,
                                   get_valid_presidents, president_multiselect,
                                   reshape_by_presidents,
                                   SeriesSpec, series_year_axis, series_month_axis)

SPEC = SeriesSpec("Tasa (%)", "Lending Rate")
UNIT = "%"


def _year_set(years_sel, presidents_sel, data_years):
    """Union explicit years with each president's years, dropping years the data lacks."""
    ys = set(years_sel)
    for name in presidents_sel:
        ys.update(set(presidents[name]) & set(data_years))
    return ys


def render_lending_rate(df: pd.DataFrame) -> None:
    st.title("Miscellaneous")
    local = to_datatime(df, True)

    chart_type = st.sidebar.selectbox("Chart Type:", ["Line", "Bar"])

    year_options = sorted(local.index.year.unique())
    month_labels = list(months.values())

    prev_months = st.session_state.get("lending_rate_months", ["December"])
    prev_years = st.session_state.get("lending_rate_years", [])
    prev_pres = st.session_state.get("lending_rate_presidents", [])
    month_disabled = bool(prev_years or prev_pres)
    yearpres_disabled = bool(prev_months)

    col1, col2 = st.columns(2)
    with col1:
        cur_years = st.multiselect("Year:", year_options, key="lending_rate_years", disabled=yearpres_disabled)
    with col2:
        cur_month_labels = st.multiselect("Month:", month_labels, default=["December"],
                                           key="lending_rate_months", disabled=month_disabled)

    valid_presidents = get_valid_presidents(year_options)
    with st.sidebar:
        selected_presidents = president_multiselect(
            valid_presidents, disabled=yearpres_disabled, key="lending_rate_presidents"
        )

    month_nums = [] if month_disabled else [find_key_by_value(months, m) for m in cur_month_labels]
    years = [] if yearpres_disabled else cur_years
    presidents_sel = [] if yearpres_disabled else selected_presidents

    annual_avg = False
    if len(presidents_sel) >= 2:
        series = series_year_axis(local, SPEC, [])
        info = [SPEC.label, "Year", UNIT]
        series, info = reshape_by_presidents(series, presidents_sel, info)
        annual_avg = True
    elif years or presidents_sel:  # single president or explicit years -> x = months
        year_set = _year_set(years, presidents_sel, year_options)
        series = series_month_axis(local, SPEC, sorted(year_set))
        info = [f"{SPEC.label} by month", "Month", UNIT]
    else:  # months selected, or default -> x = years
        series = series_year_axis(local, SPEC, month_nums)
        info = [SPEC.label, "Year", UNIT]
        annual_avg = not month_nums

    if series.empty:
        st.warning("No data for selected filters.")
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
        if annual_avg:
            st.caption("Using annual average")

    st.caption("Source: Banco de la República")
