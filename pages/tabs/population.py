import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.macro import macro_functions as mf
from generalities.dictionaries import presidents, months
from generalities.function import get_valid_presidents, show_all_years, to_datatime, find_key_by_value
from generalities.migration import COUNTRY_EN, METRIC_LABEL, VIEW

MIGRATION_PATH = "./data/datos_abiertos/migration.csv"

def render_population(pop_df: pd.DataFrame) -> None:
    with st.sidebar:
        view = st.radio("View:", VIEW)

    if view == VIEW[0]:
        _render_population_tab(pop_df)
    else:
        _render_migration_tab()

def _render_population_tab(pop_df: pd.DataFrame) -> None:
    pop_local = to_datatime(pop_df, True)
    pop_local.index = pop_local.index.year.astype(int)

    st.title("Population")

    metric = "Absolute"

    col1, col2 = st.columns(2)

    with col1:
        method = st.selectbox("Method:", ["Total", "Growth"])

    if method == "Growth":
        with col2:
            metric = st.selectbox("Metric", ["Absolute", "Percentage"])

        if metric == "Percentage":
            series = round(pop_local["Población"].pct_change() * 100, 2)
            info = ["Annual Population Growth", "Year", "%"]
        else:
            series = pop_local["Población"].diff()
            info = ["Annual Population Growth", "Year", "New People"]

        column = "Growth"
        years = pop_local.index[1:]
    else:
        series = pop_local["Población"]
        info = ["Population", "Year", "People"]
        column = "Population"
        years = pop_local.index

    full_series = series

    with st.sidebar:
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])
        valid_presidents = get_valid_presidents(years)
        president = st.selectbox("President:", valid_presidents, index=None)

        if president:
            pres_years = [y for y in years if y in presidents[president]]
            choice_year = st.multiselect("Year:", sorted(pres_years, reverse=True), key="pop_year")
        else:
            choice_year = st.multiselect("Year:", sorted(years, reverse=True), key="pop_year")

    series = show_all_years(series, president)

    if president:
        series = series[series.index.isin(presidents[president])]

    if choice_year:
        series = series[series.index.isin(choice_year)]

    series = series.dropna()

    if series.empty:
        st.warning("Remember to select 'Show all years' to see info about years prior to 2000")
        return

    data = series.to_frame(name=column)

    if len(data) == 1:
        year = data.index[0]
        if method == "Growth":
            reference = full_series.median()
            
            if metric == "Absolute":
                gauge_info = [f"Absolute {year} Population Growth", ",.0f", "", " vs Median"]
            else:
                gauge_info = [f"{year} Population Growth", ".2f", "%", " vs Median"]
        else:
            reference = full_series.get(year - 1)
            if pd.isna(reference):
                reference = full_series.median()
            gauge_info = [f"{year} Population", ",.0f", "", " vs Prior Year"]

        fig = mc.indicator(data, full_series, reference, gauge_info)
    elif chart_type == "Bar":
        fig = mc.bar_chart(data, {}, info)
    else:
        fig = mc.line_chart(data, {}, info)

    st.plotly_chart(fig)
    st.caption("Source: Banco de la República")
    st.info("If you want to choose a year prior to 2000, make sure you click 'Show all years'")


def _render_migration_tab() -> None:
    migration_df = mf.load_migration(MIGRATION_PATH)

    st.title("Population")

    with st.sidebar:
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Map", "Line", "Bar"])

    all_years = sorted(migration_df["Fecha"].dt.year.unique().tolist(), reverse=True)
    valid_pres = get_valid_presidents(all_years)

    if chart_type == "Map":
        _render_map(migration_df, all_years)
    else:
        _render_line_bar(migration_df, chart_type, all_years, valid_pres)

    st.caption("Inbound is foreing people coming into Colombia. Outbound is colombians leaving the country.")
    st.caption("Source: Migración Colombia")


def _render_map(migration_df, all_years):
    col1, col2, col3 = st.columns(3)

    with col1:
        direction = st.selectbox("Direction:", ["Inbound", "Outbound"], key="mig_direction")
    with col2:
        metric = st.selectbox("Metric:", ["Total", "Female", "Male"], key="mig_metric")
    with col3:
        year_sel = st.selectbox("Year:", ["All"] + all_years, index=0)
        year = None if year_sel == "All" else year_sel

    data_col = mf.COL_MAP[(direction, metric)]
    label = METRIC_LABEL[metric]
    meta = [direction, metric, label]

    with st.sidebar:
        month_opts = ["All"] + list(months.values())
        month_name = st.selectbox("Month:", month_opts, index=0)

    grouped, title = mf.build_migration_map_data(migration_df, year, month_name, data_col, meta)

    if grouped.empty:
        st.warning("No data for selected filters.")
    else:
        fig = mc.choropleth_map(grouped, data_col, [title, "Country", label])
        st.plotly_chart(fig)


