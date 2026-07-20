import streamlit as st
from pages.helpers import charts as mc
from pages.helpers import charts as dc
from pages.helpers.demography import births_functions as bir
from pages.helpers.demography import deaths_functions as dth
from generalities.dictionaries import presidents
from generalities.function import get_valid_presidents, president_multiselect, reshape_by_presidents, load_csv, load_geojson, highlight_selectbox
from generalities.demography_generalities.deaths import DEATHS_PATHS, DEATHS_COMPARE, AREA_EN, AGE_EN as DEATHS_AGE_EN, AGE_MUNI_EN, MUNI_CAPTION
from generalities.demography_generalities.births import DEPT_GEOJSON_PATH, DEPT_FEATURE_KEY
from generalities.demography_generalities.population import PYRAMID_MODES
from pages.tabs.demography._shared import _render_geo_bar_line, _render_pyramid_result


def render_deaths() -> None:
    st.title("Deaths")

    compare_by = st.session_state.get("deaths_compare", DEATHS_COMPARE[0])

    with st.sidebar:
        st.header("Filters")

    if compare_by == "Department":
        _render_deaths_department()
    elif compare_by == "Municipality":
        _render_deaths_municipality()
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
    chart_options = ["Line", "Bar"] + (["Population pyramid"] if compare_by == "Age Group" else [])
    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", chart_options)

    if chart_type == "Population pyramid":
        _render_deaths_pyramid()
        return

    gender_cause = None
    dept_df = None
    age_cause = age_gender = None
    if compare_by == "Gender":
        cause_names = dth.deaths_cause_names(dth.deaths_dept_prepared(DEATHS_PATHS["dept_death"]))
        with st.sidebar:
            gender_cause = st.selectbox("Cause:", ["All causes"] + cause_names)
        if gender_cause == "All causes":
            df = load_csv(DEATHS_PATHS["total"])
        else:
            dept_df = dth.deaths_dept_prepared(DEATHS_PATHS["dept_death"])
            df = dept_df
    elif compare_by == "Age Group":
        base_dept_df = dth.deaths_dept_prepared(DEATHS_PATHS["dept_death"])
        cause_names = dth.deaths_cause_names(base_dept_df)
        dept_names = sorted(base_dept_df["Name"].dropna().unique())
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            age_gender = st.selectbox("Gender:", ["Total", "Men", "Women"])
        with col2:
            age_cause = st.selectbox("Cause:", ["All causes"] + cause_names)
        with col3:
            age_dept = st.selectbox("Department:", ["All"] + dept_names)
        use_dept_source = age_cause != "All causes" or age_dept != "All"
        if not use_dept_source:
            df = load_csv(DEATHS_PATHS["area_age"])
        elif age_dept != "All":
            df = _deaths_dept_source()
            df = df[df["Name"] == age_dept]
        else:
            df = base_dept_df
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
            pivot, info = dth.deaths_gender_pivot(df)
        else:
            pivot, info = dth.deaths_gender_cause_pivot(dept_df, gender_cause)
    elif compare_by == "Area":
        col1, col2, col3 = st.columns(3)
        with col1:
            area_gender = st.selectbox("Gender:", ["Total", "Men", "Women"])
        with col2:
            age_label = st.selectbox("Age group:", ["All ages"] + age_labels)
        with col3:
            area_sel = st.selectbox("Area:", ["All areas"] + list(AREA_EN.values()))
        pivot, info = dth.deaths_area_pivot(df, age_label, area_gender, area_sel)
    else:  # Age Group
        if not use_dept_source:
            with st.sidebar:
                area = st.selectbox("Area:", ["Total"] + list(AREA_EN.values()))
            pivot, info = dth.deaths_age_pivot(df, age_gender, area)
        else:
            pivot, info = dth.deaths_age_cause_pivot(df, age_gender, age_cause)
            if age_dept != "All":
                info = [f"{info[0]} — {age_dept}", info[1], info[2]]
        with col4:
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

    highlight = highlight_selectbox(pivot)

    fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight)

    mc.render_chart(fig)


