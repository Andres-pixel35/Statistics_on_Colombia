import streamlit as st
from pages.tabs.macroeconomics import gdp, cpi, job_market, productivity, debt
from generalities.function import load_csv, BASE_DIR

st.set_page_config(layout="wide", page_title="Macroeconomic")

path_gdp = BASE_DIR / "data/dane/GDP/spend/summarize.csv"
path_cpi = BASE_DIR / "data/banco_republica/CPI/city/Total_Nacional.csv"
path_unemp = BASE_DIR / "data/banco_republica/unemployment/unemployment.csv"
path_prod = BASE_DIR / "data/dane/productivity/laboral/por_persona_empleada.csv"
path_debt = BASE_DIR / "data/hacienda/debt/saldos/saldos.csv"

gdp_df = load_csv(path_gdp, dtype=str)
cpi_df = load_csv(path_cpi)
unemp_df = load_csv(path_unemp)
prod_df = load_csv(path_prod)
debt_df = load_csv(path_debt)

st.title("Statistics on Colombia")

with st.sidebar:
    section = st.radio("Section:", ["GDP", "CPI", "Job Market", "Productivity", "Debt"])

if section == "GDP":
    gdp.render_gdp(gdp_df)
elif section == "CPI":
    cpi.render_cpi(cpi_df)
elif section == "Job Market":
    job_market.render_job_market(unemp_df)
elif section == "Productivity":
    productivity.render_productivity(prod_df)
else:
    debt.render_debt(debt_df)
