import streamlit as st
from pages.helpers.demography import population_functions as pop
from generalities.function import get_valid_presidents, show_all_years, load_csv
from generalities.demography_generalities.population import POP_PATHS, GENDER_AGG, AGE_SINGLE, PREV_YEAR
from pages.tabs.demography._shared import _render_pyramid, _render_pop_geo_chart, PROJECTED_NOTE


def render_municipality() -> None:
    st.title("Population")

    df = pop.dept_normalize(load_csv(POP_PATHS["municipal"]))
    dept_names = sorted(df["Name"].unique())
    genders = list(GENDER_AGG)

    with st.sidebar:
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar", "Population pyramid"])
        dept = st.selectbox("Department:", dept_names)

    scoped = df[df["Name"] == dept]
    muni_names = sorted(scoped["Municipio"].dropna().unique())

    if chart_type == "Population pyramid":
        c1, _ = st.columns(2)
        with c1:
            muni = st.selectbox("Municipality:", muni_names)
        _render_pyramid(scoped[scoped["Municipio"] == muni], muni)
        return

    all_years = sorted(scoped["AÑO"].unique().astype(int), reverse=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        gender = st.selectbox("Gender:", genders)
    with c2:
        age = st.selectbox("Age:", AGE_SINGLE)
    with c3:
        selected_munis = st.multiselect("Municipalities:", muni_names)
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

    if not selected_munis:
        st.info("Select one or more municipalities.")
        return

    noun = "Population" if gender == "Total" else gender
    pivot = pop.geo_trend(scoped, "Municipio", selected_munis, gender, age)
    pivot, show_all = show_all_years(pivot, president, return_flag=True)

    past_years = [y for y in selected_years if y < 2000]
    if past_years and not show_all and not president:
        st.warning("Remember to select 'Show all years' to see info about years prior to 2000")
        st.stop()

    if not show_projected:
        pivot = pivot[pivot.index <= PREV_YEAR]
    if selected_years:
        pivot = pivot[pivot.index.isin(selected_years)]
    _render_pop_geo_chart(pivot, chart_type, "municipality", noun, president)
    if show_projected and (pivot.index > PREV_YEAR).any():
        st.caption(PROJECTED_NOTE)
    st.caption("Source: DANE")
