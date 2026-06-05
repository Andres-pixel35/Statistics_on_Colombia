import pandas as pd
import streamlit as st
from pages.helpers.macro import macro_charts as mc
from generalities.dictionaries import presidents, months
from generalities.function import get_valid_presidents, find_key_by_value, show_all_years, to_datatime, president_multiselect, reshape_by_presidents, load_csv, BASE_DIR, norm, highlight_selectbox
from generalities.inflation import perspective_names
from generalities.migration import COUNTRY_EN, COL_MAP
from generalities.births import GENDER_EN, AGE_EN, EDU_EN
from generalities.deaths import GENDER_EN as DEATHS_GENDER_EN, AREA_EN, AGE_EN as DEATHS_AGE_EN, CAUSE_EN

GOAL_PATH       = BASE_DIR / "data/banco_republica/CPI/goal.csv"
POPULATION_PATH = BASE_DIR / "data/banco_republica/population/population.csv"

def clean_gdp(df: pd.DataFrame, rows):
    gdp_local = df.copy()

    gdp_local = gdp_local.set_index("Concepto")

    if isinstance(rows, int):
        gdp_series = gdp_local.iloc[rows,:]
    else:
        gdp_series = gdp_local.loc[rows,:]

    gdp_series = gdp_series.T
    gdp_series = gdp_series.astype(float)

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

        quarter = st.selectbox("Quarter:", ["All", "I", "II", "III", "IV"])

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

        per_capita = st.checkbox("GDP per Capita")

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

    if quarter != "All":
        qmask = df.columns.str.contains(rf"-{quarter}$", regex=True)
        qmask = qmask | (df.columns == "Concepto")
        df = df.loc[:, qmask]
        info[0] = f"{info[0]} — Q{quarter}"

    # plot the chart
    gdp_series = clean_gdp(df, variable)

    if per_capita:
        pop_raw = load_csv(POPULATION_PATH)
        pop_raw = to_datatime(pop_raw, dayfirst=True)
        pop = pop_raw["Población"].astype(int)
        pop.index = pop.index.year
        clean_years = gdp_series.index.str.replace(r'\D+', '', regex=True).astype(int)
        pop_aligned = pd.Series(pop.reindex(clean_years).values, index=gdp_series.index)
        original_name = gdp_series.name if isinstance(gdp_series, pd.Series) else None
        gdp_series = gdp_series.div(pop_aligned, axis=0) * 1_000_000_000_000
        gdp_series = gdp_series.dropna()
        if original_name is not None:
            gdp_series.name = original_name
        info[2] = "COP per capita"

    if comparing:
        if isinstance(gdp_series, pd.Series):
            gdp_series = gdp_series.to_frame()
        gdp_series, info = reshape_by_presidents(gdp_series, selected_presidents, info, col_labels=terms)
        labels_arg = {}
    else:
        labels_arg = terms

    highlight = highlight_selectbox(gdp_series, [terms.get(c, c) for c in gdp_series.columns] if isinstance(gdp_series, pd.DataFrame) else None)

    if chart_type == "Bar" or len(gdp_series) == 1:
        fig = mc.bar_chart(gdp_series, labels_arg, info, highlight=highlight)
    else:
        fig = mc.line_chart(gdp_series, labels_arg, info, highlight=highlight)

    mc.render_chart(fig)
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

# Births

def births_national_series(total_df: pd.DataFrame) -> pd.Series:
    s = total_df.set_index("year")["total_nacional"].astype(float)
    s.index = s.index.astype(int)
    return s

def births_gender_pivot(total_df: pd.DataFrame) -> tuple:
    df = total_df.set_index("year")[["hombres", "mujeres"]].astype(int).rename(columns=GENDER_EN)
    df.index = df.index.astype(int)
    df.index.name = "Year"
    return df, ["Births by gender", "Year", "Births"]

