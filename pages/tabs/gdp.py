import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_functions as mf
from pages.helpers.macro import macro_charts as mc
import translations.gdp_spend as t
from translations.gdp_production import production_summarize_terms as p

def generalities(df: pd.DataFrame, terms: dict, variable: int|list) -> None:
    """
    General utilities used in several parts of this section.
    filters in the sidebar and the logic to plot the chart
    """
    with st.sidebar: 
        st.header("Filters:")
        years =  df.columns[1:].str.split("-").str[0].unique()
        choice_year = st.multiselect("Year:", sorted(years, reverse=True))

        tmp = st.multiselect("Variable:", terms.values())
        if tmp:
            variable = [k for k, v in terms.items() if v in tmp]

        st.info("You may choose more than one option.")

    if choice_year:
        pattern = "|".join(choice_year)
        mask = df.columns.str.contains(pattern)
        mask[0] = True
        df = df.loc[:, mask]

    # plot the chart
    gdp_series = mf.clean_gdp(df, variable)
    fig = mc.total_gdp_line(gdp_series, terms) 
    st.plotly_chart(fig)
    st.caption("Chained volume series, base year 2015")
    st.caption("Source: DANE")
    st.info("\'p\' is provisional and \'pr\' is preliminary data.")

def render_gdp(gdp_df: pd.DataFrame) -> None:
    gdp_local = gdp_df.copy()
 
    st.title("Real GDP")

    col1, col2, col3 = st.columns(3)

    with col1:
        method = st.selectbox("Method:", ["Total Values", "Annual Growth", "Quarter Growth"]) 

    if method == "Total Values":
        with col2:
            perspective = st.selectbox("Perspective:", ["Spend", "Production"])

        if perspective == "Spend":
            with col3:
                category = st.selectbox("Category:", t.spend_categories.values())

            file = next((k for k, v in t.spend_categories.items() if v == category), None)
            term_name = f"spend_{file}_terms"
            selected_terms = getattr(t, term_name, None)

            if category != "Summarize":
                path = f"./data/dane/GDP/spend/{file}.csv"
                gdp_local = pd.read_csv(path, encoding="utf-8", dtype=str)
                variable = 0
            else:
                variable = -1

            generalities(gdp_local, selected_terms, variable)
        else:
            path = "./data/dane/GDP/production/summarize.csv" 
            gdp_local = pd.read_csv(path, encoding="utf-8", dtype=str)

            with col3:
                category = st.selectbox("Category:", ["Summarize"])
                
            variable = -1

            generalities(gdp_local, p, variable)
    else:
        st.write("SOON")
