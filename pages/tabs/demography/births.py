import streamlit as st
from pages.helpers import charts as mc
from pages.helpers import charts as dc
from pages.helpers.demography import births_functions as bir
from generalities.dictionaries import presidents
from generalities.function import get_valid_presidents, find_key_by_value, president_multiselect, reshape_by_presidents, load_csv, load_geojson, highlight_selectbox
from generalities.demography_generalities.births import BIRTHS_PATHS, BIRTHS_COMPARE, AGE_EN, GENDER_EN, DEPT_GEOJSON_PATH, DEPT_FEATURE_KEY
from generalities.demography_generalities.population import PYRAMID_MODES
from pages.tabs.demography._shared import _render_geo_bar_line, _render_pyramid_result


def render_births() -> None:
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
    age_df = None
    if compare_by == "Gender":
        df = load_csv(BIRTHS_PATHS["total"])
        age_df = load_csv(BIRTHS_PATHS["age"])
        present = [AGE_EN.get(a, a) for a in age_df["grupo_edad"].unique()]
        age_opts = ["All ages"] + [v for v in AGE_EN.values() if v in present]
    elif compare_by == "Mother Age":
        df = load_csv(BIRTHS_PATHS["age"])
    else:  # Education
        df = load_csv(BIRTHS_PATHS["education"])

    years = sorted(df["year"].unique().astype(int).tolist(), reverse=True)

    chart_options = ["Line", "Bar"] + (["Population pyramid"] if compare_by == "Mother Age" else [])
    with st.sidebar:
        chart_type = st.selectbox("Chart Type:", chart_options)

    if chart_type == "Population pyramid":
        _render_births_pyramid(df, years)
        return

    valid_presidents = get_valid_presidents(years)

    with st.sidebar:
        selected_presidents = president_multiselect(valid_presidents)

    comparing = len(selected_presidents) >= 2
    president = selected_presidents[0] if len(selected_presidents) == 1 else None
    year_opts = [y for y in years if y in presidents[president]] if president else years

    age_label = None
    gender_age = "All ages"
    if compare_by == "Education":
        present = [AGE_EN.get(a, a) for a in df["grupo_edad"].unique()]
        age_opts = ["All ages"] + [v for v in AGE_EN.values() if v in present]
        with st.sidebar:
            age_label = st.selectbox("Mother age:", age_opts)
    elif compare_by == "Gender":
        with st.sidebar:
            gender_age = st.selectbox("Mother age:", age_opts)

    with st.sidebar:
        selected_years = [] if comparing else st.multiselect("Year:", year_opts)

    if compare_by == "Gender":
        if gender_age == "All ages":
            pivot, info = bir.births_gender_pivot(df)
        else:
            pivot, info = bir.births_gender_age_pivot(age_df, gender_age)
    elif compare_by == "Mother Age":
        c1, c2 = st.columns(2)
        with c1:
            gender = st.selectbox("Gender:", ["Total", "Boys", "Girls"])
        pivot, info = bir.births_age_pivot(df, gender)
        with c2:
            chosen = st.multiselect("Age groups:", list(pivot.columns))
        if chosen:
            pivot = pivot[chosen]
    else:
        pivot, info = bir.births_education_pivot(df, age_label)
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

    highlight = highlight_selectbox(pivot)

    fig = mc.line_or_bar(chart_type, pivot, info, highlight=highlight)

    mc.render_chart(fig)


def _render_births_pyramid(age_df, years: list) -> None:
    mode = st.selectbox("Display:", PYRAMID_MODES)
    with st.sidebar:
        year = st.selectbox("Year:", years)

    boys_pivot, _ = bir.births_age_pivot(age_df, "Boys")
    girls_pivot, _ = bir.births_age_pivot(age_df, "Girls")
    boys = boys_pivot.loc[year].drop("Unknown", errors="ignore")
    girls = girls_pivot.loc[year].drop("Unknown", errors="ignore")
    boys.name, girls.name = "Boys", "Girls"

    title = f"Births pyramid by mother's age — {year}"
    _render_pyramid_result(boys, girls, mode, title)


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
        grouped = bir.births_department_data(dept_df, selected_years, col)
        info = [f"{noun} by department — {scope}", "Department", noun]
        geojson = load_geojson(DEPT_GEOJSON_PATH)
        fig = dc.colombia_choropleth(grouped, geojson, DEPT_FEATURE_KEY, col, info)
        mc.render_chart(fig)
        return

    if not selected_depts:
        st.info("Select one or more departments.")
        return

    pivot = bir.births_geo_trend(dept_df, "departamento", selected_depts, selected_years, value_col=col)
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
        selected_munis = st.multiselect("Municipalities:", muni_names)
        selected_years = st.multiselect("Year:", all_years)

    if not selected_munis:
        st.info("Select one or more municipalities.")
        return

    scope = "all years" if not selected_years else ", ".join(map(str, sorted(selected_years)))
    pivot = bir.births_geo_trend(scoped, "municipio", selected_munis, selected_years)
    _render_geo_bar_line(pivot, chart_type, "municipality", scope)