def births_age_pivot(age_df: pd.DataFrame) -> tuple:
    df = age_df.copy()
    df["age"] = df["grupo_edad"].map(AGE_EN).fillna(df["grupo_edad"])
    pivot = df.pivot_table(index="year", columns="age", values="total", aggfunc="sum").astype(int)
    order = [v for v in AGE_EN.values() if v in pivot.columns]
    pivot = pivot[order]
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"
    return pivot, ["Births by mother's age group", "Year", "Births"]

def births_education_pivot(edu_df: pd.DataFrame, age_label: str | None) -> tuple:
    df = edu_df.copy()
    edu_cols = [c for c in EDU_EN if c in df.columns]

    title = "Births by mother's education level"
    if age_label and age_label != "All ages":
        es = find_key_by_value(AGE_EN, age_label) or age_label
        df = df[df["grupo_edad"] == es]
        title += f" — mothers {age_label}"

    g = df.groupby("year")[edu_cols].sum().astype(int)
    g.columns = [EDU_EN[c] for c in g.columns]
    g.index = g.index.astype(int)
    g.index.name = "Year"
    return g, [title, "Year", "Births"]

def births_department_data(dept_df: pd.DataFrame, years: list, metric_col: str) -> pd.DataFrame:
    df = dept_df.copy()
    if years:
        df = df[df["year"].isin(years)]
    grouped = df.groupby("departamento")[metric_col].sum().reset_index()
    grouped["Code"] = grouped["departamento"].str.split(n=1).str[0]
    grouped["Name"] = grouped["departamento"].str.split(n=1).str[1]
    return grouped

def births_geo_trend(df: pd.DataFrame, entity_col: str, selected: list, years: list, value_col: str = "total") -> pd.DataFrame:
    d = df.copy()
    d["Name"] = d[entity_col].str.split(n=1).str[1]
    if years:
        d = d[d["year"].isin(years)]
    if selected:
        d = d[d["Name"].isin(selected)]
    pivot = (
        d.pivot_table(index="year", columns="Name", values=value_col, aggfunc="sum")
        .fillna(0)
        .astype(int)
    )
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"
    return pivot

def deaths_national_series(total_df: pd.DataFrame) -> pd.Series:
    s = total_df.set_index("Fecha")["total"].astype(float)
    s.index = s.index.astype(int)
    return s

def deaths_gender_pivot(total_df: pd.DataFrame) -> tuple:
    cols = {f"Total_{es}": en for es, en in DEATHS_GENDER_EN.items()}
    df = total_df.set_index("Fecha")[list(cols)].astype(int).rename(columns=cols)
    df.index = df.index.astype(int)
    df.index.name = "Year"
    return df, ["Deaths by gender", "Year", "Deaths"]

def deaths_gender_cause_pivot(dept_df: pd.DataFrame, cause: str) -> tuple:
    df = dept_df[dept_df["cause"] == cause]
    cols = {f"Total_{es}": en for es, en in DEATHS_GENDER_EN.items()}
    out = df.groupby("Fecha")[list(cols)].sum().astype(int).rename(columns=cols)
    out.index = out.index.astype(int)
    out.index.name = "Year"
    return out, [f"Deaths by gender — {cause}", "Year", "Deaths"]

def deaths_area_pivot(area_df: pd.DataFrame, age_label: str = "All ages") -> tuple:
    df = area_df.copy()
    df["age"] = df["grupo_edad"].map(DEATHS_AGE_EN).fillna(df["grupo_edad"])
    title = "Deaths by area"
    if age_label and age_label != "All ages":
        df = df[df["age"] == age_label]
        title += f" — age {age_label}"
    out = pd.DataFrame(index=sorted(df["Fecha"].unique()))
    for es, en in AREA_EN.items():
        gender_cols = [f"{es}_{g}" for g in DEATHS_GENDER_EN]
        out[en] = df.groupby("Fecha")[gender_cols].sum().sum(axis=1).astype(int)
    out.index = out.index.astype(int)
    out.index.name = "Year"
    return out, [title, "Year", "Deaths"]

