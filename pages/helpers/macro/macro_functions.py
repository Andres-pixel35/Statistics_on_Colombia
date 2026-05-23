import pandas as pd
import streamlit as st
from pages.helpers.macro import macro_charts as mc
from generalities.dictionaries import presidents, months
from generalities.function import get_valid_presidents, find_key_by_value, show_all_years, to_datatime, president_multiselect, reshape_by_presidents, load_csv, BASE_DIR
from generalities.inflation import perspective_names
from generalities.migration import COUNTRY_EN, COL_MAP

GOAL_PATH = BASE_DIR / "data/banco_republica/CPI/goal.csv"

def clean_gdp(df: pd.DataFrame, rows):
    gdp_local = df.copy()

    gdp_local = gdp_local.set_index("Concepto")
    gdp_local = gdp_local.apply(lambda col: col.str.replace(".", "", regex=False))

    if isinstance(rows, int):
        gdp_series = gdp_local.iloc[rows,:]
    else:
        gdp_series = gdp_local.loc[rows,:]

    gdp_series = gdp_series.T
    gdp_series = gdp_series.astype(int)

    if len(gdp_series) > 5:
        gdp_series.index = gdp_series.index.str.split("-").str[0]
        gdp_series = gdp_series.groupby(gdp_series.index).sum()

    return gdp_series

def generalities_spend_product(df: pd.DataFrame, terms: dict, variable: int|list, info: list) -> None:
    """
    General utilities used in several parts of this section.
    filters in the sidebar and the logic to plot the chart
    """
    with st.sidebar: 
        st.header("Filters:")
        
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])

        years = df.columns[1:].str.split("-").str[0].unique()

        tmp_years = years.str.replace("p|r", "", regex=True)
        tmp_years = tmp_years.astype(int)

        valid_presidents = get_valid_presidents(tmp_years)

        selected_presidents = president_multiselect(valid_presidents)
        comparing = len(selected_presidents) >= 2
        president = selected_presidents[0] if len(selected_presidents) == 1 else None

        if comparing:
            choice_year = []
        elif president:
            pres_years = [y for y, ty in zip(years, tmp_years) if ty in presidents[president]]
            choice_year = st.multiselect("Year:", sorted(pres_years, reverse=True))
        else:
            choice_year = st.multiselect("Year:", sorted(years, reverse=True))

        tmp = st.multiselect("Variable:", terms.values())
        if tmp:
            variable = [k for k, v in terms.items() if v in tmp]

    if comparing:
        pattern = None
    elif choice_year:
        pattern = "|".join(choice_year)
    elif president:
        pattern = "|".join(pres_years)
    else:
        pattern = None

    if pattern:
        mask = df.columns.str.contains(pattern)
        mask[0] = True
        df = df.loc[:, mask]

    # plot the chart
    gdp_series = clean_gdp(df, variable)

    if comparing:
        if isinstance(gdp_series, pd.Series):
            gdp_series = gdp_series.to_frame()
        gdp_series, info = reshape_by_presidents(gdp_series, selected_presidents, info, col_labels=terms)
        labels_arg = {}
    else:
        labels_arg = terms

    highlight = None
    if isinstance(gdp_series, pd.DataFrame) and len(gdp_series.columns) > 1:
        display_names = [terms.get(col, col) for col in gdp_series.columns]
        with st.sidebar:
            highlight_choice = st.selectbox("Highlight variable:", ["—"] + display_names)
            highlight = None if highlight_choice == "—" else highlight_choice

    if chart_type == "Bar":
        fig = mc.bar_chart(gdp_series, labels_arg, info, highlight=highlight)
    else:
        fig = mc.line_chart(gdp_series, labels_arg, info, highlight=highlight)

    st.plotly_chart(fig)
    st.caption(f"{info[3]}, base year 2015")
    st.caption("Source: DANE")
    st.info("\'p\' is provisional and \'pr\' is preliminary data.")

def clean_annual_growth(df: pd.DataFrame, year: list, president: str, index: int, quarter: str|None) -> tuple:
    df.columns = df.columns.str.strip()
    df[df.columns[index]] = df[df.columns[index]].astype(float)
    df_local = df.copy()

    df_local = df_local.set_index("Fecha")  

    if quarter is not None:
        df_local = df_local[df_local.index.str.contains(f"-{quarter}$", regex=True)]

        df_local = df_local.drop(columns=["Variación Año Corrido"])

        if year:
            pattern = "|".join(map(str, year))
            df_local = df_local[df_local.index.str.contains(pattern)]

        if president:
            presidents_new = {k: [str(i) for i in v] for k, v in presidents.items()}

            pattern = "|".join(presidents_new[president])

            df_local = df_local[df_local.index.str.contains(pattern)]
    else:
        if year:
            df_local = df_local[df_local.index.isin(map(str, year))]

        if president:
            df_local.index = df_local.index.astype(int)

            df_local = df_local[df_local.index.isin(presidents[president])]

    return df, df_local

# CPI
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
    title = f"{method} — {subtitle}" if subtitle else method
    cpi_info = [title, "Month", "%"]

    return cpi_series, cpi_info

def cpi_sidebar_filters(df: pd.DataFrame, placeholder, president_placeholder) -> tuple:
    df = df.dropna()
    years = df.index.year.unique().astype(int)

    with placeholder.container():
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])

    valid_presidents = get_valid_presidents(years)
    with president_placeholder.container():
        selected_presidents = president_multiselect(valid_presidents)

    return selected_presidents, chart_type