def _render_deaths_pyramid() -> None:
    base_dept_df = dth.deaths_dept_prepared(DEATHS_PATHS["dept_death"])
    cause_names = dth.deaths_cause_names(base_dept_df)
    dept_names = sorted(base_dept_df["Name"].dropna().unique())

    c0, c1, c2 = st.columns(3)
    with c0:
        cause = st.selectbox("Cause:", ["All causes"] + cause_names)
    with c1:
        dept = st.selectbox("Department:", ["All"] + dept_names)
    with c2:
        mode = st.selectbox("Display:", PYRAMID_MODES)

    use_dept_source = cause != "All causes" or dept != "All"

    if not use_dept_source:
        df = load_csv(DEATHS_PATHS["area_age"])
        with st.sidebar:
            area = st.selectbox("Area:", ["Total"] + list(AREA_EN.values()))
        men_pivot, _ = dth.deaths_age_pivot(df, "Men", area)
        women_pivot, _ = dth.deaths_age_pivot(df, "Women", area)
    else:
        if dept != "All":
            dept_df = _deaths_dept_source()
            dept_df = dept_df[dept_df["Name"] == dept]
        else:
            dept_df = base_dept_df
        men_pivot, _ = dth.deaths_age_cause_pivot(dept_df, "Men", cause)
        women_pivot, _ = dth.deaths_age_cause_pivot(dept_df, "Women", cause)

    years = sorted(men_pivot.index.tolist(), reverse=True)
    with st.sidebar:
        year = st.selectbox("Year:", years)

    men = dth.deaths_pyramid_row(men_pivot.loc[year])
    women = dth.deaths_pyramid_row(women_pivot.loc[year])
    men.name, women.name = "Men", "Women"

    title = f"Deaths pyramid — {year}"
    if cause != "All causes":
        title += f" — {cause}"
    if dept != "All":
        title += f" — {dept}"
    _render_pyramid_result(men, women, mode, title)


def _deaths_dept_source():
    with st.sidebar:
        place = st.selectbox("Place:", ["Occurrence", "Residence"])
    path = DEATHS_PATHS["dept_death"] if place == "Occurrence" else DEATHS_PATHS["dept_residence"]
    return dth.deaths_dept_prepared(path)


def _render_deaths_department() -> None:
    dept_df = _deaths_dept_source().rename(columns={"Fecha": "year"})

    all_years = sorted(dept_df["year"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["Name"].dropna().unique())
    age_labels = list(dict.fromkeys(DEATHS_AGE_EN.values()))
    cause_names = dth.deaths_cause_names(dept_df)
    valid_presidents = get_valid_presidents(all_years)

    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", ["Map", "Line", "Bar"])
        cause = st.selectbox("Cause:", ["All causes"] + cause_names)
        selected_presidents = president_multiselect(valid_presidents)

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    year_opts = [y for y in all_years if y in presidents[president]] if president else all_years

    with st.sidebar:
        selected_years = [] if comparing else st.multiselect("Year:", year_opts)

    col1, col2, col3 = st.columns(3)
    selected_depts = []
    if chart_type != "Map":
        with col3:
            selected_depts = st.multiselect("Departments:", dept_names)
    with col1:
        gender = st.selectbox("Gender:", ["Total", "Men", "Women"])
    with col2:
        age_label = st.selectbox("Age:", ["All ages"] + age_labels)

    if cause != "All causes":
        dept_df = dept_df[dept_df["cause"] == cause]

    dept_df["_val"] = dth.deaths_age_gender_value(dept_df, gender, age_label)
    col = "_val"
    noun = "Deaths" if gender == "Total" else gender
    scope = "all years" if not selected_years else ", ".join(map(str, sorted(selected_years)))
    if president and not selected_years:
        scope = president
    if age_label != "All ages":
        scope = f"{scope}, age {age_label}"
    if cause != "All causes":
        scope = f"{scope} — {cause}"

    if chart_type == "Map":
        if comparing:
            st.info("Map can't compare presidents — pick a single president or switch to Line/Bar.")
            return
        map_years = selected_years or ([y for y in all_years if y in presidents[president]] if president else [])
        grouped = bir.births_department_data(dept_df, map_years, col)
        info = [f"{noun} by department — {scope}", "Department", noun]
        geojson = load_geojson(DEPT_GEOJSON_PATH)
        fig = dc.colombia_choropleth(grouped, geojson, DEPT_FEATURE_KEY, col, info)
        mc.render_chart(fig)
        return

    if not selected_depts:
        st.info("Select one or more departments.")
        return

    pivot = bir.births_geo_trend(dept_df, "departamento", selected_depts, selected_years, value_col=col)

    if president:
        pivot = pivot[pivot.index.isin(presidents[president])]

    if comparing:
        info = [f"{noun} trend by department", "Year", noun]
        if not pivot.empty:
            pivot, info = reshape_by_presidents(pivot, selected_presidents, info)
        if pivot.empty:
            st.warning("No data for selected filters.")
            return
        highlight = highlight_selectbox(pivot)
        fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight, bar_if_single=False)
        mc.render_chart(fig)
        return

    _render_geo_bar_line(pivot, chart_type, "department", scope, noun=noun)


