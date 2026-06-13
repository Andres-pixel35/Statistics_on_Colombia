import streamlit as st
from pages.helpers.macro import macro_charts as mc
from pages.helpers.demography import demography_charts as dc
from pages.helpers.demography import population_functions as pop
from generalities.function import get_valid_presidents, show_all_years, load_csv, load_geojson
from generalities.demography_generalities.population import POP_PATHS, GENDER_AGG, AGE_SINGLE, PREV_YEAR
from generalities.demography_generalities.births import DEPT_GEOJSON_PATH, DEPT_FEATURE_KEY
from pages.tabs.demography._shared import _render_pyramid, _render_pop_geo_chart, PROJECTED_NOTE


def render_department() -> None:
    st.title("Population")

    df = pop.dept_normalize(load_csv(POP_PATHS["departmental"]))
    all_years = sorted(df["AÑO"].unique().astype(int), reverse=True)
    dept_names = sorted(df["Name"].unique())
    genders = list(GENDER_AGG)

    with st.sidebar:
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Map", "Line", "Bar", "Population pyramid"])

    if chart_type == "Population pyramid":
        c1, _ = st.columns(2)
        with c1:
            dept = st.selectbox("Department:", dept_names)
        _render_pyramid(df[df["Name"] == dept], dept)
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        gender = st.selectbox("Gender:", genders)
    with c2:
        age = st.selectbox("Age:", AGE_SINGLE)
    noun = "Population" if gender == "Total" else gender

    if chart_type == "Map":
        default = all_years.index(PREV_YEAR) if PREV_YEAR in all_years else 0
        with st.sidebar:
            year = st.selectbox("Year:", all_years, index=default)
        grouped = pop.dept_map_data(df, year, gender, age)
        info = [f"{noun} by department — {year}", "Department", noun]
        geojson = load_geojson(DEPT_GEOJSON_PATH)
        fig = dc.colombia_choropleth(grouped, geojson, DEPT_FEATURE_KEY, "_val", info)
        mc.render_chart(fig)
        if year > PREV_YEAR:
            st.caption("Projected (expected) data.")
            st.caption(PROJECTED_NOTE)
        st.caption("Source: DANE")
        return

    with c3:
        selected_depts = st.multiselect("Departments:", dept_names)
    with st.sidebar:
        president = st.selectbox("President:", ["All"] + get_valid_presidents(all_years))
        president = None if president == "All" else president
        selected_years = st.multiselect("Year:", all_years)
        show_projected = st.checkbox("Show projected", value=False)

    future_years = [y for y in selected_years if y > PREV_YEAR]
    if future_years and not show_projected:
        st.warning(
            f"Year {future_years[0]} contain projected data. "
            "Enable 'Show projected' to include them."
        )
        st.stop()

    if not selected_depts:
        st.info("Select one or more departments.")
        return

    pivot = pop.geo_trend(df, "Name", selected_depts, gender, age)
    pivot, show_all = show_all_years(pivot, president, return_flag=True)

    past_years = [y for y in selected_years if y < 2000]
    if past_years and not show_all and not president:
        st.warning("Remember to select 'Show all years' to see info about years prior to 2000")
        st.stop()

    if not show_projected:
        pivot = pivot[pivot.index <= PREV_YEAR]
    if selected_years:
        pivot = pivot[pivot.index.isin(selected_years)]
    _render_pop_geo_chart(pivot, chart_type, "department", noun, president)
    if show_projected and (pivot.index > PREV_YEAR).any():
        st.caption(PROJECTED_NOTE)
    st.caption("Source: DANE")
