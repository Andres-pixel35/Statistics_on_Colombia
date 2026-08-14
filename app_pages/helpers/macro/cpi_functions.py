import pandas as pd
import streamlit as st
from generalities.dictionaries import presidents, months
from generalities.function import get_valid_presidents, find_key_by_value, show_all_years, to_datatime, president_multiselect, load_csv, BASE_DIR
from generalities.macro_generalities.inflation import perspective_names
from generalities.i18n import t

GOAL_PATH = BASE_DIR / "data/banco_republica/CPI/goal.csv"


def build_yearly_table(df: pd.DataFrame, selected_year: list, column: str, method: str, subtitle: str = None) -> tuple:
    series_list = []
    for yr in selected_year:
        s = df.loc[:, column].copy()
        s = s[df.index.year == yr].dropna()
        s.index = s.index.month
        s.index = s.index.map(months)
        s.name = yr
        series_list.append(s)

    cpi_series = pd.concat(series_list, axis=1)
    title = f"{t(method)} — {t(subtitle)}" if subtitle else method
    cpi_info = [title, "Month", "%"]

    return cpi_series, cpi_info

def cpi_sidebar_filters(df: pd.DataFrame, placeholder, president_placeholder, pres_mode: str = "multi") -> tuple:
    df = df.dropna()
    years = df.index.year.unique().astype(int)

    with placeholder.container():
        st.header(t("Filters"))
        chart_type = st.selectbox(t("Chart Type:"), ["Line", "Bar", "Table"], format_func=t)

    valid_presidents = get_valid_presidents(years)
    with president_placeholder.container():
        if pres_mode == "hidden":
            selected_presidents = []
        elif pres_mode == "single":
            choice = st.selectbox(t("Presidents:"), ["—"] + valid_presidents, format_func=t)
            selected_presidents = [] if choice == "—" else [choice]
        else:
            selected_presidents = president_multiselect(valid_presidents)

    return selected_presidents, chart_type

def build_cpi_series(cpi: pd.DataFrame, cpi_c: pd.DataFrame, params: list, subtitle: str = None, flags: list = [False, True], comparing: bool = False) -> tuple:
    perspective_column = params[0]
    president          = params[1]
    method             = params[2]

    selected_month = st.multiselect(t("Month:"), months.values(), default="December", format_func=t)

    if not selected_month:
        selected_month = ["December"]

    number_months = [find_key_by_value(months, m) for m in selected_month]

    series_list = []
    for num, name in zip(number_months, selected_month):
        s = cpi.loc[:, perspective_column].copy()
        s = s[cpi.index.month == num].dropna()
        s.index = s.index.year
        s.name = name
        series_list.append(s)

    cpi_series = pd.concat(series_list, axis=1)

    if not flags[0] and not comparing:
        cpi_series = show_all_years(cpi_series, president)

    if president:
        cpi_series = cpi_series[cpi_series.index.isin(presidents[president])]

    title_base = f"{t(method)} — {t(subtitle)}" if subtitle else t(method)
    compare_headline = False
    compare_goal = False

    if flags[1] and not comparing:
        with st.sidebar:
            compare_headline = st.checkbox(t("Compare with Headline Inflation"), value=False)

        if compare_headline:
            annual_col = find_key_by_value(perspective_names, "Annual")
            h_list = []
            for num, name in zip(number_months, selected_month):
                s = cpi_c.loc[:, annual_col]
                s = s[s.index.year.isin(cpi_series.index)]
                s = s[s.index.month == num].dropna()
                s.index = s.index.year
                s.name = f"{t(name)} ({t('Headline')})"
                h_list.append(s)
            cpi_series = pd.concat([cpi_series] + h_list, axis=1)

    if cpi_series.index.min() > 1990 and not comparing:
        with st.sidebar:
            compare_goal = st.checkbox(t("Compare with Goal Inflation"), value=False)

        if compare_goal:
            goal_df = to_datatime(load_csv(GOAL_PATH), True)
            g = goal_df.loc[:, "Inflación"]
            g = g[g.index.year.isin(cpi_series.index)].dropna()
            g.index = g.index.year
            g = g[~g.index.duplicated(keep="first")]
            g.name = "Goal"
            cpi_series = pd.concat([cpi_series, g], axis=1)

    suffixes = (["Headline"] if compare_headline else []) + (["Goal"] if compare_goal else [])
    cpi_info = (
        [f"{title_base} vs {' & '.join(t(sf) for sf in suffixes)}", "Year", "%"]
        if suffixes
        else [title_base, "Year", "%"]
    )

    return cpi_series, cpi_info

def build_comparison_series(
    items: list,
    items_dict: dict,
    base_path: str,
    perspective_column: str,
    perspective: str,
    fixed_value: int,
    president,
    show_all: bool,
    method: str,
) -> tuple:
    by_year = perspective == "Annual"  # fix a month, index by year; else fix a year, index by month
    series_list = []
    for name in items:
        key = find_key_by_value(items_dict, name)
        df = to_datatime(load_csv(f"{base_path}{key}.csv"), False)
        s = df[perspective_column]
        if by_year:
            s = s[s.index.month == fixed_value].dropna()
            s.index = s.index.year
            if not show_all and not president:
                s = s[s.index >= 2000]
            if president:
                s = s[s.index.isin(presidents[president])]
        else:
            s = s[s.index.year == fixed_value].dropna()
            s.index = s.index.month
        s.name = name
        series_list.append(s)

    cpi_series = pd.concat(series_list, axis=1).sort_index()
    if not by_year:
        cpi_series.index = cpi_series.index.map(months)
    fixed_label = months[fixed_value] if by_year else fixed_value
    x_label = "Year" if by_year else "Month"
    cpi_info = [f"{t(method)} — {t(fixed_label)}", x_label, "%"]
    return cpi_series, cpi_info
