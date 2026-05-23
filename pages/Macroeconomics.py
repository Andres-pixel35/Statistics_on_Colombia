import streamlit as st
from pages.tabs import gdp, cpi, population
from generalities.function import load_csv, BASE_DIR

st.set_page_config(layout="wide", page_title="Macroeconomic")

path_gdp        = BASE_DIR / "data/dane/GDP/spend/summarize.csv"
path_cpi        = BASE_DIR / "data/banco_republica/CPI/city/Total_Nacional.csv"
path_population = BASE_DIR / "data/banco_republica/population/population.csv"

gdp_df = load_csv(path_gdp, dtype=str)
cpi_df = load_csv(path_cpi)
population_df = load_csv(path_population)

st.title("Statistics on Colombia")

with st.sidebar:
    section = st.radio("Section:", ["GDP", "CPI", "Population"])

if section == "GDP":
    gdp.render_gdp(gdp_df)
elif section == "CPI":
    cpi.render_cpi(cpi_df)
else:
    population.render_population(population_df)
