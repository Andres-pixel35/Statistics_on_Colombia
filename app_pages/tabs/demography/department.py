import streamlit as st
from app_pages.helpers import charts as mc
from app_pages.helpers import charts as dc
from app_pages.helpers.demography import population_functions as pop
from generalities.function import get_valid_presidents, show_all_years, load_csv, load_geojson
from generalities.demography_generalities.population import POP_PATHS, GENDER_AGG, AGE_SINGLE, PREV_YEAR, PROJECTED_NOTE
from generalities.demography_generalities.births import DEPT_GEOJSON_PATH, DEPT_FEATURE_KEY
from app_pages.tabs.demography._shared import _render_pyramid, _render_pop_geo_chart
from generalities.i18n import t


def render_department() -> None:
    st.title(t("Population"))

    df = pop.dept_normalize(load_csv(POP_PATHS["departmental"]))
    all_years = sorted(df["AÑO"].unique().astype(int), reverse=True)
    dept_names = sorted(df["Name"].unique())
    genders = list(GENDER_AGG)

    with st.sidebar:
        st.header(t("Filters"))
        chart_type = st.selectbox(t("Chart Type:"), ["Map", "Line", "Bar", "Population pyramid"], format_func=t)

    if chart_type == "Population pyramid":
        _render_pyramid(df, entity={"label": "Department", "options": dept_names, "column": "Name"})
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        gender = st.selectbox(t("Gender:"), genders, format_func=t)
    with c2:
        age = st.selectbox(t("Age:"), AGE_SINGLE, format_func=t)
    noun = "Population" if gender == "Total" else gender

    if chart_type == "Map":
        default = all_years.index(PREV_YEAR) if PREV_YEAR in all_years else 0
        with st.sidebar:
            year = st.selectbox(t("Year:"), all_years, index=default)
        grouped = pop.dept_map_data(df, year, gender, age)
        info = [t("{noun} by {entity}").format(noun=t(noun), entity=t("department")) + f" — {year}", "Department", noun]
        geojson = load_geojson(DEPT_GEOJSON_PATH)
        fig = dc.colombia_choropleth(grouped, geojson, DEPT_FEATURE_KEY, "_val", info)
        mc.render_chart(fig)
        if year > PREV_YEAR:
            st.caption(t("Projected (expected) data."))
            st.caption(t(PROJECTED_NOTE))
        st.caption(t("Source: DANE"))
        return

    with c3:
        selected_depts = st.multiselect(t("Departments:"), dept_names)
    with st.sidebar:
        president = st.selectbox(t("President:"), ["All"] + get_valid_presidents(all_years), format_func=t)
        president = None if president == "All" else president
        selected_years = st.multiselect(t("Year:"), all_years)
        show_projected = st.checkbox(t("Show projected"), value=False)

    future_years = [y for y in selected_years if y > PREV_YEAR]
    if future_years and not show_projected:
        st.warning(t("Year {year} contain projected data. Enable 'Show projected' to include them.").format(year=future_years[0]))
        st.stop()

    if not selected_depts:
        st.info(t("Select one or more departments."))
        return

    pivot = pop.geo_trend(df, "Name", selected_depts, gender, age)
    pivot, show_all = show_all_years(pivot, president, return_flag=True)

    past_years = [y for y in selected_years if y < 2000]
    if past_years and not show_all and not president:
        st.warning(t("Remember to select 'Show all years' to see info about years prior to 2000"))
        st.stop()

    if not show_projected:
        pivot = pivot[pivot.index <= PREV_YEAR]
    if selected_years:
        pivot = pivot[pivot.index.isin(selected_years)]
    _render_pop_geo_chart(pivot, chart_type, "department", noun, president)
    if show_projected and (pivot.index > PREV_YEAR).any():
        st.caption(t(PROJECTED_NOTE))
    st.caption(t("Source: DANE"))