def deaths_age_pivot(area_df: pd.DataFrame, gender: str = "Total", area: str = "Total") -> tuple:
    df = area_df.copy()
    df["age"] = df["grupo_edad"].map(DEATHS_AGE_EN).fillna(df["grupo_edad"])

    area_es = find_key_by_value(AREA_EN, area)  # None when area == "Total"
    gender_es = find_key_by_value(DEATHS_GENDER_EN, gender)  # None when gender == "Total"

    if area == "Total" and gender == "Total":
        df["val"] = df["total"]
    elif area == "Total":
        df["val"] = df[f"Total_{gender_es}"]
    elif gender == "Total":
        df["val"] = df[[f"{area_es}_{g}" for g in DEATHS_GENDER_EN]].sum(axis=1)
    else:
        df["val"] = df[f"{area_es}_{gender_es}"]

    pivot = df.pivot_table(index="Fecha", columns="age", values="val", aggfunc="sum").astype(int)
    order = list(dict.fromkeys(DEATHS_AGE_EN.values()))  # dedupe typo collisions, keep order
    pivot = pivot[[c for c in order if c in pivot.columns]]
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"

    parts = [p for p in (None if area == "Total" else area, None if gender == "Total" else gender) if p]
    title = "Deaths by age group" + (f" — {', '.join(parts)}" if parts else "")
    return pivot, [title, "Year", "Deaths"]

def _cause_label(causa: pd.Series) -> pd.Series:
    """Strip the leading NNN code, then map to English (accent-variants collapse to one)."""
    stripped = causa.astype(str).str.replace(r"^\d+\s+", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    return stripped.map(lambda s: CAUSE_EN.get(norm(s), s))

@st.cache_data
def deaths_dept_prepared(path) -> pd.DataFrame:
    df = load_csv(path)
    df = df[~df["departamento"].str.strip().str.lower().eq("total nacional")].copy()
    df["Name"] = df["departamento"].str.split(n=1).str[1]
    df["cause"] = _cause_label(df["causa"])
    return df

def _dept_filter(dept_df: pd.DataFrame, years: list, president: str, dept_name: str = None) -> pd.DataFrame:
    df = dept_df
    if dept_name and dept_name != "All":
        df = df[df["Name"] == dept_name]
    if president:
        df = df[df["Fecha"].isin(presidents[president])]
    elif years:
        df = df[df["Fecha"].isin(years)]
    return df

def deaths_age_gender_value(df: pd.DataFrame, gender: str, age_label: str) -> pd.Series:
    """Series of deaths for a (gender, age) combo from dept×cause frames (cols: total, Total_<gender>, <age>_<gender>)."""
    genders = list(DEATHS_GENDER_EN) if gender == "Total" else [find_key_by_value(DEATHS_GENDER_EN, gender)]
    if not age_label or age_label == "All ages":
        return df["total"] if gender == "Total" else df[f"Total_{genders[0]}"]
    age_keys = [k for k, v in DEATHS_AGE_EN.items() if v == age_label]
    cols = [f"{a}_{g}" for a in age_keys for g in genders if f"{a}_{g}" in df.columns]
    return df[cols].sum(axis=1)

def deaths_top_causes(dept_df: pd.DataFrame, years: list, dept_name: str, president: str, value_col: str = "total") -> pd.Series:
    df = _dept_filter(dept_df, years, president, dept_name)
    return df.groupby("cause")[value_col].sum().astype(int).nlargest(5)

def deaths_cause_pivot(dept_df: pd.DataFrame, selected_causes: list, years: list, president: str, value_col: str = "total", dept_name: str = "All") -> pd.DataFrame:
    df = _dept_filter(dept_df, years, president, dept_name)
    df = df[df["cause"].isin(selected_causes)]
    pivot = (
        df.pivot_table(index="Fecha", columns="cause", values=value_col, aggfunc="sum")
        .fillna(0)
        .astype(int)
    )
    pivot.index = pivot.index.astype(int)
    pivot.index.name = "Year"
    return pivot

def deaths_cause_names(dept_df: pd.DataFrame) -> list:
    return sorted(dept_df["cause"].unique())
