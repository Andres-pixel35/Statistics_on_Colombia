import streamlit as st
import pandas as pd
from pages.tabs import gdp, cpi, population

st.set_page_config(layout="wide", page_title="Macroeconomic")

path_gdp = "./data/dane/GDP/spend/summarize.csv"
path_cpi = "./data/banco_republica/CPI/city/Total_Nacional.csv"
path_population = "./data/banco_republica/population/population.csv"

gdp_df = pd.read_csv(path_gdp, encoding="utf-8", dtype=str)
cpi_df = pd.read_csv(path_cpi, encoding="utf-8")
population_df = pd.read_csv(path_population, encoding="utf-8")

st.title("Statistics on Colombia")

with st.sidebar:
    section = st.radio("Section:", ["GDP", "CPI", "Population"])

if section == "GDP":
    gdp.render_gdp(gdp_df)
elif section == "CPI":
    cpi.render_cpi(cpi_df)
else:
    population.render_population(population_df)
