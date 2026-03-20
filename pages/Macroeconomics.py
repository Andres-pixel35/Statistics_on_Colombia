import streamlit as st
import pandas as pd
from pages.tabs import gdp 

st.set_page_config(layout="wide", page_title="Macroeconomic")

path_gdp = "./data/dane/GDP/spend/summarize.csv"

gdp_df = pd.read_csv(path_gdp, encoding="utf-8", dtype=str)
st.set_page_config(layout="wide")

st.title("Statistics on Colombia")

tab1, tab2 = st.tabs(["GDP", "CPI"])

with tab1:
    gdp.render_gdp(gdp_df)
