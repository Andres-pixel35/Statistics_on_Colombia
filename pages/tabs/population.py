import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.macro import macro_functions as mf
from generalities.dictionaries import presidents, months
from generalities.function import get_valid_presidents, show_all_years, to_datatime, find_key_by_value, president_multiselect, reshape_by_presidents, load_csv, load_geojson, BASE_DIR
from generalities.migration import COUNTRY_EN, METRIC_LABEL, VIEW
from generalities.births import BIRTHS_PATHS, BIRTHS_COMPARE, AGE_EN, DEPT_GEOJSON_PATH, DEPT_FEATURE_KEY

MIGRATION_PATH = BASE_DIR / "data/datos_abiertos/migration.csv"
NET_MIGRATION_PATH = BASE_DIR / "data/world_bank/net_migration.csv"

def render_population(pop_df: pd.DataFrame) -> None:
    with st.sidebar:
        view = st.radio("View:", VIEW)

    if view == VIEW[0]:
        _render_population_tab(pop_df)
    elif view == VIEW[1]:
        _render_migration_tab()
    else:
        _render_births_tab()

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
        with col2:
            perspective = st.selectbox("Perspective:", ["National", "Net Migration", "Births"])

        if perspective == "Net Migration":
            net_migration = load_csv(NET_MIGRATION_PATH)

            years = net_migration["Fecha"]
            series = net_migration["Migration"].astype(int)
            series.index = years
        elif perspective == "Births":
            series = mf.births_national_series(load_csv(BIRTHS_PATHS["total"]))
            years = series.index
        else:
            series = pop_local["Población"]
            years = pop_local.index

        a = "Population" if perspective == "National" else f"{perspective}"

        info = [a, "Year", "People" if perspective != "Births" else "Births"]
        column = f"{a}"

    source = (
        "World Bank" if method == "Total" and perspective == "Net Migration"
        else "DANE" if method == "Total" and perspective == "Births"
        else "Banco de la República"
    )

    full_series = series

    with st.sidebar:
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])
        valid_presidents = get_valid_presidents(years)
        selected_presidents = president_multiselect(valid_presidents)
        comparing = len(selected_presidents) >= 2
        president = selected_presidents[0] if len(selected_presidents) == 1 else None 

        if comparing:
            choice_year = []
        elif president:
            pres_years = [y for y in years if y in presidents[president]]
            choice_year = st.multiselect("Year:", sorted(pres_years, reverse=True))
        else:
            choice_year = st.multiselect("Year:", sorted(years, reverse=True))

        compare_births = compare_migration = False
        if method == "Growth" and metric == "Absolute" and not comparing:
            compare_births = st.checkbox("Compare with Births")
            compare_migration = st.checkbox("Compare with Net Migration")

    extras = []
    if compare_births:
        b = mf.births_national_series(load_csv(BIRTHS_PATHS["total"]))
        b.name = "Births"
        extras.append(b)
    if compare_migration:
        m = load_csv(NET_MIGRATION_PATH).set_index("Fecha")["Migration"].astype(int)
        m.name = "Net Migration"
        extras.append(m)
    if extras:
        series = pd.concat([series.rename(column)] + extras, axis=1)
        suffixes = (["Births"] if compare_births else []) + (["Net Migration"] if compare_migration else [])
        info[0] = f"{info[0]} vs {' & '.join(suffixes)}"

    if comparing:
        data, info = reshape_by_presidents(full_series.to_frame(name=column), selected_presidents, info)
        fig = mc.bar_chart(data, {}, info) if chart_type == "Bar" else mc.line_chart(data, {}, info)
        st.plotly_chart(fig)
        st.caption(f"Source: {source}")
        return

    if source != "DANE":
        series = show_all_years(series, president)

    if president:
        series = series[series.index.isin(presidents[president])]

    if choice_year:
        series = series[series.index.isin(choice_year)]

    series = series.dropna(how="all") if isinstance(series, pd.DataFrame) else series.dropna()

    if series.empty:
        st.warning("Remember to select 'Show all years' to see info about years prior to 2000")
        return

    data = series if isinstance(series, pd.DataFrame) else series.to_frame(name=column)

    if len(data) == 1 and data.shape[1] == 1:
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

    if source == "World Bank":
        st.caption("Net migration is the net total of migrants during the period, that is, the number of immigrants minus the number of emigrants, including both citizens and noncitizens.")

    st.caption(f"Source: {source}")

    if extras:
        st.caption("Births: DANE · Net migration: World Bank")

    if source != "DANE":
        st.info("If you want to choose a year prior to 2000, make sure you click 'Show all years'")


