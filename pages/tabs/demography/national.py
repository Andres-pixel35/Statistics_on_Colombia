import streamlit as st
import pandas as pd
from pages.helpers import charts as mc
from pages.helpers import charts as dc
from pages.helpers.demography import births_functions as bir
from pages.helpers.demography import deaths_functions as dth
from pages.helpers.demography import population_functions as pop
from generalities.dictionaries import presidents
from generalities.function import get_valid_presidents, show_all_years, load_csv, BASE_DIR
from generalities.demography_generalities.births import BIRTHS_PATHS
from generalities.demography_generalities.deaths import DEATHS_PATHS
from generalities.demography_generalities.population import GENDER_AGG, AGE_SINGLE, PREV_YEAR, PROJECTED_NOTE
from pages.tabs.demography._shared import _render_pyramid

NET_MIGRATION_PATH = BASE_DIR / "data/world_bank/net_migration.csv"


def render_national(pop_df: pd.DataFrame) -> None:
    st.title("Population")

    with st.sidebar:
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar", "Population pyramid"])

    if chart_type == "Population pyramid":
        _render_pyramid(pop_df, "Colombia")
        return

    col1, col2 = st.columns(2)

    with col1:
        method = st.selectbox("Method:", ["Total", "Growth"])

    national = pop.national_total_series(pop_df, cap=PREV_YEAR)
    metric = "Absolute"
    show_projected = False
    is_national = False

    if method == "Growth":
        with col2:
            metric = st.selectbox("Metric", ["Absolute", "Percentage"])

        if metric == "Percentage":
            series = round(national.pct_change() * 100, 2)
            info = ["Annual Population Growth", "Year", "%"]
        else:
            series = national.diff()
            info = ["Annual Population Growth", "Year", "New People"]

        column = "Growth"
        years = national.index[1:]
    else:
        with col2:
            perspective = st.selectbox("Perspective:", ["National", "Net Migration", "Births", "Deaths", "Rates"])

        if perspective == "Net Migration":
            net_migration = load_csv(NET_MIGRATION_PATH)

            years = net_migration["Fecha"]
            series = net_migration["Migration"].astype(int)
            series.index = years
        elif perspective == "Births":
            series = bir.births_national_series(load_csv(BIRTHS_PATHS["total"]))
            years = series.index
        elif perspective == "Deaths":
            series = dth.deaths_national_series(load_csv(DEATHS_PATHS["total"]))
            years = series.index
        elif perspective == "Rates":
            b = bir.births_national_series(load_csv(BIRTHS_PATHS["total"]))
            d = dth.deaths_national_series(load_csv(DEATHS_PATHS["total"]))
            common = national.index.intersection(b.index).intersection(d.index)
            series = pd.DataFrame({
                "Birth rate": b[common] / national[common] * 1000,
                "Death rate": d[common] / national[common] * 1000,
            })
            years = series.index
        else:  # National
            is_national = True
            years = national.index

        if perspective == "Rates":
            info = ["National Birth & Death Rate", "Year", "Rate per 1,000"]
        elif perspective != "National":
            a = f"{perspective}"
            unit = {"Births": "Births", "Deaths": "Deaths"}.get(perspective, "People")
            info = [a, "Year", unit]
            column = f"{a}"

    source = "World Bank" if (method == "Total" and perspective == "Net Migration") else "DANE"

    show_all_applies = method == "Growth" or source != "DANE" or (method == "Total" and perspective == "National")

    if not is_national:
        full_series = series

    with st.sidebar:
        if is_national:
            gender = st.selectbox("Gender:", list(GENDER_AGG))
            age = st.selectbox("Age:", AGE_SINGLE)
        valid_presidents = get_valid_presidents(years)
        president = st.selectbox("President:", ["All"] + valid_presidents)
        president = None if president == "All" else president

        if president:
            pres_years = [y for y in years if y in presidents[president]]
            choice_year = st.multiselect("Year:", sorted(pres_years, reverse=True))
        else:
            choice_year = st.multiselect("Year:", sorted(years, reverse=True))

        compare_births = compare_migration = compare_deaths = False
        if method == "Growth" and metric == "Absolute":
            compare_births = st.checkbox("Compare with Births")
            compare_migration = st.checkbox("Compare with Net Migration")
            compare_deaths = st.checkbox("Compare with Deaths")
        elif method == "Total":
            if perspective == "Births":
                compare_deaths = st.checkbox("Compare with Deaths")
            elif perspective == "Deaths":
                compare_births = st.checkbox("Compare with Births")

        if is_national:
            show_projected = st.checkbox("Show projected", value=False)

    if is_national:
        cap = None if show_projected else PREV_YEAR
        series = pop.national_total_series(pop_df, gender, age, cap=cap)
        noun = "Population" if gender == "Total" else gender
        info = [noun, "Year", "People"]
        column = noun
        if age != "All ages":
            info[0] = f"{noun} (age {age})"
        full_series = series

    extras = []
    if compare_births:
        b = bir.births_national_series(load_csv(BIRTHS_PATHS["total"]))
        b.name = "Births"
        extras.append(b)
    if compare_migration:
        m = load_csv(NET_MIGRATION_PATH).set_index("Fecha")["Migration"].astype(int)
        m.name = "Net Migration"
        extras.append(m)
    if compare_deaths:
        d = dth.deaths_national_series(load_csv(DEATHS_PATHS["total"]))
        d.name = "Deaths"
        extras.append(d)
    if extras:
        series = pd.concat([series.rename(column)] + extras, axis=1)
        suffixes = (["Births"] if compare_births else []) + (["Net Migration"] if compare_migration else []) + (["Deaths"] if compare_deaths else [])
        info[0] = f"{info[0]} vs {' & '.join(suffixes)}"

    if show_all_applies:
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

        fig = dc.indicator(data, full_series, reference, gauge_info)
    else:
        if extras:
            fig = mc.line_or_bar(chart_type, data, info, bar_if_single=True)
        elif is_national and show_projected and chart_type == "Line":
            fig = dc.projection_line(data, info, split_year=PREV_YEAR)
        else:
            fig = mc.line_or_bar(chart_type, data, info, bar_if_single=False)

    mc.render_chart(fig)

    if is_national and show_projected and (data.index > PREV_YEAR).any():
        st.caption(PROJECTED_NOTE)

    if source == "World Bank":
        st.caption("Net migration is the net total of migrants during the period, that is, the number of immigrants minus the number of emigrants, including both citizens and noncitizens.")

    st.caption(f"Source: {source}")

    if extras:
        st.caption("Births & deaths: DANE · Net migration: World Bank")

    if show_all_applies:
        st.info("If you want to choose a year prior to 2000, make sure you click 'Show all years'")