def _render_deaths_municipality() -> None:
    dept_df = dth.deaths_muni_prepared(DEATHS_PATHS["muni_residence"]).rename(columns={"Fecha": "year"})

    all_years = sorted(dept_df["year"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["Name"].dropna().unique())
    age_labels = list(dict.fromkeys(AGE_MUNI_EN.values()))
    valid_presidents = get_valid_presidents(all_years)

    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])
        selected_presidents = president_multiselect(valid_presidents)

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    year_opts = [y for y in all_years if y in presidents[president]] if president else all_years

    with st.sidebar:
        selected_years = [] if comparing else st.multiselect("Year:", year_opts)

    col1, col2, col3 = st.columns(3)
    with col1:
        dept = st.selectbox("Department:", dept_names)
    with col2:
        gender = st.selectbox("Gender:", ["Total", "Men", "Women"])
    with col3:
        age_label = st.selectbox("Age:", ["All ages"] + age_labels)

    scoped = dept_df[dept_df["Name"] == dept].copy()
    muni_names = sorted(scoped["municipio"].str.split(n=1).str[1].dropna().unique())
    abroad = dept == "Abroad"

    with st.sidebar:
        selected_munis = st.multiselect("Countries:" if abroad else "Municipalities:", muni_names)

    cause_scope = scoped
    if selected_munis:
        cause_scope = scoped[scoped["municipio"].str.split(n=1).str[1].isin(selected_munis)]
    cause_names = dth.deaths_cause_names(cause_scope)

    with st.sidebar:
        cause = st.selectbox("Cause:", ["All causes"] + cause_names)

    if cause != "All causes":
        scoped = scoped[scoped["cause"] == cause]

    scoped["_val"] = dth.deaths_age_gender_value(scoped, gender, age_label, AGE_MUNI_EN)
    col = "_val"
    noun = "Deaths" if gender == "Total" else gender
    entity = "country" if abroad else ("municipality" if selected_munis else "department")
    scope = "all years" if not selected_years else ", ".join(map(str, sorted(selected_years)))
    if president and not selected_years:
        scope = president
    if age_label != "All ages":
        scope = f"{scope}, age {age_label}"
    if cause != "All causes":
        scope = f"{scope} — {cause}"

    if selected_munis:
        pivot = bir.births_geo_trend(scoped, "municipio", selected_munis, selected_years, value_col=col)
    else:
        pivot = bir.births_geo_trend(scoped, "departamento", [], selected_years, value_col=col)

    if president:
        pivot = pivot[pivot.index.isin(presidents[president])]

    if comparing:
        info = [f"{noun} trend by {entity}", "Year", noun]
        if not pivot.empty:
            pivot, info = reshape_by_presidents(pivot, selected_presidents, info)
        if pivot.empty:
            st.warning("No data for selected filters.")
            return
        highlight = highlight_selectbox(pivot)
        fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight, bar_if_single=False)
        mc.render_chart(fig)
        st.caption(MUNI_CAPTION)
        return

    _render_geo_bar_line(pivot, chart_type, entity, scope, noun=noun)
    if not pivot.empty:
        st.caption(MUNI_CAPTION)


