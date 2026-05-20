import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_charts as mc
from generalities.dictionaries import presidents
from generalities.function import get_valid_presidents, show_all_years, to_datatime

def render_population(pop_df: pd.DataFrame) -> None:
    pop_local = to_datatime(pop_df, True)
    pop_local.index = pop_local.index.year.astype(int)

    st.title("Population")

    col1, col2 = st.columns(2)

    with col1:
        metric = st.selectbox("Metric:", ["Total", "Growth"])

    if metric == "Growth":
        series = round(pop_local["Población"].pct_change() * 100, 2)
        info = ["Annual Population Growth", "Year", "%"]
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
            choice_year = st.multiselect("Year:", sorted(pres_years, reverse=True))
        else:
            choice_year = st.multiselect("Year:", sorted(years, reverse=True))

    series = show_all_years(series, president)

    if president:
        series = series[series.index.isin(presidents[president])]

    if choice_year:
        series = series[series.index.isin(choice_year)]

    series = series.dropna()

    if series.empty:
        st.warning("Remember to select 'Show all years'  to see info about years prior to 2000")
        st.stop()

    data = series.to_frame(name=column)

    if len(data) == 1:
        year = data.index[0]
        if metric == "Growth":
            reference = full_series.median()
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
    st.info("If you want to choose a year prior to 2000, make sure you click \'Show all years\'")