def _render_migration_tab() -> None:
    migration_df = load_csv(MIGRATION_PATH)
    migration_df["Fecha"] = pd.to_datetime(migration_df["Fecha"])

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
        direction = st.selectbox("Direction:", ["Inbound", "Outbound"])
    with col2:
        metric = st.selectbox("Metric:", ["Total", "Female", "Male"])
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
        selected_presidents = president_multiselect(valid_pres)

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    pres_compare = comparing and compare_by in ("Countries", "Direction", "Gender")

    year_opts = [y for y in all_years if y in presidents[president]] if president else all_years

    direction = "Inbound"
    metric = "Total"

    c1, c2, c3 = st.columns(3)

    if compare_by == "Direction":
        with c1:
            metric = st.selectbox("Metric:", ["Total", "Female", "Male"])
        with c2:
            selected_years = [] if pres_compare else st.multiselect("Year:", year_opts)
    elif compare_by == "Gender":
        with c1:
            direction = st.selectbox("Direction:", ["Inbound", "Outbound"])
        with c2:
            selected_years = [] if pres_compare else st.multiselect("Year:", year_opts)
    else:  # Countries or Year
        with c1:
            direction = st.selectbox("Direction:", ["Inbound", "Outbound"])
        with c2:
            metric = st.selectbox("Metric:", ["Total", "Female", "Male"])
        with c3:
            if compare_by == "Year":
                selected_years = st.multiselect("Year:", year_opts)
            else:
                selected_years = [] if pres_compare else st.multiselect("Year:", year_opts)

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

    if pres_compare and pivot is not None and not pivot.empty:
        pivot, info = reshape_by_presidents(pivot, selected_presidents, info)

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


def _render_births_tab() -> None:
    st.title("Births")

    compare_by = st.session_state.get("births_compare", BIRTHS_COMPARE[0])

    with st.sidebar:
        st.header("Filters")

    if compare_by == "Department":
        _render_births_department()
    elif compare_by == "Municipality":
        _render_births_municipality()
    else:
        _render_births_breakdown(compare_by)

    with st.sidebar:
        st.radio("Compare by:", BIRTHS_COMPARE, horizontal=True, key="births_compare")

    st.caption("Source: DANE")


def _render_births_breakdown(compare_by: str) -> None:
    if compare_by == "Gender":
        df = load_csv(BIRTHS_PATHS["total"])
    elif compare_by == "Mother Age":
        df = load_csv(BIRTHS_PATHS["age"])
    else:  # Education
        df = load_csv(BIRTHS_PATHS["education"])

    years = sorted(df["year"].unique().astype(int).tolist(), reverse=True)
    valid_presidents = get_valid_presidents(years)

    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])
        selected_presidents = president_multiselect(valid_presidents)

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    year_opts = [y for y in years if y in presidents[president]] if president else years

    age_label = None
    if compare_by == "Education":
        present = [AGE_EN.get(a, a) for a in df["grupo_edad"].unique()]
        age_opts = ["All ages"] + [v for v in AGE_EN.values() if v in present]
        with st.sidebar:
            age_label = st.selectbox("Mother age:", age_opts)

    with st.sidebar:
        selected_years = [] if comparing else st.multiselect("Year:", year_opts)

    if compare_by == "Gender":
        pivot, info = mf.births_gender_pivot(df)
    elif compare_by == "Mother Age":
        pivot, info = mf.births_age_pivot(df)
        with st.sidebar:
            chosen = st.multiselect("Age groups:", list(pivot.columns))
        if chosen:
            pivot = pivot[chosen]
    else:
        pivot, info = mf.births_education_pivot(df, age_label)
        with st.sidebar:
            chosen = st.multiselect("Education levels:", list(pivot.columns))
        if chosen:
            pivot = pivot[chosen]

    if president:
        pivot = pivot[pivot.index.isin(presidents[president])]
    elif selected_years:
        pivot = pivot[pivot.index.isin(selected_years)]

    if comparing and not pivot.empty:
        pivot, info = reshape_by_presidents(pivot, selected_presidents, info)

    if pivot.empty:
        st.warning("No data for selected filters.")
        return

    highlight = None
    if len(pivot.columns) > 1:
        with st.sidebar:
            names = list(pivot.columns.astype(str))
            choice = st.selectbox("Highlight variable:", ["—"] + names)
            highlight = None if choice == "—" else choice

    if chart_type == "Bar" or len(pivot) == 1:
        fig = mc.bar_chart(pivot, {}, info, highlight=highlight)
    else:
        fig = mc.line_chart(pivot, {}, info, highlight=highlight)

    st.plotly_chart(fig)


