import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_functions as mf
from pages.helpers.macro import macro_charts as mc
import translations.gdp_spend as t
from translations.gdp_production import production_summarize_terms as p
from translations.gdp_income import income_summarize_terms as i
from translations.presidents import presidents

def render_gdp(gdp_df: pd.DataFrame) -> None:
    gdp_local = gdp_df.copy()
 
    st.title("GDP")

    col1, col2, col3 = st.columns(3)

    with col1:
        method = st.selectbox("Method:", ["Total Values", "Growth"]) 

    if method == "Total Values":
        with col2:
            perspective = st.selectbox("Perspective:", ["Spend", "Production", "Income"])

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

            mf.generalities_spend_product(gdp_local, selected_terms, variable, "Chained volume series")
        elif perspective == "Production":
            path = "./data/dane/GDP/production/summarize.csv" 
            gdp_local = pd.read_csv(path, encoding="utf-8", dtype=str)

            with col3:
                category = st.selectbox("Category:", ["Summarize"])
                
            variable = -1

            mf.generalities_spend_product(gdp_local, p, variable, "Chained volume series")
        else:
            path = "./data/dane/GDP/income/summarize.csv"
            gdp_local = pd.read_csv(path, encoding="utf-8", dtype=str)

            with col3:
                category = st.selectbox("Category:", ["Summarize"])
                
            variable = -1

            mf.generalities_spend_product(gdp_local, i, variable, "Current Prices")
    else:
        with col2:
            perspective = st.selectbox("Perspective:", ["Annual", "Quarter"])

        if perspective == "Annual":
            path = "./data/banco_republica/GDP/annual_growth.csv"

            gdp_local = pd.read_csv(path, encoding="utf-8", dtype=str) 

            quarter = None
        else:
            path = "./data/banco_republica/GDP/quarter_growth.csv"

            gdp_local = pd.read_csv(path, encoding="utf-8", dtype=str)

            quarter = "I"

        with col3: 
            years = gdp_local[gdp_local.columns[0]].str.split("-").str[0].unique()

            tmp_years = years.astype(int)

            valid_presidents = [
                name for name, years in presidents.items() 
                if not set(years).isdisjoint(tmp_years)
            ]

            president = st.selectbox("President:", valid_presidents, index=None)

        with st.sidebar:
            st.title("Filters")

            years = gdp_local["Fecha"]

            if quarter is not None:
                quarter = st.selectbox("Quarter:", ["I", "II", "III", "IV"])
                years = gdp_local["Fecha"].str.split("-").str[0].unique()

            if president:
                choice_year = st.multiselect("Year:", sorted(presidents[president], reverse=True)) 
            else:
                choice_year = st.multiselect("Year:", sorted(years, reverse=True)) 

            st.info("You may choose more than one option.")

        fig = mc.gdp_growth(gdp_local, choice_year, president, 1, quarter) 
        st.plotly_chart(fig)
        st.caption("Spliced series, base 2015")
        st.caption("Source: DANE")
