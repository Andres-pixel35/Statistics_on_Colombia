import streamlit as st
import pandas as pd
from pages.tabs import gdp, cpi 

st.set_page_config(layout="wide", page_title="Macroeconomic")

path_gdp = "./data/dane/GDP/spend/summarize.csv"
path_cpi = "./data/banco_republica/CPI/city/Total_Nacional.csv"

gdp_df = pd.read_csv(path_gdp, encoding="utf-8", dtype=str)
cpi_df = pd.read_csv(path_cpi, encoding="utf-8")

st.title("Statistics on Colombia")

with st.sidebar:
    section = st.radio("Section:", ["GDP", "CPI"])

if section == "GDP":
    gdp.render_gdp(gdp_df)
else:
    cpi.render_cpi(cpi_df)