def _render_births_department() -> None:
    dept_df = load_csv(BIRTHS_PATHS["department"])
    all_years = sorted(dept_df["year"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["departamento"].str.split(n=1).str[1].unique())

    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", ["Map", "Line", "Bar"])

        if chart_type != "Map":
            selected_depts = st.multiselect("Departments:", dept_names)

        selected_years = st.multiselect("Year:", all_years)

    scope = "all years" if not selected_years else ", ".join(map(str, sorted(selected_years)))

    if chart_type == "Map":
        grouped = mf.births_department_data(dept_df, selected_years, "total")
        info = [f"Births by department — {scope}", "Department", "Births"]
        geojson = load_geojson(DEPT_GEOJSON_PATH)
        fig = mc.colombia_choropleth(grouped, geojson, DEPT_FEATURE_KEY, "total", info)
        st.plotly_chart(fig)
        return

    if not selected_depts:
        st.info("Select one or more departments.")
        return

    pivot = mf.births_geo_trend(dept_df, "departamento", selected_depts, selected_years)
    _render_geo_bar_line(pivot, chart_type, "department", scope)


def _render_births_municipality() -> None:
    muni_df = load_csv(BIRTHS_PATHS["municipality"])
    all_years = sorted(muni_df["year"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(muni_df["departamento"].str.split(n=1).str[1].dropna().unique())

    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])
        dept = st.selectbox("Department:", dept_names)
        scoped = muni_df[muni_df["departamento"].str.split(n=1).str[1] == dept]
        muni_names = sorted(scoped["municipio"].str.split(n=1).str[1].unique())
        selected_munis = st.multiselect("Municipios:", muni_names)
        selected_years = st.multiselect("Year:", all_years)

    if not selected_munis:
        st.info("Select one or more municipios.")
        return

    scope = "all years" if not selected_years else ", ".join(map(str, sorted(selected_years)))
    pivot = mf.births_geo_trend(scoped, "municipio", selected_munis, selected_years)
    _render_geo_bar_line(pivot, chart_type, "municipio", scope)


def _render_geo_bar_line(pivot, chart_type: str, entity: str, scope: str) -> None:
    if pivot.empty:
        st.warning("No data for selected filters.")
        return

    if chart_type == "Bar" or len(pivot) == 1:
        info = [f"Total births by {entity} — {scope}", "Births", entity.capitalize()]
        fig = mc.ranked_bar_chart(pivot.sum(axis=0), info)
    else:
        highlight = None
        if len(pivot.columns) > 1:
            with st.sidebar:
                choice = st.selectbox("Highlight variable:", ["—"] + list(pivot.columns))
                highlight = None if choice == "—" else choice
        info = [f"Births trend by {entity}", "Year", "Births"]
        fig = mc.line_chart(pivot, {}, info, highlight=highlight)

    st.plotly_chart(fig)
