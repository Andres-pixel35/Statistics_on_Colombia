import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.macro import macro_functions as mf
from generalities.dictionaries import presidents, months
from generalities.function import get_valid_presidents, show_all_years, to_datatime, find_key_by_value, president_multiselect, reshape_by_presidents, load_csv, load_geojson, BASE_DIR
from generalities.migration import COUNTRY_EN, METRIC_LABEL, VIEW
from generalities.births import BIRTHS_PATHS, BIRTHS_COMPARE, AGE_EN, GENDER_EN, DEPT_GEOJSON_PATH, DEPT_FEATURE_KEY
from generalities.deaths import DEATHS_PATHS, DEATHS_COMPARE, AREA_EN, AGE_EN as DEATHS_AGE_EN, GENDER_EN as DEATHS_GENDER_EN

MIGRATION_PATH = BASE_DIR / "data/datos_abiertos/migration.csv"
NET_MIGRATION_PATH = BASE_DIR / "data/world_bank/net_migration.csv"

def render_population(pop_df: pd.DataFrame) -> None:
    with st.sidebar:
        view = st.radio("View:", VIEW)

    if view == VIEW[0]:
        _render_population_tab(pop_df)
    elif view == VIEW[1]:
        _render_migration_tab()
    elif view == VIEW[2]:
        _render_births_tab()
    else:
        _render_deaths_tab()

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
            perspective = st.selectbox("Perspective:", ["National", "Net Migration", "Births", "Deaths"])

        if perspective == "Net Migration":
            net_migration = load_csv(NET_MIGRATION_PATH)

            years = net_migration["Fecha"]
            series = net_migration["Migration"].astype(int)
            series.index = years
        elif perspective == "Births":
            series = mf.births_national_series(load_csv(BIRTHS_PATHS["total"]))
            years = series.index
        elif perspective == "Deaths":
            series = mf.deaths_national_series(load_csv(DEATHS_PATHS["total"]))
            years = series.index
        else:
            series = pop_local["Población"]
            years = pop_local.index

        a = "Population" if perspective == "National" else f"{perspective}"

        unit = {"Births": "Births", "Deaths": "Deaths"}.get(perspective, "People")
        info = [a, "Year", unit]
        column = f"{a}"

    source = (
        "World Bank" if method == "Total" and perspective == "Net Migration"
        else "DANE" if method == "Total" and perspective in ("Births", "Deaths")
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

        compare_births = compare_migration = compare_deaths = False
        if method == "Growth" and metric == "Absolute" and not comparing:
            compare_births = st.checkbox("Compare with Births")
            compare_migration = st.checkbox("Compare with Net Migration")
            compare_deaths = st.checkbox("Compare with Deaths")
        elif method == "Total" and not comparing:
            if perspective == "Births":
                compare_deaths = st.checkbox("Compare with Deaths")
            elif perspective == "Deaths":
                compare_births = st.checkbox("Compare with Births")

    extras = []
    if compare_births:
        b = mf.births_national_series(load_csv(BIRTHS_PATHS["total"]))
        b.name = "Births"
        extras.append(b)
    if compare_migration:
        m = load_csv(NET_MIGRATION_PATH).set_index("Fecha")["Migration"].astype(int)
        m.name = "Net Migration"
        extras.append(m)
    if compare_deaths:
        d = mf.deaths_national_series(load_csv(DEATHS_PATHS["total"]))
        d.name = "Deaths"
        extras.append(d)
    if extras:
        series = pd.concat([series.rename(column)] + extras, axis=1)
        suffixes = (["Births"] if compare_births else []) + (["Net Migration"] if compare_migration else []) + (["Deaths"] if compare_deaths else [])
        info[0] = f"{info[0]} vs {' & '.join(suffixes)}"

    if comparing:
        data, info = reshape_by_presidents(full_series.to_frame(name=column), selected_presidents, info)
        fig = mc.bar_chart(data, {}, info) if chart_type == "Bar" else mc.line_chart(data, {}, info)
        mc.render_chart(fig)
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

    mc.render_chart(fig)

    if source == "World Bank":
        st.caption("Net migration is the net total of migrants during the period, that is, the number of immigrants minus the number of emigrants, including both citizens and noncitizens.")

    st.caption(f"Source: {source}")

    if extras:
        st.caption("Births & deaths: DANE · Net migration: World Bank")

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
        mc.render_chart(fig)


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

    mc.render_chart(fig)

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

    mc.render_chart(fig)


def _render_births_department() -> None:
    dept_df = load_csv(BIRTHS_PATHS["department"])
    all_years = sorted(dept_df["year"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["departamento"].str.split(n=1).str[1].unique())

    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", ["Map", "Line", "Bar"])

        if chart_type != "Map":
            selected_depts = st.multiselect("Departments:", dept_names)

        gender = st.selectbox("Gender:", ["Total", "Boys", "Girls"])
        selected_years = st.multiselect("Year:", all_years)

    col = "total" if gender == "Total" else find_key_by_value(GENDER_EN, gender)
    noun = "Births" if gender == "Total" else gender
    scope = "all years" if not selected_years else ", ".join(map(str, sorted(selected_years)))

    if chart_type == "Map":
        grouped = mf.births_department_data(dept_df, selected_years, col)
        info = [f"{noun} by department — {scope}", "Department", noun]
        geojson = load_geojson(DEPT_GEOJSON_PATH)
        fig = mc.colombia_choropleth(grouped, geojson, DEPT_FEATURE_KEY, col, info)
        mc.render_chart(fig)
        return

    if not selected_depts:
        st.info("Select one or more departments.")
        return

    pivot = mf.births_geo_trend(dept_df, "departamento", selected_depts, selected_years, value_col=col)
    _render_geo_bar_line(pivot, chart_type, "department", scope, noun=noun)


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


def _render_geo_bar_line(pivot, chart_type: str, entity: str, scope: str, noun: str = "Births") -> None:
    if pivot.empty:
        st.warning("No data for selected filters.")
        return

    if chart_type == "Bar" or len(pivot) == 1:
        info = [f"Total {noun.lower()} by {entity} — {scope}", noun, entity.capitalize()]
        fig = mc.ranked_bar_chart(pivot.sum(axis=0), info)
    else:
        highlight = None
        if len(pivot.columns) > 1:
            with st.sidebar:
                choice = st.selectbox("Highlight variable:", ["—"] + list(pivot.columns))
                highlight = None if choice == "—" else choice
        info = [f"{noun} trend by {entity}", "Year", noun]
        fig = mc.line_chart(pivot, {}, info, highlight=highlight)

    mc.render_chart(fig)


def _render_deaths_tab() -> None:
    st.title("Deaths")

    compare_by = st.session_state.get("deaths_compare", DEATHS_COMPARE[0])

    with st.sidebar:
        st.header("Filters")

    if compare_by == "Department":
        _render_deaths_department()
    elif compare_by == "Cause (Top 5)":
        _render_deaths_top_causes()
    elif compare_by == "Cause (Compare)":
        _render_deaths_cause_compare()
    else:
        _render_deaths_breakdown(compare_by)

    with st.sidebar:
        st.radio("Compare by:", DEATHS_COMPARE, horizontal=True, key="deaths_compare")

    st.caption("Source: DANE")


def _render_deaths_breakdown(compare_by: str) -> None:
    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])

    gender_cause = None
    dept_df = None
    if compare_by == "Gender":
        cause_names = mf.deaths_cause_names(load_csv(DEATHS_PATHS["dept_death"]))
        with st.sidebar:
            gender_cause = st.selectbox("Cause:", ["All causes"] + cause_names)
        if gender_cause == "All causes":
            df = load_csv(DEATHS_PATHS["total"])
        else:
            dept_df = load_csv(DEATHS_PATHS["dept_death"])
            df = dept_df
    else:
        df = load_csv(DEATHS_PATHS["area_age"])

    years = sorted(df["Fecha"].unique().astype(int).tolist(), reverse=True)
    valid_presidents = get_valid_presidents(years)

    with st.sidebar:
        selected_presidents = president_multiselect(valid_presidents)

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    year_opts = [y for y in years if y in presidents[president]] if president else years

    with st.sidebar:
        selected_years = [] if comparing else st.multiselect("Year:", year_opts)

    age_labels = list(dict.fromkeys(DEATHS_AGE_EN.values()))

    if compare_by == "Gender":
        if gender_cause == "All causes":
            pivot, info = mf.deaths_gender_pivot(df)
        else:
            pivot, info = mf.deaths_gender_cause_pivot(dept_df, gender_cause)
    elif compare_by == "Area":
        with st.sidebar:
            age_label = st.selectbox("Age group:", ["All ages"] + age_labels)
        pivot, info = mf.deaths_area_pivot(df, age_label)
    else:  # Age Group
        with st.sidebar:
            gender = st.selectbox("Gender:", ["Total", "Men", "Women"])
            area = st.selectbox("Area:", ["Total"] + list(AREA_EN.values()))
        pivot, info = mf.deaths_age_pivot(df, gender, area)
        with st.sidebar:
            chosen = st.multiselect("Age groups:", list(pivot.columns))
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

    mc.render_chart(fig)


