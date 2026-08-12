import calendar
import streamlit as st
import pandas as pd
from app_pages.helpers import charts as mc
from app_pages.helpers.miscellaneous import rates_functions as rf
from generalities.dictionaries import presidents, months
from generalities.i18n import t, fmt_date
from generalities.function import (to_datatime, highlight_selectbox, find_key_by_value,
                                   get_valid_presidents, president_multiselect,
                                   reshape_by_presidents, show_all_years,
                                   SeriesSpec, series_year_axis, series_month_axis)

SPEC = SeriesSpec("Tasa (%)", "Monetary Policy Rate")
UNIT = "%"


def _year_set(years_sel, presidents_sel, data_years):
    """Union explicit years with each president's years, dropping years the data lacks."""
    ys = set(years_sel)
    for name in presidents_sel:
        ys.update(set(presidents[name]) & set(data_years))
    return ys


def render_monetary_policy_rate(df: pd.DataFrame) -> None:
    st.title(t("Miscellaneous"))
    local = rf.forward_fill_through(to_datatime(df, True), pd.Timestamp.now().normalize())

    chart_type = st.sidebar.selectbox(t("Chart Type:"), ["Line", "Bar", "Table"], format_func=t)

    in_month_view = st.session_state.get("policy_rate_in_month", False)
    day_compare = st.session_state.get("policy_rate_day_compare", False)

    year_options = sorted(local.index.year.unique())
    month_labels = list(months.values())
    extra_caption = None

    if in_month_view:
        year_frame, _ = show_all_years(pd.DataFrame(index=year_options), president=False, return_flag=True)
        years_shown = year_frame.index.tolist()

        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox(t("Year:"), years_shown, index=len(years_shown) - 1)
        with col2:
            month_label = st.selectbox(t("Month:"), month_labels, format_func=t)
        month_num = find_key_by_value(months, month_label)

        series = rf.rate_day_axis(local, SPEC, year, month_num)
        info = [t("{label} in {month} {year}").format(label=t(SPEC.label), month=t(month_label), year=year), "Day", UNIT]

    elif day_compare:
        col1, col2 = st.columns(2)
        with col1:
            month_label = st.selectbox(t("Month:"), month_labels, format_func=t)
        month_num = find_key_by_value(months, month_label)
        days_in_month = calendar.monthrange(2000, month_num)[1]  # leap year keeps Feb 29 selectable
        with col2:
            day = st.selectbox(t("Day:"), list(range(1, days_in_month + 1)))

        today = pd.Timestamp.now()
        year_end = pd.Timestamp(year=today.year, month=12, day=31)
        extended = rf.forward_fill_through(local, year_end)

        series = rf.rate_day_compare(extended, SPEC, day, month_num)
        series = show_all_years(series, president=False)
        info = [t("{label} on {month} {day} across years").format(label=t(SPEC.label), month=t(month_label), day=day), "Year", UNIT]

        if today.year in series.index and (month_num, day) > (today.month, today.day):
            extra_caption = t("{year} is projected using the most recent Policy Rate "
                              "({date}) and is subject to change.").format(
                year=today.year, date=fmt_date(today, "%B %d, %Y"))

    else:
        # Year/Month/President, mutually exclusive (same gating as Job Market -> Unemployment)
        prev_months = st.session_state.get("policy_rate_months", [])
        prev_years = st.session_state.get("policy_rate_years", [])
        prev_pres = st.session_state.get("policy_rate_presidents", [])
        month_disabled = bool(prev_years or prev_pres)
        yearpres_disabled = bool(prev_months)

        col1, col2 = st.columns(2)
        with col1:
            cur_years = st.multiselect(t("Year:"), year_options, key="policy_rate_years", disabled=yearpres_disabled)
        with col2:
            cur_month_labels = st.multiselect(t("Month:"), month_labels, key="policy_rate_months",
                                               disabled=month_disabled, format_func=t)

        valid_presidents = get_valid_presidents(year_options)
        with st.sidebar:
            selected_presidents = president_multiselect(
                valid_presidents, disabled=yearpres_disabled, key="policy_rate_presidents"
            )

        month_nums = [] if month_disabled else [find_key_by_value(months, m) for m in cur_month_labels]
        years = [] if yearpres_disabled else cur_years
        presidents_sel = [] if yearpres_disabled else selected_presidents

        if len(presidents_sel) >= 2:
            series = series_year_axis(local, SPEC, [])
            info = [SPEC.label, "Year", UNIT]
            series, info = reshape_by_presidents(series, presidents_sel, info)
        elif years or presidents_sel:  # single president or explicit years -> x = months
            year_set = _year_set(years, presidents_sel, year_options)
            series = series_month_axis(local, SPEC, sorted(year_set))
            info = [t("{label} by month").format(label=t(SPEC.label)), "Month", UNIT]
        else:  # months selected, or default -> x = years
            series = series_year_axis(local, SPEC, month_nums)
            series = show_all_years(series, president=False)
            info = [SPEC.label, "Year", UNIT]
            if not (years or presidents_sel or month_nums):
                extra_caption = t("Showing the annual average. Pick month(s) to compare them across years, "
                                 "or year(s)/a president to see months.")

    if series.empty:
        st.warning(t("No data for selected filters."))
    else:
        highlight = highlight_selectbox(series)
        fig = mc.line_or_bar(chart_type, series, info, highlight=highlight, force_bar=in_month_view)
        mc.render_chart(fig)
        if extra_caption:
            st.caption(extra_caption)

    st.sidebar.checkbox(t("In-month view"), key="policy_rate_in_month", disabled=day_compare)
    st.sidebar.checkbox(t("Day comparison"), key="policy_rate_day_compare", disabled=in_month_view)
    st.caption(t("Source: Banco de la República"))
