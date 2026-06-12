import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from pages.helpers.demography import demography_charts as dc
from pages.helpers.demography import births_functions as bir
from pages.helpers.demography import deaths_functions as dth
from pages.helpers.demography import population_functions as pop
from generalities.macro_generalities.dictionaries import presidents
from generalities.function import get_valid_presidents, show_all_years, load_csv, BASE_DIR
from generalities.demography_generalities.births import BIRTHS_PATHS
from generalities.demography_generalities.deaths import DEATHS_PATHS
from generalities.demography_generalities.population import PREV_YEAR
from pages.tabs.demography._shared import _render_pyramid, PROJECTED_NOTE

NET_MIGRATION_PATH = BASE_DIR / "data/world_bank/net_migration.csv"


def render_national(pop_df: pd.DataFrame) -> None:
    st.title("Population")

    col1, col2 = st.columns(2)

    with col1:
        method = st.selectbox("Method:", ["Total", "Growth", "Projection", "By Age"])

    if method == "Projection":
        _render_population_projection(pop_df)
        return
    if method == "By Age":
        with st.sidebar:
            st.header("Filters")
        _render_pyramid(pop_df, "Colombia")
        return

    national = pop.national_total_series(pop_df, cap=PREV_YEAR)
    metric = "Absolute"

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
            perspective = st.selectbox("Perspective:", ["National", "Net Migration", "Births", "Deaths"])

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
        else:
            series = national
            years = national.index

        a = "Population" if perspective == "National" else f"{perspective}"

        unit = {"Births": "Births", "Deaths": "Deaths"}.get(perspective, "People")
        info = [a, "Year", unit]
        column = f"{a}"

    source = "World Bank" if (method == "Total" and perspective == "Net Migration") else "DANE"

    show_all_applies = method == "Growth" or source != "DANE" or (method == "Total" and perspective == "National")

    full_series = series

    with st.sidebar:
        st.header("Filters")
        chart_type = st.selectbox("Chart Type:", ["Line", "Bar"])
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
        else:
            fig = mc.line_or_bar(chart_type, data, info, bar_if_single=False)

    mc.render_chart(fig)

    if source == "World Bank":
        st.caption("Net migration is the net total of migrants during the period, that is, the number of immigrants minus the number of emigrants, including both citizens and noncitizens.")

    st.caption(f"Source: {source}")

    if extras:
        st.caption("Births & deaths: DANE · Net migration: World Bank")

    if show_all_applies:
        st.info("If you want to choose a year prior to 2000, make sure you click 'Show all years'")


def _render_population_projection(pop_df: pd.DataFrame) -> None:
    series = pop.national_total_series(pop_df)

    with st.sidebar:
        st.header("Filters")
        show_all = st.checkbox("Show all years", value=False)

    if not show_all:
        series = series[series.index >= 2020]

    info = ["Population projection", "Year", "People"]
    fig = dc.projection_line(series.to_frame(name="Population"), info, split_year=PREV_YEAR)
    mc.render_chart(fig)
    st.caption(f"Projected from {PREV_YEAR + 1} onward (dashed).")
    st.caption(PROJECTED_NOTE)
    st.caption("Source: DANE")