def _deaths_dept_source():
    with st.sidebar:
        place = st.selectbox("Place:", ["Occurrence", "Residence"])
    path = DEATHS_PATHS["dept_death"] if place == "Occurrence" else DEATHS_PATHS["dept_residence"]
    return load_csv(path)


def _render_deaths_department() -> None:
    dept_df = _deaths_dept_source().rename(columns={"Fecha": "year"})
    dept_df = dept_df[~dept_df["departamento"].str.strip().str.lower().eq("total nacional")]

    all_years = sorted(dept_df["year"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["departamento"].str.split(n=1).str[1].dropna().unique())

    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", ["Map", "Line", "Bar"])

        if chart_type != "Map":
            selected_depts = st.multiselect("Departments:", dept_names)

        gender = st.selectbox("Gender:", ["Total", "Men", "Women"])
        selected_years = st.multiselect("Year:", all_years)

    col = "total" if gender == "Total" else f"Total_{find_key_by_value(DEATHS_GENDER_EN, gender)}"
    noun = "Deaths" if gender == "Total" else gender
    scope = "all years" if not selected_years else ", ".join(map(str, sorted(selected_years)))

    if chart_type == "Map":
        grouped = mf.births_department_data(dept_df, selected_years, col)
        info = [f"{noun} by department — {scope}", "Department", noun]
        geojson = load_geojson(DEPT_GEOJSON_PATH)
        fig = mc.colombia_choropleth(grouped, geojson, DEPT_FEATURE_KEY, col, info)
        mc.render_chart(fig)
        return

    if not selected_depts:
        st.info("Select one or more departments.")
        return

    pivot = mf.births_geo_trend(dept_df, "departamento", selected_depts, selected_years, value_col=col)
    _render_geo_bar_line(pivot, chart_type, "department", scope, noun=noun)


def _render_deaths_top_causes() -> None:
    dept_df = _deaths_dept_source()
    no_nat = dept_df[~dept_df["departamento"].str.strip().str.lower().eq("total nacional")]

    all_years = sorted(no_nat["Fecha"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(no_nat["departamento"].str.split(n=1).str[1].dropna().unique())
    valid_presidents = get_valid_presidents(all_years)

    with st.sidebar:
        opts = ["All"] + dept_names
        saved = st.session_state.get("deaths_cause_dept", "All")
        idx = opts.index(saved) if saved in opts else 0
        dept = st.selectbox("Department:", opts, index=idx)
        st.session_state["deaths_cause_dept"] = dept
        gender = st.selectbox("Gender:", ["Total", "Men", "Women"])
        selected_presidents = president_multiselect(valid_presidents)
        president = selected_presidents[0] if len(selected_presidents) == 1 else None
        year_opts = [y for y in all_years if y in presidents[president]] if president else all_years
        selected_years = [] if president else st.multiselect("Year:", year_opts)

    col = "total" if gender == "Total" else f"Total_{find_key_by_value(DEATHS_GENDER_EN, gender)}"
    series = mf.deaths_top_causes(dept_df, selected_years, dept, president, value_col=col)

    if series.empty:
        st.warning("No data for selected filters.")
        return

    scope = ", ".join(map(str, sorted(selected_years))) if selected_years else (president or "all years")
    place = dept if dept != "All" else "Colombia"
    g = "" if gender == "Total" else f" ({gender})"
    info = [f"Top 5 causes of death{g} — {place}, {scope}", "Deaths", "Cause"]
    fig = mc.ranked_bar_chart(series, info)
    mc.render_chart(fig)


def _render_deaths_cause_compare() -> None:
    dept_df = _deaths_dept_source()
    no_nat = dept_df[~dept_df["departamento"].str.strip().str.lower().eq("total nacional")]

    all_years = sorted(no_nat["Fecha"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(no_nat["departamento"].str.split(n=1).str[1].dropna().unique())
    valid_presidents = get_valid_presidents(all_years)
    cause_names = mf.deaths_cause_names(dept_df)

    with st.sidebar:
        opts = ["All"] + dept_names
        saved = st.session_state.get("deaths_cause_dept", "All")
        idx = opts.index(saved) if saved in opts else 0
        dept = st.selectbox("Department:", opts, index=idx)
        st.session_state["deaths_cause_dept"] = dept
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])
        selected_causes = st.multiselect("Causes (max 5):", cause_names)
        gender = st.selectbox("Gender:", ["Total", "Men", "Women"])
        selected_presidents = president_multiselect(valid_presidents)

    if not selected_causes:
        st.info("Select one or more causes to compare.")
        return
    if len(selected_causes) > 5:
        st.warning("Select at most 5 causes.")
        return

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    year_opts = [y for y in all_years if y in presidents[president]] if president else all_years

    with st.sidebar:
        selected_years = [] if comparing else st.multiselect("Year:", year_opts)

    col = "total" if gender == "Total" else f"Total_{find_key_by_value(DEATHS_GENDER_EN, gender)}"
    pivot = mf.deaths_cause_pivot(dept_df, selected_causes, selected_years, president, value_col=col, dept_name=dept)
    place = dept if dept != "All" else "Colombia"
    title = f"Deaths by cause — {place}" if gender == "Total" else f"Deaths by cause ({gender}) — {place}"
    info = [title, "Year", "Deaths"]

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

    mc.render_chart(fig)