def _render_line_bar(migration_df, chart_type, all_years, valid_pres):
    compare_by = st.session_state.get("mig_compare", "Countries")

    with st.sidebar:
        president = st.selectbox(
            "President:", [None] + valid_pres,
            format_func=lambda x: x or "All",
        )

    year_opts = [y for y in all_years if y in presidents[president]] if president else all_years

    direction = "Inbound"
    metric = "Total"

    c1, c2, c3 = st.columns(3)

    if compare_by == "Direction":
        with c1:
            metric = st.selectbox("Metric:", ["Total", "Female", "Male"], key="mig_metric")
        with c2:
            selected_years = st.multiselect("Year:", year_opts, key="mig_years")
    elif compare_by == "Gender":
        with c1:
            direction = st.selectbox("Direction:", ["Inbound", "Outbound"], key="mig_direction")
        with c2:
            selected_years = st.multiselect("Year:", year_opts, key="mig_years")
    else:  # Countries or Year
        with c1:
            direction = st.selectbox("Direction:", ["Inbound", "Outbound"], key="mig_direction")
        with c2:
            metric = st.selectbox("Metric:", ["Total", "Female", "Male"], key="mig_metric")
        with c3:
            if compare_by == "Year":
                default_year = 2019
                selected_years = st.multiselect("Year:", year_opts, default=default_year)
            else:
                selected_years = st.multiselect("Year:", year_opts, key="mig_years")

    label = METRIC_LABEL[metric]
    data_col = mf.COL_MAP[(direction, metric)]
    meta = [direction, metric, label]

    df_f = migration_df.copy()

    if president:
        df_f = df_f[df_f["Fecha"].dt.year.isin(presidents[president])]
    if selected_years:
        df_f = df_f[df_f["Fecha"].dt.year.isin(selected_years)]

    if compare_by == "Year":
        all_countries_es = [c for c in sorted(migration_df["País"].unique()) if c in COUNTRY_EN]
        all_countries_en = sorted([COUNTRY_EN[c] for c in all_countries_es])

        with st.sidebar:
            country_en = st.selectbox("Country:", ["All"] + all_countries_en)

        if country_en != "All":
            country_es = find_key_by_value(COUNTRY_EN, country_en)
            df_f = df_f[df_f["País"] == country_es]
            meta = [direction, metric, label, country_en]

        pivot, info = mf.migration_year_pivot(df_f, data_col, meta)
        force_bar = False
    else:
        annual_mode = len(selected_years) != 1

        if annual_mode:
            df_f = df_f.copy()
            df_f["Period"] = df_f["Fecha"].dt.year.astype(str)
            period_label = "Year"
        else:
            df_f = df_f[df_f["Fecha"].dt.year == selected_years[0]].copy()
            df_f["Period"] = df_f["Fecha"].dt.strftime("%Y-%m")
            period_label = "Month"

        all_countries_es = [c for c in sorted(df_f["País"].unique()) if c in COUNTRY_EN]
        all_countries_en = sorted([COUNTRY_EN[c] for c in all_countries_es])

        if compare_by == "Countries":
            pivot, info = mf.migration_countries_pivot(df_f, all_countries_en, data_col, period_label, meta)
        else:  # Direction or Gender
            pivot, info = mf.migration_single_pivot(df_f, all_countries_en, compare_by, meta, period_label)

        force_bar = not annual_mode and len(pivot) == 1 if pivot is not None else False

    highlight = None

    if pivot is not None and not pivot.empty and len(pivot.columns) > 1:
        with st.sidebar:
            display_names = list(pivot.columns.astype(str))
            highlight_choice = st.selectbox(
                "Highlight variable:", ["—"] + display_names,
            )
            highlight = None if highlight_choice == "—" else highlight_choice

    compare_placeholder = st.sidebar.empty()

    if pivot is None or pivot.empty:
        with compare_placeholder:
            st.radio(
                "Compare by:", ["Countries", "Direction", "Gender", "Year"],
                horizontal=True, key="mig_compare",
            )
        return

    if pivot.empty:
        st.warning("No data for selected filters.")
        st.stop()

    if chart_type == "Bar" or force_bar or len(pivot) == 1:
        fig = mc.bar_chart(pivot, {}, info, highlight=highlight)
    else:
        fig = mc.line_chart(pivot, {}, info, highlight=highlight)

    st.plotly_chart(fig)

    with compare_placeholder:
        st.radio(
            "Compare by:", ["Countries", "Direction", "Gender", "Year"],
            horizontal=True, key="mig_compare",
        )