def _render_deaths_top_causes() -> None:
    dept_df = _deaths_dept_source()

    all_years = sorted(dept_df["Fecha"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["Name"].dropna().unique())
    valid_presidents = get_valid_presidents(all_years)
    age_labels = list(dict.fromkeys(DEATHS_AGE_EN.values()))

    with st.sidebar:
        selected_presidents = president_multiselect(valid_presidents)
        president = selected_presidents[0] if len(selected_presidents) == 1 else None
        year_opts = [y for y in all_years if y in presidents[president]] if president else all_years
        selected_years = [] if president else st.multiselect("Year:", year_opts)

    col1, col2, col3 = st.columns(3)
    with col1:
        opts = ["All"] + dept_names
        saved = st.session_state.get("deaths_cause_dept", "All")
        idx = opts.index(saved) if saved in opts else 0
        dept = st.selectbox("Department:", opts, index=idx)
        st.session_state["deaths_cause_dept"] = dept
    with col2:
        gender = st.selectbox("Gender:", ["Total", "Men", "Women"])
    with col3:
        age_label = st.selectbox("Age:", ["All ages"] + age_labels)

    dept_df["_val"] = dth.deaths_age_gender_value(dept_df, gender, age_label)
    series = dth.deaths_top_causes(dept_df, selected_years, dept, president, value_col="_val")

    if series.empty:
        st.warning("No data for selected filters.")
        return

    scope = ", ".join(map(str, sorted(selected_years))) if selected_years else (president or "all years")
    if age_label != "All ages":
        scope = f"{scope}, age {age_label}"
    place = dept if dept != "All" else "Colombia"
    g = "" if gender == "Total" else f" ({gender})"
    info = [f"Top 5 causes of death{g} — {place}, {scope}", "Deaths", "Cause"]
    fig = mc.ranked_bar_chart(series, info)
    mc.render_chart(fig)


def _render_deaths_cause_compare() -> None:
    dept_df = _deaths_dept_source()

    all_years = sorted(dept_df["Fecha"].unique().astype(int).tolist(), reverse=True)
    dept_names = sorted(dept_df["Name"].dropna().unique())
    valid_presidents = get_valid_presidents(all_years)
    cause_names = dth.deaths_cause_names(dept_df)
    age_labels = list(dict.fromkeys(DEATHS_AGE_EN.values()))

    col1, col2, col3 = st.columns(3)
    with col1:
        opts = ["All"] + dept_names
        saved = st.session_state.get("deaths_cause_dept", "All")
        idx = opts.index(saved) if saved in opts else 0
        dept = st.selectbox("Department:", opts, index=idx)
        st.session_state["deaths_cause_dept"] = dept
    with col2:
        gender = st.selectbox("Gender:", ["Total", "Men", "Women"])
    with col3:
        age_label = st.selectbox("Age:", ["All ages"] + age_labels)

    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])
        selected_causes = st.multiselect("Causes (max 5):", cause_names)
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

    dept_df["_val"] = dth.deaths_age_gender_value(dept_df, gender, age_label)
    pivot = dth.deaths_cause_pivot(dept_df, selected_causes, selected_years, president, value_col="_val", dept_name=dept)
    place = dept if dept != "All" else "Colombia"
    title = f"Deaths by cause — {place}" if gender == "Total" else f"Deaths by cause ({gender}) — {place}"
    if age_label != "All ages":
        title = f"{title} (age {age_label})"
    info = [title, "Year", "Deaths"]

    if comparing and not pivot.empty:
        pivot, info = reshape_by_presidents(pivot, selected_presidents, info)

    if pivot.empty:
        st.warning("No data for selected filters.")
        return

    highlight = highlight_selectbox(pivot)

    fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight)

    mc.render_chart(fig)
