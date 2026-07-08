import calendar
import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.miscellaneous import trm_functions as mf
from generalities.macro_generalities.dictionaries import presidents, months
from generalities.function import (to_datatime, highlight_selectbox, find_key_by_value,
                                   get_valid_presidents, president_multiselect,
                                   reshape_by_presidents, show_all_years)


def _year_set(years_sel, presidents_sel, data_years):
    """Union explicit years with each president's years, dropping years the data lacks."""
    ys = set(years_sel)
    for name in presidents_sel:
        ys.update(set(presidents[name]) & set(data_years))
    return ys


def render_trm(df: pd.DataFrame) -> None:
    st.title("Miscellaneous")
    trm_local = to_datatime(df, False)

    chart_type = st.sidebar.selectbox("Chart Type:", ["Line", "Bar"])

    in_month_view = st.session_state.get("trm_in_month", False)
    day_compare = st.session_state.get("trm_day_compare", False)

    year_options = sorted(trm_local.index.year.unique())
    month_labels = list(months.values())
    extra_caption = None

    if in_month_view:
        year_frame, _ = show_all_years(pd.DataFrame(index=year_options), president=False, return_flag=True)
        years_shown = year_frame.index.tolist()

        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("Year:", years_shown, index=len(years_shown) - 1)
        with col2:
            month_label = st.selectbox("Month:", month_labels)
        month_num = find_key_by_value(months, month_label)

        series = mf.trm_day_axis(trm_local, year, month_num)
        info = [f"TRM in {month_label} {year}", "Day", "COP per USD"]

    elif day_compare:
        col1, col2 = st.columns(2)
        with col1:
            month_label = st.selectbox("Month:", month_labels)
        month_num = find_key_by_value(months, month_label)
        days_in_month = calendar.monthrange(2000, month_num)[1]  # leap year keeps Feb 29 selectable
        with col2:
            day = st.selectbox("Day:", list(range(1, days_in_month + 1)))

        series = mf.trm_day_compare(trm_local, day, month_num)
        series = show_all_years(series, president=False)
        info = [f"TRM on {month_label} {day} across years", "Year", "COP per USD"]

    else:
        # Year/Month/President, mutually exclusive (same gating as Job Market -> Unemployment)
        prev_months = st.session_state.get("trm_months", [])
        prev_years = st.session_state.get("trm_years", [])
        prev_pres = st.session_state.get("trm_presidents", [])
        month_disabled = bool(prev_years or prev_pres)
        yearpres_disabled = bool(prev_months)

        col1, col2 = st.columns(2)
        with col1:
            cur_years = st.multiselect("Year:", year_options, key="trm_years", disabled=yearpres_disabled)
        with col2:
            cur_month_labels = st.multiselect("Month:", month_labels, key="trm_months", disabled=month_disabled)

        valid_presidents = get_valid_presidents(year_options)
        with st.sidebar:
            selected_presidents = president_multiselect(
                valid_presidents, disabled=yearpres_disabled, key="trm_presidents"
            )

        month_nums = [] if month_disabled else [find_key_by_value(months, m) for m in cur_month_labels]
        years = [] if yearpres_disabled else cur_years
        presidents_sel = [] if yearpres_disabled else selected_presidents

        if len(presidents_sel) >= 2:
            series = mf.trm_year_axis(trm_local, [])
            info = ["TRM", "Year", "COP per USD"]
            series, info = reshape_by_presidents(series, presidents_sel, info)
        elif years or presidents_sel:  # single president or explicit years -> x = months
            year_set = _year_set(years, presidents_sel, year_options)
            series = mf.trm_month_axis(trm_local, sorted(year_set))
            info = ["TRM by month", "Month", "COP per USD"]
        else:  # months selected, or default -> x = years
            series = mf.trm_year_axis(trm_local, month_nums)
            series = show_all_years(series, president=False)
            info = ["TRM", "Year", "COP per USD"]
            if not (years or presidents_sel or month_nums):
                extra_caption = ("Showing the annual average. Pick month(s) to compare them across years, "
                                 "or year(s)/a president to see months.")

    if series.empty:
        st.warning("No data for selected filters.")
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight)
        mc.render_chart(fig)
        if extra_caption:
            st.caption(extra_caption)

    st.sidebar.checkbox("In-month view", key="trm_in_month", disabled=day_compare)
    st.sidebar.checkbox("Day comparison", key="trm_day_compare", disabled=in_month_view)
    st.caption("Source: Banco de la República")