def build_cpi_series(cpi: pd.DataFrame, cpi_c: pd.DataFrame, params: list, subtitle: str = None, flags: list = [False, True], comparing: bool = False) -> tuple:
    perspective_column = params[0]
    president          = params[1]
    method             = params[2]

    selected_month = st.multiselect("Month:", months.values(), default="December")

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

    title_base = f"{method} — {subtitle}" if subtitle else method
    compare_headline = False
    compare_goal = False

    if flags[1] and not comparing:
        with st.sidebar:
            compare_headline = st.checkbox("Compare with Headline Inflation", value=False)

        if compare_headline:
            annual_col = find_key_by_value(perspective_names, "Annual")
            h_list = []
            for num, name in zip(number_months, selected_month):
                s = cpi_c.loc[:, annual_col]
                s = s[s.index.year.isin(cpi_series.index)]
                s = s[s.index.month == num].dropna()
                s.index = s.index.year
                s.name = f"{name} (Headline)"
                h_list.append(s)
            cpi_series = pd.concat([cpi_series] + h_list, axis=1)

    if cpi_series.index.min() > 1990 and not comparing:
        with st.sidebar:
            compare_goal = st.checkbox("Compare with Goal Inflation", value=False)

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
        [f"{title_base} vs {' & '.join(suffixes)}", "Year", "%"]
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
            s.index = s.index.month.map(months)
        s.name = name
        series_list.append(s)

    cpi_series = pd.concat(series_list, axis=1)
    fixed_label = months[fixed_value] if by_year else fixed_value
    x_label = "Year" if by_year else "Month"
    cpi_info = [f"{method} — {fixed_label}", x_label, "%"]
    return cpi_series, cpi_info

# Migration

def build_migration_map_data(df: pd.DataFrame, year: int | None, month_name: str, data_col: str, meta: list) -> tuple:
    direction, _, _ = meta

    if year is None:
        if month_name == "All":
            filtered = df
            title = f"{direction} travelers — All years"
        else:
            month_num = find_key_by_value(months, month_name)
            filtered = df[df["Fecha"].dt.month == month_num]
            title = f"{direction} travelers — {month_name} (All years)"
    elif month_name == "All":
        filtered = df[df["Fecha"].dt.year == year]
        title = f"{direction} travelers — {year}"
    else:
        month_num = find_key_by_value(months, month_name)
        filtered = df[(df["Fecha"].dt.year == year) & (df["Fecha"].dt.month == month_num)]
        title = f"{direction} travelers — {month_name} {year}"

    grouped = filtered.groupby("País")[data_col].sum().reset_index()
    grouped["Location"] = grouped["País"].map(COUNTRY_EN)
    grouped = grouped.dropna(subset=["Location"])

    return grouped, title

def migration_countries_pivot(df_f: pd.DataFrame, all_countries_en: list, data_col: str, period_label: str, meta: list) -> tuple:
    direction, metric, label = meta

    with st.sidebar:
        selected_en = st.multiselect("Countries:", all_countries_en)

    if not selected_en:
        st.info("Select one or more countries from the sidebar.")
        return None, None

    selected_es = [find_key_by_value(COUNTRY_EN, n) for n in selected_en]
    df_c = df_f[df_f["País"].isin(selected_es)].copy()
    df_c["País_en"] = df_c["País"].map(COUNTRY_EN)

    pivot = (
        df_c.pivot_table(index="Period", columns="País_en", values=data_col, aggfunc="sum")
        .fillna(0)
        .astype(int)
    )
    pivot.index.name = period_label
    info = [f"{direction} — {metric} travelers by country", period_label, label]

    return pivot, info

def migration_single_pivot(df_f: pd.DataFrame, all_countries_en: list, compare_by: str, meta: list, period_label: str) -> tuple:
    direction, metric, _ = meta

    key = "mig_country_dir" if compare_by == "Direction" else "mig_country_gender"

    with st.sidebar:
        selected_en = st.selectbox("Country:", ["All"] + all_countries_en, key=key)

    if selected_en != "All":
        country_es = find_key_by_value(COUNTRY_EN, selected_en)
        df_f = df_f[df_f["País"] == country_es]

    country_label = "All countries" if selected_en == "All" else selected_en

    if compare_by == "Direction":
        col_a = COL_MAP[("Inbound", metric)]
        col_b = COL_MAP[("Outbound", metric)]
        col_names = ["Inbound", "Outbound"]
        title = f"{country_label} — {metric} travelers"
    else:
        col_a = COL_MAP[(direction, "Female")]
        col_b = COL_MAP[(direction, "Male")]
        col_names = ["Female", "Male"]
        title = f"{country_label} — {direction} by gender"

    pivot = df_f.groupby("Period")[[col_a, col_b]].sum()
    pivot.columns = col_names
    pivot.index.name = period_label
    info = [title, period_label, "People"]

    return pivot, info

def migration_year_pivot(df_f: pd.DataFrame, data_col: str, meta: list) -> tuple:
    direction, metric, label, *country = meta

    month_order = [months[i] for i in sorted(months.keys())]

    df_f = df_f.copy()
    df_f["Month_num"] = df_f["Fecha"].dt.month
    df_f["Year"] = df_f["Fecha"].dt.year.astype(str)

    pivot = (
        df_f.pivot_table(index="Month_num", columns="Year", values=data_col, aggfunc="sum")
        .fillna(0)
        .astype(int)
    )
    pivot.index = pivot.index.map(months)
    pivot = pivot.reindex([m for m in month_order if m in pivot.index])
    pivot.index.name = "Month"

    if country:
        info = [f"{direction} — {country[0]} year comparison", "Month", label]
    else:
        info = [f"{direction} — {metric} year comparison", "Month", label]

    return pivot, info
