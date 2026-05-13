import streamlit as st
import pandas as pd
from pages.helpers.macro import macro_functions as mf
from pages.helpers.macro import macro_charts as mc
import generalities.gdp_spend as t
from generalities.gdp_production import production_summarize_terms as p
from generalities.gdp_income import income_summarize_terms as i
from generalities.dictionaries import presidents
from generalities.function import get_valid_presidents, find_key_by_value, show_all_years 

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
            cats = t.spend_categories
            with col3:
                category = st.selectbox("Category:", cats.values())

            filename = find_key_by_value(cats, category)
            selected_terms = t.spend_terms_map.get(filename)

            if category != "Summarize":
                path = f"./data/dane/GDP/spend/{filename}.csv"
                gdp_local = pd.read_csv(path, encoding="utf-8", dtype=str)
                variable = 0
            else:
                variable = -1

            gdp_info = ["Real GDP per Year", "Year", "Billions (COP)", "Chained volume series"]
            mf.generalities_spend_product(gdp_local, selected_terms, variable, gdp_info)
        elif perspective == "Production":
            path = "./data/dane/GDP/production/summarize.csv"
            gdp_local = pd.read_csv(path, encoding="utf-8", dtype=str)

            with col3:
                category = st.selectbox("Category:", ["Summarize"])

            variable = -1

            gdp_info = ["Real GDP per Year", "Year", "Billions (COP)", "Chained volume series"]
            mf.generalities_spend_product(gdp_local, p, variable, gdp_info)
        else:
            path = "./data/dane/GDP/income/summarize.csv"
            gdp_local = pd.read_csv(path, encoding="utf-8", dtype=str)

            with col3:
                category = st.selectbox("Category:", ["Summarize"])

            variable = -1

            gdp_info = ["Real GDP per Year", "Year", "Billions (COP)", "Current Prices"]
            mf.generalities_spend_product(gdp_local, i, variable, gdp_info)
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

            valid_presidents = get_valid_presidents(tmp_years)

            president = st.selectbox("President:", valid_presidents, index=None)

        with st.sidebar:
            st.title("Filters")

            if quarter is not None:
                quarter = st.selectbox("Quarter:", ["I", "II", "III", "IV"])

            if president:
                pres_years = [y for y in tmp_years if y in presidents[president]]
                choice_year = st.multiselect("Year:", sorted(pres_years, reverse=True)) 
            else:
                choice_year = st.multiselect("Year:", sorted(years, reverse=True)) 

            if quarter is None:
                gdp_local.index = tmp_years

                gdp_local = show_all_years(gdp_local, president)

                gdp_local = gdp_local.reset_index(drop=True)

                st.info("If you want to choose a year prior to 2000, make sure you click \'Show all years\'")

        fig = mc.gdp_growth(gdp_local, choice_year, president, 1, quarter) 
        st.plotly_chart(fig)
        st.caption("Spliced series, base 2015")
        st.caption("Source: DANE")
