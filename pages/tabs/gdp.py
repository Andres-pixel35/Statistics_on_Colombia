import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_functions as mf
from pages.helpers.macro import macro_charts as mc

def render_gdp(gdp_df: pd.DataFrame) -> None:
    gdp_local = gdp_df.copy()

    with st.sidebar:
        st.header("Filters:")

        years =  gdp_local.columns[1:].str.split("-").str[0].unique()
        choice_year = st.multiselect("Year:", sorted(years, reverse=True))

        st.info("You may choose more than one option.")

    st.title("Real GDP")

    if choice_year:
        pattern = "|".join(choice_year)
        mask = gdp_local.columns.str.contains(pattern)
        mask[0] = True
        gdp_local = gdp_local.loc[:, mask]

    gdp_series = mf.clean_gdp(gdp_local)
    fig = mc.total_gdp_line(gdp_series) 
    st.plotly_chart(fig)
    st.caption("Chained volume series, base year 2015")
    st.caption("Source: DANE")
    st.info("\'p\' is provisional and \'pr\' is preliminary data.")
